"""Qtile configuration."""
import copy
import os
import re
import subprocess
import sys
import time

from libqtile import bar, layout, widget, hook, qtile
from libqtile.config import (
    Drag, DropDown, Group, Key, Match, Screen, ScratchPad)
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal
from libqtile.log_utils import logger

sys.path.append(os.path.dirname(__file__))

from qtilemods.layout.stacking import Stacking, Unmanaged
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
from qtilemods.tools.randr import randr


IS_X11 = os.getenv('XDG_SESSION_TYPE').lower() == 'x11'


def get_gpu():
    if not IS_X11:
        return 'AMD'

    lines = subprocess.check_output(['glxinfo']).decode()
    for line in lines.split('\n'):
        if line.startswith('OpenGL renderer string:'):
            if 'AMD' in line:
                return 'AMD'
            elif 'NVIDIA' in line:
                return 'NVIDIA'


if os.path.exists('/usr/bin/kitty'):
    TERMINAL = 'kitty'
else:
    TERMINAL = guess_terminal()
DISPLAY_INTERNAL = 'eDP'
DISPLAY_EXTERNAL = 'HDMI' if get_gpu() == 'AMD' else 'DP'
QT_THEME = 'Adwaita'
GTK_THEME = 'Yaru-magenta'
ICON_THEME = 'Yaru-magenta'
CURSOR_THEME = 'Breeze_Light_Samurai'
XDG_PORTALS = ['gnome', 'gtk', '']
if IS_X11:
    XDG_PORTALS.append('wlr')
WALLPAPER_CONFIG = {
    'wallpaper': os.path.expanduser('~/Pictures/Wallpaper.png'),
    'wallpaper_mode': 'fill',
}
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


def contains(line, *values):
    for value in values:
        if type(value) in (list, tuple):
            if contains(line, *value):
                return True
        if value in line:
            return True
    return False


def take_screenshot(area=False):
    def f(qtile):
        path = os.path.expanduser('~/Pictures/Screenshots')
        subprocess.Popen([
            'flatpak', 'run', 'org.flameshot.Flameshot',
            'gui' if area else 'full', '--path', path,
        ], start_new_session=True)

    return f


def remap_screens(qtile):
    if len(qtile.screens) == 1:
        return

    screen_ids = tuple(range(len(qtile.screens)))
    screens = [screen_ids[0], screen_ids[-1]]
    # if not IS_X11:
    #     screens.reverse()

    last_workspace = '6'

    qtile.focus_screen(screens[-1])
    qtile.groups_map[last_workspace].toscreen()
    qtile.focus_screen(screens[0])


def input_update(qtile):
    if not IS_X11:
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

    # subprocess.call(['xmodmap', '-e', 'remove Lock = Caps_Lock'])
    # subprocess.call(['xmodmap', '-e', 'keysym Caps_Lock = F13'])


def display_autoconfig(qtile):
    external = {
        'output': DISPLAY_EXTERNAL,
        'mode': '1920x1080',
        'refresh': '240',
        'primary': True,
    }
    randr(**external)

    internal = {
        'output': DISPLAY_INTERNAL,
        'mode': '1920x1080',
        'refresh': '60',
    }

    location = 'left-of'
    if os.path.isdir('/sys/class/drm'):
        for card in os.listdir('/sys/class/drm'):
            edid = os.path.join('/sys/class/drm', card, 'edid')
            if os.path.isfile(edid):
                data = open(edid, 'rb').read()
                if contains(data, b'S2522', b'SONY TV'):
                    location = 'below'
    internal[location] = DISPLAY_EXTERNAL

    randr(**internal)

    internal['refresh'] = '144'
    randr(**internal)


def display_toggle(qtile):
    if IS_X11:
        cmd = ['xrandr', '--listactivemonitors']
    else:
        cmd = ['wlr-randr']
    lines = subprocess.check_output(cmd).decode()

    have_external = False
    for line in lines.split('\n'):
        if DISPLAY_EXTERNAL in line:
            have_external = True
            break

    if have_external:
        randr(output=DISPLAY_EXTERNAL, off=True)
    else:
        display_autoconfig(qtile)
    remap_screens(qtile)


