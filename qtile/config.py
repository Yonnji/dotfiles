import copy
import os
import re
import subprocess
import sys
import time

from libqtile import bar, layout, widget, hook, images, qtile
from libqtile.command.base import expose_command
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.lazy import lazy
from libqtile.log_utils import logger
from libqtile.utils import guess_terminal

sys.path.append(os.path.dirname(__file__))

from qtilemods.layout.stacking import Stacking
from qtilemods.layout.tiling import Tiling
from qtilemods.widget.battery import Battery
from qtilemods.widget.bluetooth import Bluetooth
from qtilemods.widget.box import Box
from qtilemods.widget.displaylight import DisplayLight, ChangeDirection
from qtilemods.widget.dock import Dock
from qtilemods.widget.entry import Entry
from qtilemods.widget.ibus import IBUS
from qtilemods.widget.keyboardlight import KeyboardLight
from qtilemods.widget.power import Power
from qtilemods.widget.pipewire_volume import PipewireVolume
from qtilemods.widget.volumemic import VolumeMic
from qtilemods.widget.wifi import Wifi
from qtilemods.widget.workspaces import Workspaces
from qtilemods.widget.notification import Notification


if os.path.exists('/bin/kitty'):
    TERMINAL = 'kitty'
else:
    TERMINAL = guess_terminal()
DISPLAY_INTERNAL = 'eDP-1-1'
DISPLAY_EXTERNAL = 'DP-0'
ICON_THEME = 'Yaru-magenta'
CURSOR_THEME = 'Breeze_Light_Samurai'
WALLPAPER = os.path.expanduser('~/Pictures/wallpaper.jpeg')
ACCENT_COLOR_A = '#E91E63'
ACCENT_COLOR_B = '#2196F3'
STACKING_CONFIG = {
    'border_focus': '#ff00aa',
    'border_normal': '#888888',
    'border_width': 2,
}
TILING_CONFIG = {
    'border_focus': '#00ffff',
    'border_normal': '#888888',
    'border_width': 2,
    'border_on_single': True,
    'margin': 4,
}

# Modifiers, check with "xmodmap"
MOD_CONTROL = 'control'
MOD_ALT = 'mod1'
MOD_SHIFT = 'shift'
MOD_SUPER = 'mod4'


def take_screenshot(area=False):
    def f(qtile):
        path = os.path.expanduser('~/Pictures/Screenshots')
        subprocess.Popen([
            'flatpak', 'run', 'org.flameshot.Flameshot',
            'gui' if area else 'full', '--path', path,
        ], start_new_session=True)

    return f


def remap_screens(qtile):
    if len(qtile.screens) > 1:
        group = groups[-1]
        for i in range(1, len(qtile.screens)):
            qtile.focus_screen(i)
            qtile.groups_map[group.name].toscreen()
        qtile.focus_screen(0)


def input_update(qtile):
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

        elif 'mouse' in line.lower():
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


def xrandr(**opts):
    args = ['xrandr']
    for k in ('output', 'mode', 'refresh', 'primary', 'off', 'below', 'left-of'):
        if k in opts:
            if opts[k] is True:
                args += [f'--{k}']
            else:
                args += [f'--{k}', opts[k]]

    logger.info(' '.join(args))
    subprocess.call(args)


def display_autoconfig(qtile):
    external = {
        'output': DISPLAY_EXTERNAL,
        'mode': '1920x1080',
        'refresh': '143.98',
        'primary': True,
    }
    xrandr(**external)

    internal = {
        'output': DISPLAY_INTERNAL,
        'mode': '1920x1080',
        'refresh': '60.01',
        # 'below': DISPLAY_EXTERNAL,
        'left-of': DISPLAY_EXTERNAL,
    }
    xrandr(**internal)

    internal['refresh'] = '144'
    xrandr(**internal)


