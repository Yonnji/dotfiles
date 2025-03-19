"""
Use with @hook.subscribe.float_change decorator.
"""
import subprocess

from libqtile import qtile
from libqtile.log_utils import logger


def float_change_xset():
    has_fullscreen = False

    for group in qtile.groups:
        for window in group.windows:
            if window.fullscreen:
                has_fullscreen = True
                break

    if has_fullscreen:
        cmds = [
            ['xset', 's', 'noblank'],
            ['xset', 's', 'off'],
            ['xset', '-dpms'],
        ]

    else:
        cmds = [
            ['xset', 's', 'noblank'],
            ['xset', 's', 'off'],
            ['xset', '+dpms'],
            ['xset', 'dpms', '0', '0', '300'],
        ]

    for cmd in cmds:
        logger.error(cmd)
        subprocess.call(cmd)


def inhibit_dbus():
    if not qtile.ss_inhibit:
        qtile.ss_inhibit = int(subprocess.check_output([
            'qdbus',
            'org.freedesktop.ScreenSaver',  # service
            '/ScreenSaver',  # path
            'org.freedesktop.ScreenSaver.Inhibit',  # method
            '$$', 'qtile',
        ]).decode().strip('\n'))

    if not qtile.pm_inhibit:
        qtile.pm_inhibit = int(subprocess.check_output([
            'qdbus',
            'org.freedesktop.PowerManagement.Inhibit',  # service
            '/org/freedesktop/PowerManagement/Inhibit',  # path
            'org.freedesktop.PowerManagement.Inhibit.Inhibit',  # method
            '$$', 'qtile',
        ]).decode().strip('\n'))


def uninhibit_dbus():
    if qtile.ss_inhibit:
        subprocess.call([
            'qdbus',
            'org.freedesktop.ScreenSaver',
            '/ScreenSaver',
            'org.freedesktop.ScreenSaver.UnInhibit',
            str(qtile.ss_inhibit),
        ])
        qtile.ss_inhibit = 0

    if qtile.pm_inhibit:
        subprocess.call([
            'qdbus',
            'org.freedesktop.PowerManagement.Inhibit',
            '/org/freedesktop/PowerManagement/Inhibit',
            'org.freedesktop.PowerManagement.Inhibit.UnInhibit',
            str(qtile.pm_inhibit),
        ])
        qtile.pm_inhibit = 0


def float_change_dbus():
    has_fullscreen = False

    for group in qtile.groups:
        for window in group.windows:
            if window.fullscreen:
                has_fullscreen = True
                break

    if has_fullscreen:
        inhibit_dbus()
    else:
        uninhibit_dbus()