def audio_toggle(qtile):
    qtile.widgets_map['volumemic'].mute()
    volume = qtile.widgets_map['volumemic'].poll()
    state = 'false' if volume > 0 else 'true'
    subprocess.Popen([os.path.expanduser('~/audio_toggle.sh'), state])


def audio_activate(qtile):
    subprocess.Popen([os.path.expanduser('~/audio_activate.sh')])


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


# Configuration variables
auto_fullscreen = True
auto_minimize = True
bring_front_click = True
floats_kept_above = False
cursor_warp = False
dgroups_key_binder = None
dgroups_app_rules = []
extension_defaults = {
    'font': 'Ubuntu Bold',
    'fontsize': 16,
    'padding': 8,
    'margin': 8,
}
focus_on_window_activation = 'smart'
follow_mouse_focus = False
widget_defaults = copy.copy(extension_defaults)
reconfigure_screens = True
wmname = 'LG3D'
wl_input_rules = {}

if not IS_X11:
    from libqtile.backend.wayland import InputConfig
    # qtile cmd-obj -o core -f get_inputs
    wl_input_rules.update({
        'type:touchpad': InputConfig(
            tap=True,
            natural_scroll=True,
            scroll_method='two_finger',
        ),
        'type:pointer': InputConfig(
            pointer_accel=False,
        ),
        'type:keyboard': InputConfig(
            kb_layout='us,ru',
            kb_options='caps:none',
        ),
    })

groups = []
layouts = [Tiling(**TILING_CONFIG)]
floating_layout = Stacking(
    float_rules=Stacking.default_float_rules + [
        Match(wm_class='Gthumb'),
        Match(wm_class='org.gnome.Nautilus'),
        Match(wm_class='zoom'),
    ], **STACKING_CONFIG
)

workspaces = [
    Group(
        '1',
        layouts=[Unmanaged(**TILING_CONFIG)],
        matches=[
            Match(wm_class='discord'),
        ],
    ),

    Group(
        '2',
        layouts=[Tiling(**TILING_CONFIG)],
        matches=[
            Match(wm_class='Emacs'),
        ],
    ),

    Group(
        '3',
        layouts=[layout.MonadTall(ratio=0.6, **TILING_CONFIG)],
        matches=[
            Match(wm_class='Slack'),
            Match(wm_class='TelegramDesktop'),
            Match(wm_class='firefox-aurora'),
        ],
    ),

    Group(
        '4',
        layouts=[Tiling(**TILING_CONFIG)],
        matches=[
            Match(wm_class='thunderbird'),
            Match(wm_class='thunderbird-default'),
        ],
    ),

    Group(
        '5',
        layouts=[layout.Max()],
        matches=[
            Match(wm_class='Blender'),
            Match(wm_class='Gimp-2.10'),
            Match(wm_class='NVIDIA Nsight Graphics'),
            Match(wm_class='Substance Designer'),
            Match(wm_class='Unity'),
            Match(wm_class='Waveform'),
            Match(wm_class='kdenlive'),
            Match(wm_class='krita'),
            Match(wm_class='maya.bin'),
            Match(wm_class='org.inkscape.Inkscape'),
            Match(wm_class='tiled'),
        ],
    ),

    Group(
        '6',
        layouts=[Tiling(**TILING_CONFIG)],
        matches=[
            Match(title='Picture-in-Picture'),
            Match(title='Windowed Projector (Program)'),
        ],
    ),
]
groups.extend(workspaces)

scratch = [
    ScratchPad('scratchpad', [
       DropDown(
           'good',
           'gnome-disks',
           x=0,
           y=0,
           width=0.5,
           height=0.5,
           opacity=0.5,
       ),
    ]),
]
groups.extend(scratch)

extra_widgets = [
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
]

if IS_X11:
    extra_widgets.append(
        Power(
           foreground='#ffffff',
           theme_path=ICON_THEME,
           icon_ext='.svg',
           icon_size=16,
           update_interval=60,
        ),
    )

extra_widgets += [
    VolumeMic(
        foreground='#ffffff',
        theme_path=ICON_THEME,
        channel='@DEFAULT_AUDIO_SOURCE@',
        media_class='Audio/Source',
        icon_ext='.svg',
        icon_size=16,
        update_interval=15,
    ),
]

