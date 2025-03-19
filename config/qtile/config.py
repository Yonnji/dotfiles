"""Qtile configuration."""
import copy
import os
import subprocess
import sys

from libqtile import bar, widget, hook, qtile
from libqtile.config import (
    Drag, DropDown, Group, Key, Match, Screen, ScratchPad)
from libqtile.lazy import lazy
from libqtile.log_utils import logger

sys.path.append(os.path.dirname(__file__))

from qtilemods import apps
from qtilemods.layout.floating import Floating
from qtilemods.layout.tiling import Bsp, Max, MonadTall
from qtilemods.tools.gtk import set_gtk_settings
from qtilemods.tools.portal import portals_start, portals_stop
from qtilemods.tools.xrdb import xrdb_merge
from qtilemods.tools import inhibit, shortcuts
from qtilemods.widget.battery import Battery
from qtilemods.widget.bluetooth import Bluetooth
from qtilemods.widget.box import Box
from qtilemods.widget.displaylight import DisplayLight, ChangeDirection
from qtilemods.widget.dock import Dock, PinnedApp
from qtilemods.widget.entry import Entry
from qtilemods.widget.keyboard_layout import KeyboardLayout
from qtilemods.widget.notification import Notification
from qtilemods.widget.volume import Volume
from qtilemods.widget.power import Power
from qtilemods.widget.network_manager import NetworkManager
from qtilemods.widget.workspaces import Workspaces

AUDIO_BACKEND = 'pulse' if os.path.exists('/usr/bin/pulseaudio') else 'pw'
# AUDIO_BACKEND = 'pulse'

HOME = os.getenv('HOME')
SCALE = 1
BASE_DPI = 96
DPI = BASE_DPI * SCALE
IM = 'fcitx'
GTK_THEME = 'Colloid-Pink-Light'
# GTK_THEME = 'Adwaita'
QT_THEME = 'kvantum'
ICON_THEME = 'Papirus-Light'
PANEL_ICON_THEME = 'Papirus-Dark'
CURSOR_THEME = 'Breeze_Hacked'
CURSOR_SIZE = 36 * SCALE
ACCENT_COLOR_A = '#E91E63'
ACCENT_COLOR_B = '#2196F3'
FLOATING_CONFIG = {
    'border_focus': '#ff00aa',
    'border_normal': '#888888',
    'border_width': 2 * SCALE,
    'no_reposition_rules': [
        Match(wm_class='Waveform'),
    ]
}
TILING_CONFIG = {
    'border_focus': '#00ffff',
    'border_normal': '#888888',
    'border_width': 2 * SCALE,
    'border_on_single': True,
    'margin': 4 * SCALE,
}

ROFI_ICON_LIST_THEME = '''
listview {
    columns: 1;
}
element {
    padding: 0.75em;
}
element-icon {
    size: 1em;
}
element-text {
    padding: 0 0.25em;
}
'''.replace('\n', '')
logger.error(ROFI_ICON_LIST_THEME)

ROFI_TEXT_LIST_THEME = '''
listview {
    columns: 1;
}
element {
    padding: 0.75em;
}
element-icon {
    size: 0;
}
element-text {
    padding: 0;
}
'''.replace('\n', '')
logger.error(ROFI_TEXT_LIST_THEME)

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

    tiling_rules=[Match(wm_class=wm_class) for wm_class in (
        'Blender',
        'Buttercup',
        'Gimp-2.10',
        'LibreWolf',
        'MongoDB Compass',
        'NVIDIA Nsight Graphics',
        'Quodlibet', 'io.github.quodlibet.QuodLibet',
        'REAPER',
        'Studio 3T',
        'Substance Designer',
        'TelegramDesktop',
        'Unity',
        'baobab',
        'com.github.tchx84.Flatseal',
        'discord',
        'electrum', 'electrum-ltc',
        'emacs', 'Emacs', 'Emacs-gtk+x11',
        'firefox-aurora',
        'game-jolt-client',
        'insomnia',
        'itch',
        'kdenlive',
        'kitty',
        'krita',
        'libreoffice',
        'maya.bin',
        'obs',
        'openshot',
        'org.chromium.Chromium', 'Org.chromium.Chromium',
        'org.gnome.Nautilus',
        'org.inkscape.Inkscape',
        'pstats',
        'steam',
        'thunderbird', 'thunderbird-default', 'net.thunderbird.Thunderbird', 'org.mozilla.thunderbird',
        'tiled',
        'transmission-gtk',
    )],

    **FLOATING_CONFIG
)

