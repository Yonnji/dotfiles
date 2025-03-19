from qtilemods.tools import shortcuts
from qtilemods.widget.dock import PinnedApp


emacs = PinnedApp(
    desktop={
        'Desktop Entry': {
            'Name': 'Emacs',
            'Icon': '/usr/share/icons/hicolor/128x128/apps/emacs.png',
            'Exec': 'emacs-gtk+x11' if shortcuts.is_x11() else 'emacs',
            'StartupWMClass': 'Emacs-gtk+x11' if shortcuts.is_x11() else 'emacs',
        },
    },
    name='Emacs',
)


thunderbird = PinnedApp(
    desktop={
        'Desktop Entry': {
            'Name': 'Thunderbird',
            'Icon': '/var/lib/flatpak/exports/share/icons/hicolor/256x256/apps/org.mozilla.Thunderbird.png',
            'Exec': (
                '/usr/bin/flatpak run --branch=stable --arch=x86_64 '
                '--command=thunderbird '
                '--file-forwarding org.mozilla.Thunderbird'
            ),
            'StartupWMClass': 'net.thunderbird.Thunderbird',
        },
    },
    name='Thunderbird',
)


chromium = PinnedApp(
    desktop={
        'Desktop Entry': {
            'Name': 'Chromium',
            'Icon': '/var/lib/flatpak/exports/share/icons/hicolor/256x256/apps/org.chromium.Chromium.png',
            'Exec': (
                '/usr/bin/flatpak run --branch=stable --arch=x86_64 '
                '--command=/app/bin/chromium org.chromium.Chromium '
                '--disable-web-security '
                '--user-data-dir=/tmp/org.chromium.Chromium'
            ),
            'StartupWMClass': 'Org.chromium.Chromium',
        },
    },
    name='Chromium',
)


buttercup = PinnedApp(
    desktop={
        'Desktop Entry': {
            'Name': 'Buttercup',
            'Icon': '/var/home/yonnji/Apps/Buttercup/buttercup.png',
            'Exec': '/var/home/yonnji/Apps/Buttercup/Buttercup-linux-x86_64.AppImage' + (
                '' if shortcuts.is_x11() else ' --enable-features=UseOzonePlatform --ozone-platform=wayland'
            ),
            'StartupWMClass': 'Buttercup',
        },
    },
    name='Buttercup',
)
