"""Qtile configuration."""
import copy
import os
import re
import subprocess
import sys
import time

from libqtile import bar, widget, hook, qtile
from libqtile.config import (
    Drag, DropDown, Group, Key, Match, Screen, ScratchPad)
from libqtile.lazy import lazy
from libqtile.log_utils import logger

sys.path.append(os.path.dirname(__file__))

from qtilemods.layout.floating import Floating
from qtilemods.layout.tiling import Bsp, Max, MonadTall
from qtilemods.tools.gtk import set_gtk_settings
from qtilemods.tools.portal import portals_start, portals_stop
from qtilemods.tools.xrdb import xrdb_merge
from qtilemods.tools import shortcuts
from qtilemods.tools.inhibit import float_change_dbus, uninhibit_dbus
from qtilemods.widget.battery import Battery
from qtilemods.widget.bluetooth import Bluetooth
from qtilemods.widget.box import Box
from qtilemods.widget.displaylight import DisplayLight, ChangeDirection
from qtilemods.widget.dock import Dock
from qtilemods.widget.entry import Entry
from qtilemods.widget.ibus import IBUS
from qtilemods.widget.keyboardlight import KeyboardLight
from qtilemods.widget.notification import Notification
from qtilemods.widget.pulse_volume import PulseVolume
from qtilemods.widget.pipewire_volume import PipewireVolume
from qtilemods.widget.power import Power
from qtilemods.widget.network_manager import NetworkManager
from qtilemods.widget.workspaces import Workspaces

Volume = PulseVolume if os.path.exists('/usr/bin/pulseaudio') else PipewireVolume

SCALE = 1
BASE_DPI = 96
DPI = BASE_DPI * SCALE
# SCALE = 2
GTK_THEME = 'Colloid-Pink-Light'
# GTK_THEME = 'Adwaita'
QT_THEME = 'kvantum'
ICON_THEME = 'Papirus-Light'
PANEL_ICON_THEME = 'Papirus-Dark'
CURSOR_THEME = 'Breeze_Light_Samurai'
# CURSOR_THEME = 'Breeze_Light'
CURSOR_SIZE = 24 * SCALE
ACCENT_COLOR_A = '#E91E63'
ACCENT_COLOR_B = '#2196F3'
FLOATING_CONFIG = {
    'border_focus': '#ff00aa',
    'border_normal': '#888888',
    'border_width': 2 * SCALE,
}
TILING_CONFIG = {
    'border_focus': '#00ffff',
    'border_normal': '#888888',
    'border_width': 2 * SCALE,
    'border_on_single': True,
    'margin': 4 * SCALE,
}

# Modifiers, check with "xmodmap"
MOD_CONTROL = 'control'
MOD_ALT = 'mod1'
MOD_SHIFT = 'shift'
MOD_SUPER = 'mod4'

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
    'fontsize': 16 * SCALE,
    'padding': 8 * SCALE,
    'margin': 8 * SCALE,
}
focus_on_window_activation = 'smart'
follow_mouse_focus = False
widget_defaults = copy.copy(extension_defaults)
reconfigure_screens = True
wmname = 'LG3D'
wl_input_rules = {}

if not shortcuts.is_x11():
    from libqtile.backend.wayland import InputConfig
    # qtile cmd-obj -o core -f get_inputs
    wl_input_rules.update({
        'type:touchpad': InputConfig(
            accel_profile='flat',
            pointer_accel=0,
            natural_scroll=True,
            scroll_method='two_finger',
            tap=True,
        ),
        'type:pointer': InputConfig(
            accel_profile='flat',
            pointer_accel=0,
        ),
        'type:keyboard': InputConfig(
            kb_layout='us,ru',
            kb_options='caps:none grp:win_space_toggle',
        ),
    })

groups = []

layouts = [
    Bsp(**TILING_CONFIG),
    MonadTall(ratio=0.6, **TILING_CONFIG),
    Max(**TILING_CONFIG),
]

