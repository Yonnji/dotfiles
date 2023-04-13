import glob
import re
import os

from subprocess import CalledProcessError, check_output

from libqtile import widget, utils
from libqtile.widget import base
from libqtile.widget.prompt import CommandCompleter
from libqtile.log_utils import logger

from .mixins import AppMixin


class EntryCompleter(AppMixin, CommandCompleter):
    def _lookup_fullpath(self, txt):
        lookup = []

        path = os.path.expanduser(txt)
        if os.path.isdir(path):
            files = glob.glob(os.path.join(path, '*'))
            prefix = txt
        else:
            files = glob.glob(path + '*')
            prefix = os.path.dirname(txt)
        prefix = prefix.rstrip('/') or '/'
        for f in files:
            if self.executable(f):
                display = os.path.join(prefix, os.path.basename(f))
                if os.path.isdir(f):
                    display += '/'
                lookup.append((display, f))

        return lookup

    def _lookup_flatpaks(self, txt):
        lookup = []

        for appid, desktop in self.get_flatpaks():
            if 'Desktop Entry' not in desktop:
                continue

            name = desktop['Desktop Entry']['Name']
            if name.lower().startswith(txt):
                lookup.append((f'flatpak run {appid}', name))

        return lookup

    def _lookup_desktop_files(self, txt):
        lookup = []

        for filename, desktop in self.get_desktop_files():
            if 'Desktop Entry' not in desktop:
                continue

            name = desktop['Desktop Entry']['Name']
            executable = ''
            executable_name = ''
            if 'Exec' in desktop['Desktop Entry']:
                executable = re.sub(r'%[A-Za-z]', '', desktop['Desktop Entry']['Exec'])
                executable_name = os.path.basename(executable)

            if name.lower().startswith(txt):
                lookup.append((executable, name))
            elif executable_name.startswith(txt):
                lookup.append((executable, executable_name))

        return lookup

    def _lookup_env_path(self, txt):
        lookup = []

        dirs = os.environ.get('PATH', self.DEFAULTPATH).split(':')
        for d in dirs:
            try:
                d = os.path.expanduser(d)
                for cmd in glob.iglob(os.path.join(d, '%s*' % txt)):
                    if self.executable(cmd):
                        lookup.append((os.path.basename(cmd), cmd))
            except OSError:
                pass

        return lookup

    def complete(self, txt):
        if self.lookup is None:
            self.lookup = []

            if txt and txt[0] in '~/':
                # self.lookup += self._lookup_fullpath(txt)
                pass
            else:
                self.lookup += self._lookup_flatpaks(txt)
                self.lookup += self._lookup_desktop_files(txt)
                # self.lookup += self._lookup_env_path(txt)

            self.lookup.sort()
            self.offset = -1
            self.lookup.append((txt, txt))

        self.offset += 1
        if self.offset >= len(self.lookup):
            self.offset = 0

        ret = self.lookup[self.offset]
        self.thisfinal = ret[1]
        return ret[0]


class Entry(base.PaddingMixin, base.MarginMixin, widget.Prompt):
    def __init__(self, **config):
        self.completers['entry'] = EntryCompleter
        super().__init__(**config)
        self.add_defaults(base.PaddingMixin.defaults)
        self.add_defaults(base.MarginMixin.defaults)
        self.rounded = config.get('rounded', True)

    def _highlight_text(self, text) -> str:
        colors = list(map(utils.hex, (self.background, self.cursor_color)))
        if self.show_cursor:
            colors.reverse()

        return f'''<span background="{colors[0]}" foreground="{colors[1]}">{text}</span>'''

    def calculate_length(self):
        length = super().calculate_length()
        if length:
            length += self.margin * 2 + self.padding * 2
        return length

    def drawbox(self, offset, text, bordercolor, textcolor, width=None, rounded=False):
        if not self.text:
            return

        self.layout.text = self.fmt.format(text)
        self.layout.font_family = self.font
        self.layout.font_size = self.fontsize
        self.layout.colour = textcolor
        if width is not None:
            self.layout.width = width

        framed = self.layout.framed(0, bordercolor, self.padding_x, self.padding_y, textcolor)
        y = (self.bar.height - framed.height) // 2
        framed.draw_fill(offset, y, rounded)

    def draw(self):
        self.drawer.clear(self.bar.background)
        self.drawbox(
            self.margin_x,
            self.text,
            self.background,
            self.foreground,
            rounded=self.rounded,
        )
        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.width)