def display_toggle(qtile):
    lines = subprocess.check_output(['xrandr', '--listmonitors']).decode()

    have_external = False
    for line in lines.split('\n'):
        fields = line.split(' ')
        if fields and fields[-1] == DISPLAY_EXTERNAL:
            have_external = True
            break

    if have_external:
        xrandr(output=DISPLAY_EXTERNAL, off=True)
    else:
        display_autoconfig(qtile)
    remap_screens(qtile)


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


def spawn_later(cmd, t):
    def f(qtile):
        time.sleep(t)
        qtile.spawn(cmd)

    return f


def set_position_floating(qtile, x, y):
    with open(os.path.expanduser('~') + '/qtile.log', 'w') as f:
        f.write(f'set_position_floating {qtile} {x} {y}\n')


# Configuration variables
auto_fullscreen = True
bring_front_click = True
cursor_warp = False
dgroups_key_binder = None
dgroups_app_rules = []
extension_defaults = {
    'font': 'Ubuntu Bold',
    'fontsize': 16,
    'padding': 8,
    'margin': 8,
}
floating_layout = Stacking(**STACKING_CONFIG)
focus_on_window_activation = 'smart'
follow_mouse_focus = False
widget_defaults = copy.copy(extension_defaults)
reconfigure_screens = True
wmname = 'LG3D'
auto_minimize = True
wl_input_rules = None

layouts = [Tiling(**TILING_CONFIG)]

groups = [
    Group(
        '1',
        layouts=[floating_layout],
        matches=[
            Match(wm_class=['discord']),
        ],
    ),

    Group(
        '2',
        layouts=[Tiling(**TILING_CONFIG)],
        matches=[
            Match(title=['Picture-in-Picture']),
            Match(title=['Windowed Projector (Program)']),
            Match(wm_class=['Emacs']),
        ],
    ),

    Group(
        '3',
        layouts=[layout.MonadTall(ratio=0.6, **TILING_CONFIG)],
        matches=[
            Match(wm_class=['Slack']),
            Match(wm_class=['firefox-aurora']),
        ],
    ),

    Group(
        '4',
        layouts=[Tiling(**TILING_CONFIG)],
        matches=[Match(wm_class=['thunderbird-default'])],
    ),

    Group(
        '5',
        layouts=[layout.Max()],
        matches=[
            Match(wm_class=['Blender']),
            Match(wm_class=['Gimp-2.10']),
            Match(wm_class=['NVIDIA Nsight Graphics']),
            Match(wm_class=['Substance Designer']),
            Match(wm_class=['Unity']),
            Match(wm_class=['Waveform']),
            Match(wm_class=['kdenlive']),
            Match(wm_class=['krita']),
            Match(wm_class=['maya.bin']),
            Match(wm_class=['org.inkscape.Inkscape']),
            Match(wm_class=['tiled']),
        ],
    ),

    Group('6', layouts=[layout.Max()]),
]