floating_layout = Floating(
    float_rules_exclude=[
        Match(title='Picture-in-Picture'),
        Match(title='Windowed Projector (Program)'),
    ],
    tiling_rules=[
        Match(wm_class='Blender'),
        Match(wm_class='Buttercup'),
        Match(wm_class='Chromium-browser'),
        Match(wm_class='Emacs'),
        Match(wm_class='Emacs-gtk+x11'),
        Match(wm_class='Gimp-2.10'),
        Match(wm_class='LibreWolf'),
        Match(wm_class='NVIDIA Nsight Graphics'),
        Match(wm_class='Quodlibet'),
        Match(wm_class='Substance Designer'),
        Match(wm_class='TelegramDesktop'),
        Match(wm_class='Unity'),
        Match(wm_class='baobab'),
        Match(wm_class='discord'),
        Match(wm_class='firefox-aurora'),
        Match(wm_class='game-jolt-client'),
        Match(wm_class='itch'),
        Match(wm_class='kdenlive'),
        Match(wm_class='kitty'),
        Match(wm_class='krita'),
        Match(wm_class='libreoffice'),
        Match(wm_class='maya.bin'),
        Match(wm_class='obs'),
        Match(wm_class='openshot'),
        Match(wm_class='org.gnome.Nautilus'),
        Match(wm_class='org.inkscape.Inkscape'),
        Match(wm_class='org.mozilla.thunderbird'),
        Match(wm_class='pstats'),
        Match(wm_class='steam'),
        Match(wm_class='thunderbird'),
        Match(wm_class='thunderbird-default'),
        Match(wm_class='tiled'),
    ], **FLOATING_CONFIG
)

workspaces = [
    Group('1', layouts=[
        MonadTall(ratio=0.4, **TILING_CONFIG),
        Bsp(**TILING_CONFIG),
        Max(**TILING_CONFIG),
    ], matches=[
        Match(wm_class='Buttercup'),
        Match(wm_class='LibreWolf'),
        Match(wm_class='discord'),
    ]),

    Group('2', layouts=[
        Bsp(**TILING_CONFIG),
    ], matches=[
        Match(wm_class='Emacs'),
        Match(wm_class='Emacs-gtk+x11'),
    ]),

    Group('3', layouts=[
        MonadTall(ratio=0.6, **TILING_CONFIG),
        Bsp(**TILING_CONFIG),
        Max(**TILING_CONFIG),
    ], matches=[
        Match(wm_class='TelegramDesktop'),
        Match(wm_class='firefox-aurora'),
    ]),

    Group('4', layouts=[
        Bsp(**TILING_CONFIG),
    ], matches=[
        Match(wm_class='org.mozilla.thunderbird'),
        Match(wm_class='thunderbird'),
        Match(wm_class='thunderbird-default'),
    ]),

    Group('5', layouts=[
        Bsp(**TILING_CONFIG),
        MonadTall(ratio=0.5, **TILING_CONFIG),
    ], matches=[
        Match(title='Windowed Projector (Program)'),
    ]),
]
groups.extend(workspaces)

scratch = [
    ScratchPad('0', [
       DropDown(
           'kitty',
           'kitty',
           x=0.1,
           y=0.1,
           width=0.8,
           height=0.8,
           opacity=0.85,
       ),
       DropDown(
           'megasync',
           'flatpak run nz.mega.MEGAsync',
           x=0,
           y=0,
           width=0.1,
           height=0.1,
           opacity=1.0,
       ),
    ]),
]
groups.extend(scratch)


def get_box_widgets():
    yield DisplayLight(
        foreground='#ffffff',
        theme_path=PANEL_ICON_THEME,
        icon_ext='.svg',
        icon_size=16 * SCALE,
        icon_spacing=2 * SCALE,
        update_interval=15,
        backlight_name='intel_backlight',
        change_command='brightnessctl -d intel_backlight set {0}',
        step=20,
        default=200,
    )

    if shortcuts.is_x11():
        yield Power(
            foreground='#ffffff',
            theme_path=PANEL_ICON_THEME,
            icon_ext='.svg',
            icon_size=16 * SCALE,
            update_interval=60,
            callback=shortcuts.power_switch,
        )

    yield widget.ThermalSensor(
        tag_sensor='Package id 0',
        threshold=110,
    )

    yield Volume(
        name='volumemic',
        foreground='#ffffff',
        theme_path=PANEL_ICON_THEME,
        channel='@DEFAULT_SOURCE@',
        media_class='source',
        icon_ext='.svg',
        icon_size=16 * SCALE,
        update_interval=15,
        icon_names=(
            (0, 'microphone-sensitivity-muted-symbolic'),
            (33, 'microphone-sensitivity-low-symbolic'),
            (66, 'microphone-sensitivity-medium-symbolic'),
            (100, 'microphone-sensitivity-high-symbolic'),
        ),
    )