workspaces = [
    Group('1', layouts=[
        MonadTall(ratio=0.5, **TILING_CONFIG),
        Max(**TILING_CONFIG),
    ], matches=[
        Match(wm_class='Buttercup'),
        Match(wm_class='LibreWolf'),
    ]),

    Group('2', layouts=[
        Bsp(**TILING_CONFIG),
        Max(**TILING_CONFIG),
    ], matches=[
        Match(wm_class='emacs'),
        Match(wm_class='Emacs'),
        Match(wm_class='Emacs-gtk+x11'),
    ]),

    Group('3', layouts=[
        MonadTall(ratio=0.6, **TILING_CONFIG),
        Max(**TILING_CONFIG),
    ], matches=[
        Match(wm_class='TelegramDesktop'),
        Match(wm_class='firefox-aurora'),
    ]),

    Group('4', layouts=[
        Bsp(**TILING_CONFIG),
        Max(**TILING_CONFIG),
    ], matches=[
        Match(wm_class='net.thunderbird.Thunderbird'),
        Match(wm_class='org.mozilla.thunderbird'),
        Match(wm_class='thunderbird'),
        Match(wm_class='thunderbird-default'),
    ]),

    Group('5', layouts=[
        MonadTall(ratio=0.5, **TILING_CONFIG),
        Max(**TILING_CONFIG),
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
    ]),
]
groups.extend(scratch)


def get_env():
    return {
        # 'GTK_CSD': '1',  # FF tab's previews stuck on every desktop
        # 'GDK_SCALE': str(SCALE),
        # 'MOZ_GTK_TITLEBAR_DECORATION': 'client',
        'GTK_IM_MODULE': IM,
        'ICON_THEME': ICON_THEME,
        'LANG': 'en_GB.UTF-8',
        'MOZ_USE_XINPUT2': '1',
        'QT_IM_MODULE': IM,
        'QT_STYLE_OVERRIDE': QT_THEME,
        'SSH_ASKPASS': '~/.local/bin/askpass',
        'SSH_ASKPASS_REQUIRE': 'force',
        'SSH_AUTH_SOCK': os.path.join(os.getenv('XDG_RUNTIME_DIR'), 'gcr/ssh'),
        'XMODIFIERS': f'@im={IM}',
    }


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

    # if shortcuts.is_x11():
    if True:
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
        icon_ext='.svg',
        icon_size=16 * SCALE,
        update_interval=15,
        volume_app=f"{HOME}/.local/bin/rofi-{AUDIO_BACKEND} -dpi {DPI} -theme-str '{ROFI_TEXT_LIST_THEME}' -M source",
        channel='Capture',
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
            PinnedApp(
                desktop={
                    'Desktop Entry': {
                        'Name': 'Rofi',
                        'Icon': '/usr/share/pixmaps/system-logo-white.png',
                    },
                },
                name='rofi-launcher',
                cmd=f'rofi -show drun -dpi {DPI}',
            ),
            'kitty',
            'org.gnome.Nautilus',
            'org.kde.dolphin',
            'io.gitlab.librewolf-community',
            'discord_local',
            apps.thunderbird,
            apps.emacs,
            apps.buttercup,
            'firefox-aurora',
            apps.chromium,
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
        env=get_env(),
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

    yield KeyboardLayout(
        backend=IM,
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
        # device='sysdefault:CARD=sofhdadsp',
        volume_app=f"{HOME}/.local/bin/rofi-{AUDIO_BACKEND} -dpi {DPI} -theme-str '{ROFI_TEXT_LIST_THEME}'",
    )

    yield Bluetooth(
        foreground='#ffffff',
        theme_path=PANEL_ICON_THEME,
        icon_ext='.svg',
        icon_size=16 * SCALE,
        update_interval=15,
    )

    yield NetworkManager(
        foreground='#ffffff',
        icon_ext='.svg',
        icon_size=16 * SCALE,
        spacing=16 * SCALE,
        theme_path=PANEL_ICON_THEME,
        update_interval=60,
        margin=8 * SCALE,
        network_app=f"{HOME}/.local/bin/rofi-nm -dpi {DPI} -theme-str '{ROFI_TEXT_LIST_THEME}'",
    )

    yield Battery(
        foreground='#ffffff',
        theme_path=PANEL_ICON_THEME,
        icon_ext='.svg',
        icon_size=16 * SCALE,
        icon_spacing=2 * SCALE,
        format='{percent:2.0%}',
        padding=8 * SCALE,
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
    Key([MOD_CONTROL], 'XF86AudioMute', lazy.widget['volume'].run_app(), desc='Volume app'),
    Key([], 'XF86AudioRaiseVolume', lazy.widget['volume'].increase_vol(), desc='Volume up'),
    Key([], 'XF86AudioMicMute', lazy.function(shortcuts.audio_toggle), desc='Mic mute'),
    Key([MOD_CONTROL], 'XF86AudioMicMute', lazy.widget['volumemic'].run_app(), desc='Mic app'),
]