screens = [
    Screen(
        x11_drag_polling_rate=144,
        wallpaper=WALLPAPER,
        wallpaper_mode='fill',
        top=bar.Bar(
            [
                Workspaces(
                    highlight_method='block',
                    active='#ffffff',
                    inactive='#aaaaaa',
                    block_highlight_text_color='#ffffff',
                    this_current_screen_border=ACCENT_COLOR_A,
                    this_screen_border='#404040',
                    other_current_screen_border=ACCENT_COLOR_B,
                    other_screen_border='#404040',
                    urgent_border=None,
                    padding_x=8,
                    padding_y=4,
                    spacing=0,
                    disable_drag=True,
                    theme_path=ICON_THEME,
                    icon_ext='.svg',
                    icon_size=16,
                    icon_spacing=4,
                    margin=12,
                ),
                Dock(
                    pinned_apps=(
                        'firefox',
                        'firefox-aurora',
                        'org.mozilla.Thunderbird',
                        'kitty',
                        'emacs',
                        'org.gnome.Nautilus',
                        'discord',
                        'com.slack.Slack',
                        'org.blender.Blender',
                        'org.videolan.VLC',
                        'com.valvesoftware.Steam',
                        'net.lutris.Lutris',
                        'org.keepassxc.KeePassXC',
                    ),
                    padding=4,
                    icon_size=32,
                    fontsize=14,
                    border=ACCENT_COLOR_A,
                    other_border=ACCENT_COLOR_B,
                    unfocused_border='#ffffff',
                    spacing=8,
                    theme_path=ICON_THEME,
                    theme_mode='fallback',
                    margin=12,
                ),

                Notification(
                    highlight_method='line',
                    fontsize=14,
                    background='#ffffff',
                    foreground='#000000',
                    selected=ACCENT_COLOR_A,
                    borderwidth=2,
                    size=128,
                    padding_x=8,
                    padding_y=2,
                    margin=12,
                ),
                Entry(
                    prompt='{prompt}',
                    font='Ubuntu Mono',
                    fontsize=16,
                    background='#ffffff',
                    foreground='#000000',
                    cursor_color=ACCENT_COLOR_A,
                    padding_x=16,
                    padding_y=2,
                    margin=12,
                ),

                Box(
                    widgets=[
                        DisplayLight(
                            foreground='#ffffff',
                            theme_path=ICON_THEME,
                            icon_ext='.svg',
                            icon_size=16,
                            icon_spacing=2,
                            update_interval=15,
                            backlight_name='amdgpu_bl1',
                            change_command='brightnessctl -d amdgpu_bl1 set {0}',
                            step=16,
                        ),
                        KeyboardLight(
                            foreground='#ffffff',
                            theme_path=ICON_THEME,
                            icon_ext='.svg',
                            icon_size=16,
                            icon_spacing=2,
                            update_interval=15,
                            backlight_name='asus::kbd_backlight',
                            change_command='brightnessctl -d asus::kbd_backlight set {0}',
                            step=1,
                        ),
                        Power(
                            foreground='#ffffff',
                            theme_path=ICON_THEME,
                            icon_ext='.svg',
                            icon_size=16,
                            update_interval=60,
                        ),
                        VolumeMic(
                            foreground='#ffffff',
                            theme_path=ICON_THEME,
                            icon_ext='.svg',
                            icon_size=16,
                            update_interval=15,
                        ),
                    ],
                    close_button_location='right',
                    text_closed='',
                    text_open='',
                    foreground='#ffffff',
                    theme_path=ICON_THEME,
                    icon_ext='.svg',
                    icon_size=16,
                ),

                widget.OpenWeather(
                    location='Saint Petersburg, RU',
                    format='{icon} {main_temp:.0f} °{units_temperature}',
                ),
                IBUS(
                    configured_keyboards=[
                        'xkb:us::eng',
                        'xkb:ru::rus',
                        'anthy',
                    ],
                    display_map={
                        'anthy': 'jap',
                    },
                    fontsize=14,
                    update_interval=15,
                    background='#ffffff',
                    foreground='#404040',
                    padding_x=4,
                    padding_y=4,
                ),
                PipewireVolume(
                    foreground='#ffffff',
                    theme_path=ICON_THEME,
                    icon_ext='.svg',
                    icon_size=16,
                    update_interval=15,
                ),
                Bluetooth(
                    foreground='#ffffff',
                    theme_path=ICON_THEME,
                    icon_ext='.svg',
                    icon_size=16,
                    update_interval=15,
                ),
                Wifi(
                    foreground='#ffffff',
                    theme_path=ICON_THEME,
                    icon_ext='.svg',
                    icon_size=16,
                    update_interval=60,
                ),
                Battery(
                    foreground='#ffffff',
                    theme_path=ICON_THEME,
                    icon_ext='.svg',
                    icon_size=16,
                    icon_spacing=2,
                    format='{percent:2.0%}',
                    padding=12,
                ),
                widget.Clock(format="%d %b %H:%M"),
            ],
            48,
            border_width=[0, 0, 0, 0],
            margin=0,
            background="#00000080",
        ),
    ),

    Screen(
       x11_drag_polling_rate=144,
       wallpaper=WALLPAPER,
       wallpaper_mode='fill',
    )
]
# screens.reverse()
# Keyboard shortcuts, based on GNOME:
# https://help.gnome.org/users/gnome-help/stable/keyboard-shortcuts-set.html.en

