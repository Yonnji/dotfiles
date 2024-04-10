import os
import subprocess


IS_X11 = os.getenv('XDG_SESSION_TYPE').lower() == 'x11'
XDG_PORTALS = ['gnome', 'gtk', '']
if IS_X11:
    XDG_PORTALS.append('wlr')


def portals_start():
    env = dict(os.environ)
    env.update({
        'XDG_SESSION_DESKTOP': 'gnome',
        'XDG_CURRENT_DESKTOP': 'gnome',
    })

    for portal in XDG_PORTALS:
        path = list(filter(None, ['/usr/libexec/xdg-desktop-portal', portal]))
        subprocess.Popen(['-'.join(path), '-vr'], start_new_session=True, env=env)


def portals_stop():
    for portal in XDG_PORTALS:
        name = list(filter(None, ['xdg-desktop-portal', portal]))
        subprocess.call(['pkill', '-'.join(name)])