# System
keys += [
    Key([MOD_SUPER], 'l', lazy.function(shortcuts.lock_screen()),
        desc='Lock screen'),
    Key([MOD_SUPER], 'u', lazy.function(shortcuts.lock_screen(suspend=True)),
        desc='Lock screen and Suspend'),
    # Key([MOD_CONTROL, MOD_ALT], 'delete', lazy.spawn('systemctl poweroff'),
    #     desc='Power Off'),
    # Key([MOD_SUPER], 'q', lazy.spawn('rofi -show drun'), desc='Show all applications'),
    Key([MOD_SUPER], 'a',
        lazy.function(shortcuts.spawn(f'rofi -show drun -dpi {DPI}', **get_env())),
        desc='Show all applications'),
    Key([MOD_CONTROL], 'escape',
        lazy.function(shortcuts.spawn(f'rofi -show drun -dpi {DPI}', **get_env())),
        desc='Show all applications'),
    Key([MOD_SUPER], 'v', lazy.widget['box'].toggle(), desc='Show the widgets'),
    Key([MOD_SUPER], 'm', lazy.hide_show_bar(position='top'), desc='Show the bar'),
    Key([MOD_SUPER], 's',
        lazy.function(shortcuts.spawn(f"rofi -show window -dpi {DPI} -theme-str '{ROFI_ICON_LIST_THEME}'")),
        desc='Show the window list'),
    Key([MOD_ALT], 'F2', lazy.spawncmd(prompt='> ', widget='entry', complete='entry'),
        desc='Show the run command prompt'),
    Key([MOD_SUPER], 'r', lazy.spawncmd(prompt='> ', widget='entry', complete='entry'),
        desc='Show the run command prompt'),

    Key([MOD_CONTROL, MOD_ALT], 'backspace', lazy.shutdown(), desc='Log out'),
    Key([], 'XF86MonBrightnessUp', lazy.widget['displaylight'].change_backlight(ChangeDirection.UP)),
    Key([], 'XF86MonBrightnessDown', lazy.widget['displaylight'].change_backlight(ChangeDirection.DOWN)),
    Key([], 'XF86Bluetooth', lazy.widget['bluetooth'].block(), desc='Toggle Bluetooth'),
    # Key([], 'XF86TouchpadToggle', lazy.function(shortcuts.input_update)),
    Key([MOD_SUPER], 'p', lazy.function(shortcuts.display_double), 'Display toggle'),
    Key([], 'XF86RotateWindows', lazy.function(shortcuts.display_single), desc='Rotate button'),
]