# Navigation
keys = [
    Key([MOD_SUPER], 'page_up', lazy.screen.prev_group(),
        desc='Move to previous workspace'),
    Key([MOD_CONTROL, MOD_ALT], 'left', lazy.screen.prev_group(),
        desc='Move to previous workspace'),

    Key([MOD_SUPER], 'page_down', lazy.screen.next_group(),
        desc='Move to next workspace'),
    Key([MOD_CONTROL, MOD_ALT], 'right', lazy.screen.next_group(),
        desc='Move to next workspace'),

    Key([MOD_SUPER, MOD_SHIFT], 'down', lazy.layout.shuffle_down(),
        desc='Move window down'),
    Key([MOD_SUPER, MOD_SHIFT], 'left', lazy.layout.shuffle_left(),
        desc='Move window to the left'),
    Key([MOD_SUPER, MOD_SHIFT], 'right', lazy.layout.shuffle_right(),
        desc='Move window to the right'),
    Key([MOD_SUPER, MOD_SHIFT], 'up', lazy.layout.shuffle_up(),
        desc='Move window up'),

    Key([MOD_SUPER], 'down', lazy.layout.down(), desc='Move focus down'),
    Key([MOD_SUPER], 'left', lazy.layout.left(), desc='Move focus to the left'),
    Key([MOD_SUPER], 'right', lazy.layout.right(), desc='Move focus to the right'),
    Key([MOD_SUPER], 'up', lazy.layout.up(), desc='Move focus up'),

    Key([MOD_SUPER], 'tab', lazy.function(next_screen), desc='Switch screens'),
    Key([MOD_ALT], 'tab', lazy.group.next_window(), desc='Switch windows'),
] + [
    Key([MOD_SUPER, MOD_SHIFT], group.name, lazy.window.togroup(group.name),
        desc=f'Move window to workspace {group.name}')
    for group in groups
] + [
    Key([MOD_SUPER], group.name, lazy.group[group.name].toscreen(),
        desc=f'Switch to workspace {group.name}')
    for group in groups
]

# Screenshots
keys += [
    Key([MOD_SHIFT], 'print', lazy.function(take_screenshot(area=True)),
        desc='Save a screenshot of an area to Pictures'),
    Key([], 'print', lazy.function(take_screenshot()),
        desc='Save a screenshot to Pictures'),
]

# Sounds and Media
keys += [
    Key([], 'XF86AudioLowerVolume', lazy.widget['pipewirevolume'].decrease_vol(), desc='Volume down'),
    Key([], 'XF86AudioMute', lazy.widget['pipewirevolume'].mute(), desc='Volume mute'),
    Key([], 'XF86AudioRaiseVolume', lazy.widget['pipewirevolume'].increase_vol(), desc='Volume up'),
    Key([], 'XF86AudioMicMute', lazy.widget['volumemic'].mute(), desc='Mic mute'),
]

# System
keys += [
    Key([MOD_CONTROL, MOD_ALT], 'delete', lazy.shutdown(), desc='Log out'),
    Key([MOD_SUPER], 'v', lazy.widget['box'].toggle(), desc='Show/hide the widgets box'),
    Key([MOD_ALT], 'F2', lazy.spawncmd(prompt='> ', widget='entry', complete='entry'),
        desc='Show the run command prompt'),
    Key([MOD_SUPER], 'r', lazy.spawncmd(prompt='> ', widget='entry', complete='entry'),
        desc='Show the run command prompt'),

    Key([], 'XF86KbdBrightnessUp', lazy.widget['keyboardlight'].change_backlight(ChangeDirection.UP)),
    Key([], 'XF86KbdBrightnessDown', lazy.widget['keyboardlight'].change_backlight(ChangeDirection.DOWN)),
    Key([], 'XF86MonBrightnessUp', lazy.widget['displaylight'].change_backlight(ChangeDirection.UP)),
    Key([], 'XF86MonBrightnessDown', lazy.widget['displaylight'].change_backlight(ChangeDirection.DOWN)),
    Key([], 'XF86Launch1', lazy.function(display_toggle)),
    Key([], 'XF86Launch3', lazy.spawn('asusctl led-mode -n')),
    Key([], 'XF86Launch4', lazy.widget['power'].switch()),
    Key([], 'XF86TouchpadToggle', lazy.function(input_update)),
]