def get_bar_widgets():
    yield Workspaces(
        highlight_method='block',
        active='#ffffff',
        inactive='#aaaaaa',
        block_highlight_text_color='#ffffff',
        this_current_screen_border=ACCENT_COLOR_A,
        this_screen_border='#404040',
        other_current_screen_border=ACCENT_COLOR_B,
        other_screen_border='#404040',
        urgent_border=None,
        padding_x=8 * SCALE,
        padding_y=4 * SCALE,
        spacing=0 * SCALE,
        disable_drag=True,
        theme_path=PANEL_ICON_THEME,
        icon_ext='.svg',
        icon_size=16 * SCALE,
        icon_spacing=4 * SCALE,
        margin=12 * SCALE,
    )

    yield Dock(
        pinned_apps=(
            # 'rofi-launcher',
            'kitty',
            'org.gnome.Nautilus',
            'org.kde.dolphin',
            'io.gitlab.librewolf-community',
            'discord_local',
            'org.mozilla.Thunderbird',
            'emacs',
            'buttercup',
            'firefox-aurora',
            'com.slack.Slack',
            'org.telegram.desktop',
        ),
        padding=4 * SCALE,
        icon_size=32 * SCALE,
        fontsize=14 * SCALE,
        border=ACCENT_COLOR_A,
        other_border=ACCENT_COLOR_B,
        unfocused_border='#ffffff',
        spacing=8 * SCALE,
        theme_path=PANEL_ICON_THEME,
        theme_mode='fallback',
        margin=12 * SCALE,
    )

    yield Notification(
       highlight_method='line',
       fontsize=14 * SCALE,
       background='#ffffff',
       foreground='#000000',
       selected=ACCENT_COLOR_A,
       borderwidth=2 * SCALE,
       size=128 * SCALE,
       padding_x=8 * SCALE,
       padding_y=2 * SCALE,
       margin=12 * SCALE,
    )

    yield Entry(
       prompt='{prompt}',
       font='Ubuntu Mono',
       fontsize=16 * SCALE,
       background='#ffffff',
       foreground='#000000',
       cursor_color=ACCENT_COLOR_A,
       padding_x=16 * SCALE,
       padding_y=2 * SCALE,
       margin=12 * SCALE,
    )

    yield Box(
        widgets=list(get_box_widgets()),
        close_button_location='right',
        text_closed='',
        text_open='',
        foreground='#ffffff',
        theme_path=PANEL_ICON_THEME,
        icon_ext='.svg',
        icon_size=16 * SCALE,
    )

    if shortcuts.is_x11():
        yield IBUS(
            configured_keyboards=[
                'xkb:us::eng',
                'xkb:ru::rus',
                'anthy',
            ],
            display_map={
                'anthy': 'jap',
            },
            option='caps:none',
            fontsize=14 * SCALE,
            update_interval=15,
            background='#ffffff',
            foreground='#404040',
            padding_x=4 * SCALE,
            padding_y=4 * SCALE,
        )

    yield Volume(
        name='volume',
        foreground='#ffffff',
        theme_path=PANEL_ICON_THEME,
        icon_ext='.svg',
        icon_size=16 * SCALE,
        update_interval=15,
    )

    yield Bluetooth(
        foreground='#ffffff',
        theme_path=PANEL_ICON_THEME,
        icon_ext='.svg',
        icon_size=16 * SCALE,
        update_interval=15,
    )

    # yield NetworkManager(
    #     foreground='#ffffff',
    #     theme_path=PANEL_ICON_THEME,
    #     icon_ext='.svg',
    #     icon_size=16,
    #     update_interval=60,
    # )

    yield Battery(
        foreground='#ffffff',
        theme_path=PANEL_ICON_THEME,
        icon_ext='.svg',
        icon_size=16 * SCALE,
        icon_spacing=2 * SCALE,
        format='{percent:2.0%}',
        padding=12 * SCALE,
        update_interval=60 * 5,
    )

    yield widget.Clock(format="%d %b %H:%M")


screens = [
    Screen(
        top=bar.Bar(
            list(get_bar_widgets()),
            48 * SCALE,
            border_width=[0, 0, 0, 0],
            margin=0 * SCALE,
            background="#00000080",
        ),
    ),
    Screen(),
    # Screen(**WALLPAPER_CONFIG),
]
# if not shortcuts.is_x11():
#     screens.reverse()

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

    Key([MOD_SUPER], 'tab', lazy.function(shortcuts.next_screen), desc='Switch screens'),
    Key([MOD_SUPER, MOD_CONTROL], 'tab', lazy.next_layout(), desc='Switch layouts'),
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
    Key([], 'print', lazy.function(shortcuts.take_screenshot()),
        desc='Save a screenshot'),
    Key([MOD_ALT], 'print', lazy.function(shortcuts.take_screenshot(options=True)),
        desc='Save a screenshot with options'),
    Key([MOD_SHIFT, MOD_SUPER], 's', lazy.function(shortcuts.take_screenshot(options=True)),
        desc='Save a screenshot with options'),
]

