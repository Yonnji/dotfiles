import copy
import os
import subprocess


XDG_PORTALS = ['gnome', 'gtk', '']
# XDG_PORTALS = ['kde', '']


def portals_start(is_x11=False):
    env = dict(os.environ)
    env.update({
        'XDG_SESSION_DESKTOP': XDG_PORTALS[0],
        'XDG_CURRENT_DESKTOP': XDG_PORTALS[0],
    })

    portals = copy.copy(XDG_PORTALS)
    if is_x11:
        portals.append('wlr')

    for portal in portals:
        path = '/usr/libexec/xdg-desktop-portal'
        if portal:
            path = f'{path}-{portal}'
        subprocess.Popen([path, '-vr'], start_new_session=True, env=env)


def portals_stop(is_x11=False):
    portals = copy.copy(XDG_PORTALS)
    if is_x11:
        portals.append('wlr')

    for portal in XDG_PORTALS:
        path = '/usr/libexec/xdg-desktop-portal'
        if portal:
            path = f'{path}-{portal}'
        subprocess.call(['pkill', path])