# Typing
keys += [
    Key([MOD_CONTROL], 'space', lazy.widget['ibus'].next_keyboard(),
        desc='Switch to next input source'),
    Key([MOD_CONTROL, MOD_SHIFT], 'space', lazy.widget['ibus'].prev_keyboard(),
        desc='Switch to next input source'),
    Key([MOD_SUPER], 'space', lazy.widget['ibus'].toggle_keyboard(),
        desc='Toggle between last input sources'),
]

# Windows
keys += [
    Key([MOD_ALT], 'F4', lazy.window.kill(), desc='Close window'),
    Key([MOD_SUPER], 'H', lazy.window.toggle_minimize(), desc='Toggle minimization state'),
    Key([MOD_ALT], 'F10', lazy.window.toggle_maximize(), desc='Toggle maximization state'),
    Key([MOD_ALT], 'F11', lazy.window.toggle_fullscreen(), desc='Toggle fullscreen state'),
]

keys += [
    Key([MOD_CONTROL, MOD_SHIFT], 'escape', lazy.spawn('gnome-system-monitor'),
        desc='Open System Monitor'),
    Key([MOD_SUPER], 'f', lazy.window.toggle_floating(), desc='Toggle floating'),
    Key([MOD_CONTROL, MOD_SUPER], 'r', lazy.reload_config(), desc='Reload configuration'),
    Key([MOD_SUPER], 'l', lazy.function(spawn_later('xset dpms force off', 0.25)), desc='Turn off the displays'),
]

mouse = [
    Drag([MOD_SUPER], 'Button1', lazy.window.set_position_floating(),
         start=lazy.window.get_position()),
    Drag([MOD_SUPER], 'Button2', lazy.window.set_size_floating(),
         start=lazy.window.get_size()),
    Drag([MOD_SUPER], 'Button3', lazy.window.set_size_floating(),
         start=lazy.window.get_size()),
    Drag([MOD_SUPER, MOD_CONTROL], 'Button1', lazy.window.set_size_floating(),
         start=lazy.window.get_size()),

    # Drag([], 'Button1', lazy.window.set_position_floating(),
    #      start=lazy.window.get_position()),

    # Drag([MOD_ALT], 'Button1', lazy.function(set_position_floating)),
]


@hook.subscribe.startup_once
def startup_once():
    display_autoconfig(qtile)
    remap_screens(qtile)

    profile = subprocess.check_output(['powerprofilesctl', 'get']).decode().strip('\n')
    if profile == 'balanced':
        subprocess.Popen(['picom'], start_new_session=True)

    os.putenv('GTK_IM_MODULE', 'ibus')
    os.putenv('QT_IM_MODULE', 'ibus')
    os.putenv('XMODIFIERS', '@im=ibus')
    subprocess.call(['ibus-daemon', '-dxrR'])
    subprocess.call(['setxkbmap', '-option', 'caps:none'])


@hook.subscribe.startup
def startup():
    subprocess.call(f'echo "Xcursor.theme: {CURSOR_THEME}" | xrdb -merge', shell=True)
    subprocess.call(['xsetroot', '-cursor_name', 'left_ptr'])  # default cursor

    input_update(qtile)


@hook.subscribe.screens_reconfigured
def screens_reconfigured():
    remap_screens(qtile)