# Sounds and Media
keys += [
    Key([], 'XF86AudioPlay', lazy.function(shortcuts.audio_play), desc='Play'),
    Key([], 'XF86AudioLowerVolume', lazy.widget['volume'].decrease_vol(), desc='Volume down'),
    Key([], 'XF86AudioMute', lazy.widget['volume'].mute(), desc='Volume mute'),
    Key([], 'XF86AudioRaiseVolume', lazy.widget['volume'].increase_vol(), desc='Volume up'),
    Key([], 'XF86AudioMicMute', lazy.function(shortcuts.audio_toggle), desc='Mic mute'),
]

# System
keys += [
    # Key([MOD_SUPER], 'l', lazy.spawn('xsecurelock -- systemctl suspend'),
    #     desc='Lock screen and Suspend'),
    Key([MOD_SUPER], 'l', lazy.spawn('systemctl suspend'),
        desc='Lock screen and Suspend'),
    # Key([MOD_CONTROL, MOD_ALT], 'delete', lazy.spawn('systemctl poweroff'),
    #     desc='Power Off'),
    # Key([MOD_SUPER], 'q', lazy.spawn('rofi -show drun'), desc='Show all applications'),
    Key([MOD_SUPER], 'a',
        lazy.function(shortcuts.spawn(f'rofi -show drun -dpi {DPI}')),
        desc='Show all applications'),
    Key([MOD_CONTROL], 'escape',
        lazy.function(shortcuts.spawn(f'rofi -show drun -dpi {DPI}')),
        desc='Show all applications'),
    Key([MOD_SUPER], 'v', lazy.widget['box'].toggle(), desc='Show the widgets'),
    Key([MOD_SUPER], 'm', lazy.hide_show_bar(position='top'), desc='Show the bar'),
    Key([MOD_SUPER], 's',
        lazy.function(shortcuts.spawn(f'rofi -show window -dpi {DPI}')),
        desc='Show the window list'),
    # Key([MOD_ALT], 'F2', lazy.spawncmd(prompt='> ', widget='entry', complete='entry'),
    #     desc='Show the run command prompt'),
    # Key([MOD_SUPER], 'r', lazy.spawncmd(prompt='> ', widget='entry', complete='entry'),
    #     desc='Show the run command prompt'),
    Key([MOD_ALT], 'F2', lazy.function(shortcuts.spawn('qdbus org.kde.krunner /App querySingleRunner apps ')),
        desc='Show the run command prompt'),
    Key([MOD_SUPER], 'r', lazy.function(shortcuts.spawn('qdbus org.kde.krunner /App querySingleRunner apps ')),
        desc='Show the run command prompt'),

    Key([MOD_CONTROL, MOD_ALT], 'backspace', lazy.shutdown(), desc='Log out'),
    Key([], 'XF86MonBrightnessUp', lazy.widget['displaylight'].change_backlight(ChangeDirection.UP)),
    Key([], 'XF86MonBrightnessDown', lazy.widget['displaylight'].change_backlight(ChangeDirection.DOWN)),
    Key([], 'XF86Bluetooth', lazy.widget['bluetooth'].block(), desc='Toggle Bluetooth'),
    Key([], 'XF86TouchpadToggle', lazy.function(shortcuts.input_update)),
    Key([MOD_SUPER], 'p', lazy.function(shortcuts.display_double), 'Display toggle'),
    # Key([], 'XF86RotateWindows', lazy.function(display_single), desc='Rotate button'),
]

if shortcuts.is_x11():
    keys += [
        Key([], 'XF86Reload', lazy.widget['power'].switch(), desc='Target button'),
    ]

# Typing
if shortcuts.is_x11():
    keys += [
        Key([MOD_CONTROL], 'space', lazy.widget['ibus'].next_keyboard(),
            desc='Switch to next input source'),
        Key([MOD_CONTROL, MOD_SHIFT], 'space', lazy.widget['ibus'].prev_keyboard(),
            desc='Switch to previous input source'),
        Key([MOD_SUPER], 'space', lazy.widget['ibus'].toggle_keyboard(),
            desc='Toggle between last input sources'),
    ]