if shortcuts.is_x11():
    keys += [
        Key([], 'XF86Reload', lazy.widget['power'].switch(), desc='Target button'),
    ]

# Typing
# if shortcuts.is_x11():
if True:
    keys += [
        Key([MOD_CONTROL], 'space', lazy.widget['keyboardlayout'].next_keyboard(),
            desc='Switch to next input source'),
        Key([MOD_CONTROL, MOD_SHIFT], 'space', lazy.widget['keyboardlayout'].prev_keyboard(),
            desc='Switch to previous input source'),
        Key([MOD_SUPER], 'space', lazy.widget['keyboardlayout'].toggle_keyboard(),
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
    Key([], 'XF86Tools',
        lazy.function(shortcuts.spawn(
            'gnome-control-center',
            XDG_SESSION_DESKTOP='gnome',
            XDG_CURRENT_DESKTOP='gnome',
            **get_env()
        )),
        desc='Open System Monitor'),
    Key([MOD_CONTROL, MOD_SHIFT], 'escape',
        lazy.function(shortcuts.spawn('gnome-system-monitor', **get_env())),
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

    subprocess.call(['rfkill', 'block', 'wlan'])
    if IM == 'ibus':
        subprocess.call([
            'ibus-daemon',
            '-dxrR',
            '-p', '/usr/lib64/gtk-4.0/4.0.0/immodules/libim-ibus.so',
        ])
    else:
        subprocess.call(['fcitx5', '-d'])
    portals_start(is_x11=shortcuts.is_x11())


@hook.subscribe.startup
def startup():
    xrdb_merge(**{
        'Xcursor.size': CURSOR_SIZE,
        'Xcursor.theme': CURSOR_THEME,
        'Xft.antialias': 1,
        'Xft.hinting': 0,
        'Xft.hintstyle': 'hintnone',
        'Xft.lcdfilter': 'lcddefault',
        'Xft.rgba': 'rgb',
        'Xft.dpi': DPI,
    })

    if shortcuts.is_x11():
        subprocess.call(['xsetroot', '-cursor_name', 'left_ptr'])  # default cursor
        subprocess.call(['xrandr', '--dpi', str(DPI)])

    set_gtk_settings(**{
        'gtk-cursor-theme-name': CURSOR_THEME,
        'gtk-cursor-theme-size': CURSOR_SIZE,
        # 'gtk-font-name': 'Noto Sans, {:.0f}'.format(10 / SCALE),
        'gtk-font-name': 'Noto Sans, {:.0f}'.format(10),
        'gtk-icon-theme-name': ICON_THEME,
        'gtk-theme-name': GTK_THEME,
    })

    for k, v in get_env().items():
        os.putenv(k, v)

    shortcuts.input_update(qtile, scale=SCALE)

    qtile.ss_inhibit = 0
    qtile.pm_inhibit = 0


@hook.subscribe.shutdown
def shutdown():
    portals_stop(is_x11=shortcuts.is_x11())
    if IM == 'ibus':
        subprocess.call(['pkill', 'ibus-daemon'])
    else:
        subprocess.call(['pkill', 'fcitx5'])
    subprocess.call(['pkill', 'picom'])
    inhibit.uninhibit_dbus()


@hook.subscribe.screens_reconfigured
def screens_reconfigured():
    shortcuts.remap_screens(qtile)


# hook.subscribe.float_change(inhibit.float_change_dbus)
hook.subscribe.float_change(inhibit.float_change_xset)
