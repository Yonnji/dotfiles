import os

from xdg import IconTheme


def get_icon_path(iconname, size=None, theme=None, extensions=('png', 'svg', 'xpm')):
    if os.path.isabs(iconname):
        return iconname

    themes = IconTheme.__get_themes(theme)

    # check if it has an extension and strip it
    if os.path.splitext(iconname)[1][1:] in extensions:
        iconname = os.path.splitext(iconname)[0]

    for thme in themes:
        icon = IconTheme.LookupIcon(iconname, size, thme, extensions)
        if icon:
            return icon