# Windows
keys += [
    Key([MOD_ALT], 'F4', lazy.window.kill(), desc='Close window'),
    Key([MOD_SUPER], 'H', lazy.window.toggle_minimize(), desc='Toggle minimization state'),
    Key([MOD_ALT], 'F7', lazy.window.move_to_bottom(), desc='Move window to bottom'),
    Key([MOD_ALT], 'F8', lazy.window.move_to_top(), desc='Move window to top'),
    Key([MOD_ALT], 'F9', lazy.window.toggle_minimize(), desc='Toggle minimization state'),
    Key([MOD_ALT], 'F10', lazy.window.toggle_maximize(), desc='Toggle maximization state'),
    Key([MOD_ALT], 'F11', lazy.window.toggle_fullscreen(), desc='Toggle fullscreen state'),
]

keys += [
    Key([], 'XF86Tools', lazy.function(shortcuts.launch_settings),
        desc='Open System Monitor'),
    Key([MOD_CONTROL, MOD_SHIFT], 'escape', lazy.function(shortcuts.spawn('gnome-system-monitor')),
        desc='Open System Monitor'),
    Key([MOD_SUPER], 'f', lazy.window.toggle_floating(), desc='Toggle floating'),
    Key([MOD_CONTROL, MOD_SUPER], 'r', lazy.reload_config(), desc='Reload configuration'),
    Key([MOD_CONTROL, MOD_SUPER], 'F5', lazy.reload_config(), desc='Reload configuration'),
    Key([MOD_SUPER], 'return', lazy.group['0'].dropdown_toggle('kitty')),
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
    if shortcuts.is_x11():
        shortcuts.display_double(qtile)

    os.putenv('GTK_IM_MODULE', 'ibus')
    os.putenv('QT_IM_MODULE', 'ibus')
    os.putenv('XMODIFIERS', '@im=ibus')

    if shortcuts.is_x11():
        profile = subprocess.check_output(['powerprofilesctl', 'get']).decode().strip('\n')
        if profile == 'balanced':
            # subprocess.Popen(['picom'], start_new_session=True)
            shortcuts.spawn('picom')()

    subprocess.call([
        'ibus-daemon',
        '-dxrR',
        '-p', '/usr/lib64/gtk-4.0/4.0.0/immodules/libim-ibus.so',
    ])

    portals_start(is_x11=shortcuts.is_x11())


@hook.subscribe.startup
def startup():
    if shortcuts.is_x11():
        xrdb_merge(**{
            'Xcursor.size': CURSOR_SIZE,
            'Xcursor.theme': CURSOR_THEME,
            'Xft.antialias': 1,
            'Xft.dpi': DPI,
            'Xft.hinting': 0,
            'Xft.hintstyle': 'hintnone',
            'Xft.lcdfilter': 'lcddefault',
            'Xft.rgba': 'rgb',
        })
        subprocess.call(['xsetroot', '-cursor_name', 'left_ptr'])  # default cursor

    set_gtk_settings(**{
        'gtk-theme-name': GTK_THEME,
        'gtk-icon-theme-name': ICON_THEME,
        'gtk-cursor-theme-name': CURSOR_THEME,
        'gtk-cursor-theme-size': CURSOR_SIZE,
    })

    os.putenv('GTK_CSD', '1')
    os.putenv('ICON_THEME', ICON_THEME)
    os.putenv('LANG', 'en_GB.UTF-8')
    os.putenv('MOZ_GTK_TITLEBAR_DECORATION', 'client')
    os.putenv('MOZ_USE_XINPUT2', '1')
    os.putenv('QT_STYLE_OVERRIDE', QT_THEME)
    os.putenv('VK_DRIVER_FILES', '/usr/share/vulkan/icd.d/nvidia_icd.json')
    os.putenv('XSECURELOCK_AUTH_BACKGROUND_COLOR', '#202020')
    os.putenv('XSECURELOCK_BACKGROUND_COLOR', '#101010')
    os.putenv('XSECURELOCK_PASSWORD_PROMPT', 'asterisks')

    shortcuts.input_update(qtile)

    # subprocess.Popen(['krunner'], start_new_session=True)

    qtile.ss_inhibit = 0
    qtile.pm_inhibit = 0


@hook.subscribe.shutdown
def shutdown():
    portals_stop(is_x11=shortcuts.is_x11())
    subprocess.call(['pkill', 'picom'])
    # subprocess.call(['pkill', 'krunner'])
    uninhibit_dbus()


@hook.subscribe.screens_reconfigured
def screens_reconfigured():
    shortcuts.remap_screens(qtile)


hook.subscribe.float_change(float_change_dbus)
