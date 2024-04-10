import os

from xdg import DesktopEntry


def get_desktop_entry_path(appname):
    if os.path.isabs(appname):
        return DesktopEntry(appname)

    dirs = (
        os.path.expanduser('~/.local/share/applications'),
        '/usr/local/share/applications',
        '/usr/share/applications',
        '/var/lib/flatpak/exports/share/applications/',
    )

    # check if it has an extension and strip it
    if os.path.splitext(appname)[1][1:] in ('.desktop',):
        appname = os.path.splitext(appname)[0]

    for d in dirs:
        if not os.path.isdir(d):
            continue

        for f in os.listdir(d):
            filepath = os.path.join(d, f)
            if not os.path.isfile(filepath):
                continue

            if f != f'{appname}.desktop':
                continue

            return DesktopEntry(filepath)