widgets = [
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
            'discord_local',
            'com.slack.Slack',
            'org.telegram.desktop',
            'org.blender.Blender',
            'org.videolan.vlc',
            'com.valvesoftware.Steam',
            'org.keepassxc.KeePassXC',
            'com.cisco.anyconnect.gui',
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
        widgets=extra_widgets,
        close_button_location='right',
        text_closed='',
        text_open='',
        foreground='#ffffff',
        theme_path=ICON_THEME,
        icon_ext='.svg',
        icon_size=16,
    ),

    widget.OpenWeather(
       app_key='1ac10b77792f33e3a615410d8eed11f7',
       location='Saint Petersburg, RU',
       format='{icon} {main_temp:.0f} °{units_temperature}',
    ),
]

if IS_X11:
    widgets.append(
        IBUS(
          configured_keyboards=[
              'xkb:us::eng',
              'xkb:ru::rus',
              'anthy',
          ],
          display_map={
              'anthy': 'jap',
          },
          option='caps:none',
          fontsize=14,
          update_interval=15,
          background='#ffffff',
          foreground='#404040',
          padding_x=4,
          padding_y=4,
        ),
    )

widgets += [
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
]

screens = [
    Screen(
        top=bar.Bar(
            widgets,
            48,
            border_width=[0, 0, 0, 0],
            margin=0,
            background="#00000080",
        ),
        **WALLPAPER_CONFIG
    ),

    Screen(**WALLPAPER_CONFIG)
]
# if not IS_X11:
#     screens.reverse()

# Keyboard shortcuts, based on GNOME:
# https://help.gnome.org/users/gnome-help/stable/keyboard-shortcuts-set.html.en

# Navigation
keys = [
    Key([MOD_SUPER], 'page_up', lazy.screen.prev_group(),
        desc='Move to previous workspace'),
    Key([MOD_CONTROL, MOD_ALT], 'left', lazy.screen.prev_group(),
        desc='Move to previous workspace'),
    Key([MOD_CONTROL, MOD_ALT], 'down',
       lazy.group['scratchpad'].dropdown_toggle('good'),
       desc=''),

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
    for group in workspaces
] + [
    Key([MOD_SUPER], group.name, lazy.group[group.name].toscreen(),
        desc=f'Switch to workspace {group.name}')
    for group in workspaces
]

# Screenshots
keys += [
    # Key([MOD_SHIFT], 'print', lazy.function(take_screenshot(area=True)),
    #     desc='Save a screenshot of an area to Pictures'),
    # Key([], 'print', lazy.function(take_screenshot()),
    #     desc='Save a screenshot to Pictures'),
]

# Sounds and Media
keys += [
    Key([], 'XF86AudioLowerVolume', lazy.widget['pipewirevolume'].decrease_vol(), desc='Volume down'),
    Key([], 'XF86AudioMute', lazy.widget['pipewirevolume'].mute(), desc='Volume mute'),
    Key([], 'XF86AudioRaiseVolume', lazy.widget['pipewirevolume'].increase_vol(), desc='Volume up'),
    # Key([], 'XF86AudioMicMute', lazy.widget['volumemic'].mute(), desc='Mic mute'),
    Key([], 'XF86AudioMicMute', lazy.function(audio_toggle, desc='Mic mute')),
]

# System
keys += [
    Key([MOD_CONTROL, MOD_ALT], 'delete', lazy.shutdown(), desc='Log out'),
    # Key([MOD_SUPER], 'v', lazy.widget['box'].toggle(), desc='Show/hide the widgets box'),
    Key([MOD_ALT], 'F2', lazy.spawncmd(prompt='> ', widget='entry', complete='entry'),
        desc='Show the run command prompt'),
    Key([MOD_SUPER], 'r', lazy.spawncmd(prompt='> ', widget='entry', complete='entry'),
        desc='Show the run command prompt'),

    Key([], 'XF86KbdBrightnessUp', lazy.widget['keyboardlight'].change_backlight(ChangeDirection.UP)),
    Key([], 'XF86KbdBrightnessDown', lazy.widget['keyboardlight'].change_backlight(ChangeDirection.DOWN)),
    Key([], 'XF86MonBrightnessUp', lazy.widget['displaylight'].change_backlight(ChangeDirection.UP)),
    Key([], 'XF86MonBrightnessDown', lazy.widget['displaylight'].change_backlight(ChangeDirection.DOWN)),
    Key([MOD_SUPER], 'p', lazy.function(display_toggle)),
    Key([], 'XF86Launch1', lazy.function(audio_activate), desc='ROG button'),
    Key([], 'XF86Launch3', lazy.spawn('asusctl led-mode -n'), desc='AURA button'),
    Key([], 'XF86TouchpadToggle', lazy.function(input_update)),
]

