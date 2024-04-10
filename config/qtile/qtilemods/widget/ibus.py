import subprocess
import time

from subprocess import CalledProcessError, check_output

from libqtile import widget
from libqtile.widget import base
from libqtile.widget.keyboardlayout import _BaseLayoutBackend
from libqtile.command.base import expose_command
from libqtile.log_utils import logger


class IBUSBackend(_BaseLayoutBackend):
    transitional_keyboard = 'xkb:us::eng'

    def get_keyboard(self) -> str:
        command = ['ibus', 'engine']
        try:
            output = check_output(command).decode()
        except CalledProcessError:
            pass
        except OSError:
            logger.exception('Please, check that ibus is available:')
        else:
            return output.strip('\n')
        return 'unknown'

    def set_keyboard(self, layout, options):
        if layout != self.transitional_keyboard:
            self.set_keyboard(self.transitional_keyboard, options)

        command = ['ibus', 'engine', layout]
        try:
            check_output(command)
        except CalledProcessError:
            pass
        except OSError:
            logger.error('Please, check that ibus is available:')

        prefix, *var = layout.split(':')
        if prefix == 'xkb':
            layouts = [var[0]]
            if 'us' not in layouts:
                layouts.append('us')
            command = ['setxkbmap', '-layout', ','.join(layouts)]
            if options:
                command += ['-option', options]
            try:
                check_output(command)
            except CalledProcessError:
                pass
            except OSError:
                logger.error('Please, check that setxkbmap is available:')


class IBUS(base.PaddingMixin, base.MarginMixin, widget.KeyboardLayout):
    def __init__(self, **config):
        base.InLoopPollText.__init__(self, **config)
        self.add_defaults(widget.KeyboardLayout.defaults)
        self.add_defaults(base.PaddingMixin.defaults)
        self.add_defaults(base.MarginMixin.defaults)
        self.add_callbacks({'Button1': self.next_keyboard})
        self.add_callbacks({'Button2': self._ibus_setup})
        self.add_callbacks({'Button3': self._ibus_setup})

        self.background = config.get('background', '#000000')
        self.rounded = config.get('rounded', True)

    def _ibus_setup(self):
        subprocess.Popen(['ibus-setup'], start_new_session=True)

    def _configure(self, qtile, bar):
        base.InLoopPollText._configure(self, qtile, bar)

        self.layout = self.drawer.textlayout(
            '', self.foreground, self.font, self.fontsize, self.fontshadow)

        self.prev_keyboard = self.configured_keyboards[0]
        self.prev_keyboard_time = time.time()

        self.backend = IBUSBackend(qtile)
        self.backend.set_keyboard(self.configured_keyboards[0], self.option)

    @expose_command()
    def next_keyboard(self):
        t = time.time()
        if t - self.prev_keyboard_time > 3:
            self.prev_keyboard = self.backend.get_keyboard()
            self.prev_keyboard_time = t
        super().next_keyboard()

    @expose_command()
    def toggle_keyboard(self):
        next_keyboard = self.prev_keyboard
        prev_keyboard = self.backend.get_keyboard()

        if prev_keyboard == next_keyboard:
            self.next_keyboard()
        else:
            self.prev_keyboard = prev_keyboard
            self.prev_keyboard_time = time.time()
            self.backend.set_keyboard(next_keyboard, self.option)
            self.tick()

    def poll(self):
        keyboard = self.backend.get_keyboard()
        if keyboard in self.display_map.keys():
            return self.display_map[keyboard]
        return keyboard.split(':')[-1]

    def box_width(self):
        width, _ = self.drawer.max_layout_size([
            # self.fmt.format(self.text)
            self.fmt.format('WWW')
        ], self.font, self.fontsize)
        return width + self.padding_x * 2

    def calculate_length(self):
        return self.box_width() + self.margin_x * 2

    def drawbox(self, offset, text, bordercolor, textcolor, width=None, rounded=False):
        self.layout.text = self.fmt.format(text)
        self.layout.font_family = self.font
        self.layout.font_size = self.fontsize
        self.layout.colour = textcolor
        if width is not None:
            self.layout.width = width

        framed = self.layout.framed(0, bordercolor, 0, self.padding_y, textcolor)
        y = (self.bar.height - framed.height) // 2
        framed.draw_fill(offset, y, rounded)

    def draw(self):
        self.drawer.clear(self.bar.background)

        bw = self.box_width()
        self.drawbox(
            self.margin_x,
            self.text,
            self.background,
            self.foreground,
            width=bw,
            rounded=self.rounded,
        )
        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.width)
