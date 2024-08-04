import os
import shlex
from functools import partial

from libqtile import widget
from libqtile.widget import base
from libqtile.widget.backlight import BACKLIGHT_DIR, ChangeDirection
from libqtile.command.base import expose_command

from .mixins import IconTextMixin


class DisplayLight(IconTextMixin, base.PaddingMixin, widget.Backlight):
    backlight_dir = BACKLIGHT_DIR
    icon_names = (
        'display-brightness-symbolic',
    )

    def __init__(self, **config):
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.images = {}
        self.current_icon = self.icon_names[0]
        if not config.get('backlight_name'):
            names = os.listdir(self.backlight_dir)
            if names:
                config['backlight_name'] = names[0]

        base.InLoopPollText.__init__(self, **config)
        self.add_defaults(widget.Backlight.defaults)
        self._future = None

        self.brightness_file = os.path.join(
            self.backlight_dir,
            self.backlight_name,
            self.brightness_file,
        )
        self.max_brightness_file = os.path.join(
            self.backlight_dir,
            self.backlight_name,
            self.max_brightness_file,
        )

        self.add_defaults(base.PaddingMixin.defaults)

        self.add_callbacks({
            'Button4': partial(self.change_backlight, ChangeDirection.UP),
            'Button5': partial(self.change_backlight, ChangeDirection.DOWN),
        })

        default = config.get('default')
        if default:
            self._change_backlight(default)

    def calculate_length(self):
        return (
            super().calculate_length() +
            self.icon_size + self.icon_spacing)

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        self.setup_images()

    def _get_info(self):
        brightness = self._load_file(self.brightness_file)
        max_value = self._load_file(self.max_brightness_file)
        return brightness, max_value

    def poll(self):
        try:
            value, max_value = self._get_info()
        except RuntimeError as e:
            return "Error: {}".format(e)

        return self.format.format(percent=value / max_value)

    def _change_backlight(self, value):
        if self.change_command is None:
            try:
                with open(self.brightness_file, "w") as f:
                    f.write(str(round(value)))
            except PermissionError:
                logger.warning(
                    "Cannot set brightness: no write permission for %s", self.brightness_file
                )
        else:
            self.call_process(shlex.split(self.change_command.format(value)))
        self.update(self.poll())

    @expose_command()
    def change_backlight(self, direction, step=None):
        if not step:
            step = self.step
        if self._future and not self._future.done():
            return
        now, max_value = self._get_info()
        new = now
        if direction is ChangeDirection.DOWN:
            new = max(now - step, 0)
        elif direction is ChangeDirection.UP:
            new = min(now + step, max_value)
        if new != now:
            self._future = self.qtile.run_in_executor(self._change_backlight, new)
