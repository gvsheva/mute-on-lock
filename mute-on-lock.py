#!/usr/bin/env python

import dbus
import gobject
import signal
import sys

StateHandle = type('StateHandle', (object,), dict(
    mute_before_lock=True
))


def get_proxy(servicename, path):
    sessionbus = dbus.SessionBus()
    return sessionbus.get_object(servicename, path)


def get_iface(proxy, ifacename):
    return dbus.Interface(proxy, ifacename)


def get_current_master_control():
    kmix = get_proxy('org.kde.kmix', '/Mixers')
    propmgr = get_iface(kmix, 'org.freedesktop.DBus.Properties')
    return propmgr.Get('org.kde.KMix.MixSet', 'currentMasterControl')


def get_current_master_mixer():
    kmix = get_proxy('org.kde.kmix', '/Mixers')
    propmgr = get_iface(kmix, 'org.freedesktop.DBus.Properties')
    return propmgr.Get('org.kde.KMix.MixSet', 'currentMasterMixer')


def get_kmix_control():
    import re

    path = '/Mixers/%(mixer)s/%(control)s' % dict(
        mixer=re.sub(r'[^\w]', '_', get_current_master_mixer()),
        control=re.sub(r'[^\w]', '_', get_current_master_control())
        )

    return get_proxy('org.kde.kmix', path)


def get_mute():
    kmixctrl = get_kmix_control()
    propmgr = get_iface(kmixctrl, 'org.freedesktop.DBus.Properties')
    propmgr.Get('org.kde.KMix.Control', 'mute')


def set_mute(mute=True):
    kmixctrl = get_kmix_control()
    propmgr = get_iface(kmixctrl, 'org.freedesktop.DBus.Properties')
    propmgr.Set('org.kde.KMix.Control', 'mute', mute)


def dbus_screensaver_active_changed(locked, *args, **kwargs):
    if locked:
        StateHandle.mute_before_lock = get_mute()
        set_mute(True)
    else:
        if StateHandle.mute_before_lock:
            pass
        else:
            set_mute(False)


def main():
    from dbus.mainloop.qt import DBusQtMainLoop
    from PyQt4 import QtCore

    def interrupted(*args, **kwargs):
        QtCore.QCoreApplication.quit()

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    signal.signal(signal.SIGQUIT, interrupted)

    loop = DBusQtMainLoop(set_as_default=True)
    app = QtCore.QCoreApplication(sys.argv)
    timer = QtCore.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    sbus = dbus.SessionBus()
    screensaver_proxy = sbus.get_object('org.freedesktop.ScreenSaver', '/org/freedesktop/ScreenSaver')
    screensaver_proxy.connect_to_signal('ActiveChanged', dbus_screensaver_active_changed)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
