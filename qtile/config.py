import copy
import os
import re
import subprocess
import sys

from libqtile import bar, layout, widget, hook, images, qtile
from libqtile.log_utils import logger
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal
from libqtile.log_utils import logger

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
from qtilemods.widget.volume import Volume
from qtilemods.widget.volumemic import VolumeMic
from qtilemods.widget.wifi import Wifi
from qtilemods.widget.workspaces import Workspaces
from qtilemods.widget.notification import Notification


# TERMINAL = guess_terminal()
TERMINAL = 'kitty'
DISPLAY_INTERNAL = 'eDP-1-1'
DISPLAY_EXTERNAL = 'DP-0'
ICON_THEME = 'Yaru-magenta'
CURSOR_THEME = 'Samurai School Girl'
WALLPAPER = os.path.expanduser('~/Pictures/48.jpg')
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


def xinput_update(qtile):
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

        elif 'table' in line.lower():
            subprocess.call([
                'xinput', 'map-to-output', str(id_), DISPLAY_EXTERNAL])


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
            Match(wm_class=['Blender']),
            Match(wm_class=['Emacs']),
            Match(wm_class=['Gimp-2.10']),
            Match(wm_class=['krita']),
            Match(wm_class=['org.inkscape.Inkscape']),
            Match(title=['Picture-in-Picture']),
            Match(title=['Windowed Projector (Program)']),
        ],
    ),
    Group(
        '3',
        layouts=[layout.MonadTall(ratio=0.6, **TILING_CONFIG)],
        matches=[
            Match(wm_class=['firefox-aurora']),
            Match(wm_class=['Slack']),
        ],
    ),
    Group(
        '4',
        layouts=[Tiling(**TILING_CONFIG)],
        matches=[Match(wm_class=['thunderbird-default'])],
    ),
    Group('5', layouts=[Tiling(**TILING_CONFIG)]),
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
                    this_current_screen_border='#dd0088',
                    this_screen_border='#404040',
                    other_current_screen_border='#0088dd',
                    other_screen_border='#404040',
                    urgent_border='#ff0000',
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
                        'com.discordapp.Discord',
                        'com.slack.Slack',
                        'org.blender.Blender',
                        'org.videolan.VLC',
                        'com.valvesoftware.Steam',
                        'net.lutris.Lutris',
                        'org.keepassxc.KeePassXC',
                    ),
                    padding=4,
                    icon_size=32,
                    # highlight_method='block',
                    border='#dd0088',
                    other_border='#0088dd',
                    unfocused_border='#ffffff',
                    spacing=8,
                    theme_path=ICON_THEME,
                    theme_mode='fallback',
                    margin=12,
                ),

                Notification(
                    highlight_method='line',
                    # font='Ubuntu Mono Bold',
                    fontsize=14,
                    background='#ffffff',
                    foreground='#000000',
                    selected='#dd0088',
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
                    cursor_color='#dd0088',
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
                Volume(
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

    Key([MOD_SUPER], 'tab', lazy.group.next_window(), desc='Switch windows'),
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
    Key([], 'XF86AudioLowerVolume', lazy.widget['volume'].decrease_vol(), desc='Volume down'),
    Key([], 'XF86AudioMute', lazy.widget['volume'].mute(), desc='Volume mute'),
    Key([], 'XF86AudioRaiseVolume', lazy.widget['volume'].increase_vol(), desc='Volume up'),
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
    Key([], 'XF86Launch4', lazy.widget['power'].switch()),
    Key([], 'XF86TouchpadToggle', lazy.function(xinput_update)),
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
]


@hook.subscribe.startup_once
def startup_once():
    subprocess.call([
        'xrandr',
        '--output', DISPLAY_EXTERNAL,
        '--mode', '1920x1080',
        '--refresh', '143.98',
        '--primary',
    ])
    subprocess.call([
        'xrandr',
        '--output', DISPLAY_INTERNAL,
        '--mode', '1920x1080',
        '--refresh', '144',
        '--below', DISPLAY_EXTERNAL,
    ])

    remap_screens(qtile)

    subprocess.Popen(['picom'], start_new_session=True)

    os.putenv('GTK_IM_MODULE', 'ibus')
    os.putenv('QT_IM_MODULE', 'ibus')
    os.putenv('XMODIFIERS', '@im=ibus')
    subprocess.call(['ibus-daemon', '-dxrR'])

    subprocess.call(f'echo "Xcursor.theme: {CURSOR_THEME}" | xrdb -merge', shell=True)
    # subprocess.call(['xset', 'r', 'rate', '300', '25'])  # keyboard auto repeat
    subprocess.call(['xsetroot', '-cursor_name', 'left_ptr'])  # default cursor

    xinput_update(qtile)


# @hook.subscribe.startup_complete
# def startup_complete():
#     qtile.widget['ibus'].update()
#     qtile.widget['volume'].update()


@hook.subscribe.screens_reconfigured
def screens_reconfigured():
    remap_screens(qtile)
