import os
import re
import subprocess
import time

from libqtile import bar, layout, widget, hook, qtile

from qtilemods.tools.randr import randr
from qtilemods.widget.power import POWER_SAVER

DISPLAY_INTERNAL = 'eDP-1'
DISPLAY_EXTERNAL = 'DP-1'


def is_x11():
    return os.getenv('XDG_SESSION_TYPE').lower() in ('x11', 'tty')


def contains(line, *values):
    for value in values:
        if type(value) in (list, tuple):
            if contains(line, *value):
                return True
        if value in line:
            return True
    return False


def take_screenshot(options=False):
    def f(qtile):
        args = ['flatpak', 'run', 'org.gnome.Screenshot']
        if options:
            args.append('--interactive')
        subprocess.Popen(args, start_new_session=True)

    return f


def lock_screen(suspend=False):
    def f(qtile):
        image = os.path.expanduser('~/Pictures/i3lock.png')
        args = [
            'i3lock',
            '--show-keyboard-layout',
            '--tiling',
            f'--image={image}',
        ]
        subprocess.Popen(args)
        if suspend:
            subprocess.Popen(['systemctl', 'suspend'])
        else:
            time.sleep(2)
            subprocess.Popen(['xset', 'dpms', 'force', 'off'])

    return f


def remap_screens(qtile):
    if len(qtile.screens) == 1:
        return

    screen_ids = tuple(range(len(qtile.screens)))
    screens = [screen_ids[0], screen_ids[-1]]
    # if not IS_X11:
    #     screens.reverse()

    last_workspace = '5'

    qtile.focus_screen(screens[-1])
    qtile.groups_map[last_workspace].toscreen()
    qtile.focus_screen(screens[0])


def input_update(qtile):
    if not is_x11():
        return

    lines = subprocess.check_output(['xinput', 'list']).decode()
    for line in lines.split('\n'):
        m = re.search(r'\s(id=(\d+))\s', line)
        if not m:
            continue

        id_ = int(m.group(2))

        if 'touchpad' in line.lower():
            subprocess.call([
                'xinput', 'set-prop', str(id_),
                'libinput Tapping Enabled', '1'])
            subprocess.call([
                'xinput', 'set-prop', str(id_),
                'libinput Natural Scrolling Enabled', '1'])
            subprocess.call([
                'xinput', 'set-prop', str(id_),
                'libinput Accel Profile Enabled', '0,', '1'])

        elif contains(line.lower(), 'mouse', 'asus'):
            subprocess.call([
                'xinput', 'set-prop', str(id_),
                'libinput Accel Profile Enabled', '0,', '1'])

        elif 'wacom' in line.lower():
            if 'stylus' in line.lower():  # pen
                subprocess.call(['xinput', 'map-to-output', str(id_), DISPLAY_EXTERNAL])

            else:  # tablet
                bindings = {
                    # '1': ('key', 'ctrl', 'alt', '4'),  # Button 1
                    '1': ('key', 'ctrl', 'z'),  # Button 1
                    '2': ('key', 'ctrl', 'alt', '3'),  # Button 2
                    '3': ('key', 'ctrl', 'alt', '2'),  # Button 3
                    '8': ('key', 'ctrl', 'alt', '1'),  # Button 4
                }
                for button, action in bindings.items():
                    subprocess.call(['xsetwacom', '--set', str(id_), 'Button', button] + list(action))

    qtile.widgets_map['notification'].update('Input devices updated')


def display_single(qtile):
    randr(output=DISPLAY_EXTERNAL, off=True, is_x11=is_x11())

    internal = {
        'output': DISPLAY_INTERNAL,
        'mode': '2880x1800',
        'refresh': '120',
        'is_x11': is_x11(),
    }
    randr(**internal)
    remap_screens(qtile)


def display_double(qtile):
    external = {
        'output': DISPLAY_EXTERNAL,
        'mode': '1920x1080',
        'refresh': '144',
        'primary': True,
        'is_x11': is_x11(),
    }
    randr(auto=True, is_x11=is_x11())
    randr(**external)

    location = 'left-of'
    if os.path.isdir('/sys/class/drm'):
        for card in os.listdir('/sys/class/drm'):
            edid = os.path.join('/sys/class/drm', card, 'edid')
            if os.path.isfile(edid):
                data = open(edid, 'rb').read()
                if contains(data, b'S2522', b'SONY TV'):
                    location = 'below'

    internal = {
        'output': DISPLAY_INTERNAL,
        'mode': '2880x1800',
        'refresh': '120',
        'is_x11': is_x11(),
    }
    internal[location] = DISPLAY_EXTERNAL
    randr(**internal)
    remap_screens(qtile)


def audio_toggle(qtile):
    qtile.widgets_map['volumemic'].mute()
    volume = qtile.widgets_map['volumemic'].poll()
    state = 'false' if volume > 0 else 'true'
    subprocess.Popen([os.path.expanduser('~/audio_toggle.sh'), state])


def power_switch(profile):
    with open('/sys/devices/system/cpu/intel_pstate/max_perf_pct', 'w') as f:
        if profile == POWER_SAVER:
            f.write(str(25))
        else:
            f.write(str(100))

def audio_play(qtile):
    subprocess.Popen([os.path.expanduser('~/audio_play.sh')])


def next_screen(qtile):
    screen_index = None
    for i, screen in enumerate(qtile.screens):
        if screen is qtile.current_screen:
            screen_index = i
            break

    screen_index += 1
    if screen_index >= len(qtile.screens):
        screen_index = 0

    qtile.focus_screen(screen_index)


def launch_settings(qtile):
    env = dict(os.environ)
    env.update({
        'XDG_SESSION_DESKTOP': 'gnome',
        'XDG_CURRENT_DESKTOP': 'gnome',
    })
    subprocess.Popen(['gnome-control-center'], start_new_session=True, env=env)


def spawn(cmd):
    def f(*args):
        env = {}
        env.update(os.environ)
        # env['DRI_PRIME'] = 'pci-0000_00_02_0'
        process = subprocess.Popen(cmd.split(' '), start_new_session=True, env=env)
        # process.detach()
    return f