if IS_X11:
    keys += [
        Key([], 'XF86Launch4', lazy.widget['power'].switch(), desc='FAN button'),
    ]

# Typing
if IS_X11:
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
    Key([MOD_CONTROL, MOD_SUPER], 'F5', lazy.reload_config(), desc='Reload configuration'),
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
]


@hook.subscribe.startup_once
def startup_once():
    display_autoconfig(qtile)
    remap_screens(qtile)

    os.putenv('GTK_IM_MODULE', 'ibus')
    os.putenv('QT_IM_MODULE', 'ibus')
    os.putenv('XMODIFIERS', '@im=ibus')

    if IS_X11:
        profile = subprocess.check_output(['powerprofilesctl', 'get']).decode().strip('\n')
        if profile == 'balanced':
            subprocess.Popen(['picom'], start_new_session=True)
    subprocess.call(['ibus-daemon', '-dxrR'])

    env = dict(os.environ)
    env.update({
        'XDG_SESSION_DESKTOP': 'gnome',
        'XDG_CURRENT_DESKTOP': 'gnome',
    })

    for portal in XDG_PORTALS:
        path = list(filter(None, ['/usr/libexec/xdg-desktop-portal', portal]))
        subprocess.Popen(['-'.join(path), '-vr'], start_new_session=True, env=env)


@hook.subscribe.startup
def startup():
    if IS_X11:
        subprocess.call(f'echo "Xcursor.theme: {CURSOR_THEME}" | xrdb -merge', shell=True)
        subprocess.call('echo "Xft.antialias: 1" | xrdb -merge', shell=True)
        subprocess.call('echo "Xft.hinting: 0" | xrdb -merge', shell=True)
        subprocess.call('echo "Xft.hintstyle: hintnone" | xrdb -merge', shell=True)
        subprocess.call('echo "Xft.lcdfilter: lcddefault" | xrdb -merge', shell=True)
        subprocess.call('echo "Xft.rgba: rgb" | xrdb -merge', shell=True)
        subprocess.call('echo "Xft.rgba: rgb" | xrdb -merge', shell=True)
        subprocess.call(['xsetroot', '-cursor_name', 'left_ptr'])  # default cursor

    os.putenv('GTK_CSD', '1')
    # os.putenv('GTK_THEME', GTK_THEME)
    os.putenv('ICON_THEME', ICON_THEME)
    os.putenv('LANG', 'en_GB.UTF-8')
    os.putenv('MOZ_GTK_TITLEBAR_DECORATION', 'client')
    os.putenv('MOZ_USE_XINPUT2', '1')
    os.putenv('QT_STYLE_OVERRIDE', QT_THEME)
    # os.putenv('QT_QPA_PLATFORMTHEME', 'gnome')  # need qgnomeplatform-qt*
    # os.putenv('FREETYPE_PROPERTIES', 'cff:no-stem-darkening=0 autofitter:no-stem-darkening=0')

    input_update(qtile)


@hook.subscribe.shutdown
def shutdown():
    subprocess.call(['pkill', 'picom'])

    for portal in XDG_PORTALS:
        name = list(filter(None, ['xdg-desktop-portal', portal]))
        subprocess.call(['pkill', '-'.join(name)])


@hook.subscribe.screens_reconfigured
def screens_reconfigured():
    remap_screens(qtile)


@hook.subscribe.float_change
def float_change():
    has_fullscreen = False

    for group in qtile.groups:
        for window in group.windows:
            if window.fullscreen:
                has_fullscreen = True
                break

    if has_fullscreen:
        subprocess.call(['xset', 's', 'noblank'])
        subprocess.call(['xset', 's', 'off'])
        subprocess.call(['xset', '-dpms'])
    else:
        subprocess.call(['xset', 's', 'blank'])
        subprocess.call(['xset', 's', 'on'])
        subprocess.call(['xset', '+dpms'])
