import json
import re
import os
import subprocess

from libqtile import bar, widget, images, qtile
from libqtile.command.base import expose_command
from libqtile.log_utils import logger
from libqtile.widget import base

from .mixins import IconTextMixin
from ..icon_theme import get_icon_path
from ..tools import shortcuts


ICON_NAMES = (
    (-1, 'audio-volume-muted-symbolic'),
    (33, 'audio-volume-low-symbolic'),
    (66, 'audio-volume-medium-symbolic'),
    (100, 'audio-volume-high-symbolic'),
)

re_vol = re.compile(r"(\d?\d?\d?)%")


class Volume(IconTextMixin, base.PaddingMixin, base.InLoopPollText):
    """Widget that display and change volume

    By default, this widget uses ``amixer`` to get and set the volume so users
    will need to make sure this is installed. Alternatively, users may set the
    relevant parameters for the widget to use a different application.

    If theme_path is set it draw widget as icons.
    """

    orientations = base.ORIENTATION_HORIZONTAL
    defaults = [
        ("cardid", None, "Card Id"),
        ("device", "default", "Device Name"),
        ("channel", "Master", "Channel"),
        ("padding", 3, "Padding left and right. Calculated if None."),
        ("update_interval", 0.2, "Update time in seconds."),
        ("theme_path", None, "Path of the icons"),
        (
            "emoji",
            False,
            "Use emoji to display volume states, only if ``theme_path`` is not set."
            "The specified font needs to contain the correct unicode characters.",
        ),
        (
            "emoji_list",
            ["\U0001f507", "\U0001f508", "\U0001f509", "\U0001f50a"],
            "List of emojis/font-symbols to display volume states, only if ``emoji`` is set."
            " List contains 4 symbols, from lowest volume to highest.",
        ),
        ("mute_command", None, "Mute command"),
        ("mute_foreground", None, "Foreground color for mute volume."),
        ("mute_format", "M", "Format to display when volume is muted."),
        ("unmute_format", "{volume}%", "Format of text to display when volume is not muted."),
        ("volume_app", None, "App to control volume"),
        ("volume_up_command", None, "Volume up command"),
        ("volume_down_command", None, "Volume down command"),
        (
            "get_volume_command",
            None,
            "Command to get the current volume. "
            "The expected output should include 1-3 numbers and a ``%`` sign.",
        ),
        ("check_mute_command", None, "Command to check mute status"),
        (
            "check_mute_string",
            "[off]",
            "String expected from check_mute_command when volume is muted."
            "When the output of the command matches this string, the"
            "audio source is treated as muted.",
        ),
        (
            "step",
            2,
            "Volume change for up an down commands in percentage."
            "Only used if ``volume_up_command`` and ``volume_down_command`` are not set.",
        ),
        ("icon_names", ICON_NAMES, "Icon names."),
    ]

    def __init__(self, **config):
        base.InLoopPollText.__init__(self, **config)
        self.add_defaults(Volume.defaults)
        self.images = {}
        self.volume = None
        self.is_mute = False
        self.current_icon = self.icon_names[0][1]

        self.volume_app = config.get('volume_app')
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.icon_names = config.get('icon_names', ICON_NAMES)

        self.add_callbacks({
            'Button1': self.mute,
            'Button2': self.run_app,
            'Button3': self.run_app,
            'Button4': self.increase_vol,
            'Button5': self.decrease_vol,
        })

        self.add_defaults(base.PaddingMixin.defaults)

    def _configure(self, qtile, pbar):
        if self.theme_path:
            self.length_type = bar.STATIC
            self.length = 0
        base.ThreadPoolText._configure(self, qtile, pbar)
        self.setup_images()

    def setup_images(self):
        d_imgs = {}
        for icon_level, icon_name in self.icon_names:
            icon = get_icon_path(
                icon_name, size=self.icon_size,
                theme=self.theme_path, extensions=(self.icon_ext.lstrip('.'),))
            if icon:
                if icon.endswith('.svg'):  # symbolic icon
                    with open(icon, 'r') as f:
                        data = re.sub(r'fill="(#?[A-Za-z0-9]+)"', self._replace_svg_attr, f.read())
                        d_imgs[icon_name] = images.Img(data.encode(), icon_name, icon)
                else:
                    with open(icon, 'rb') as f:
                        d_imgs[icon_name] = images.Img(f.read(), icon_name, icon)

        for key, img in d_imgs.items():
            img.resize(height=self.icon_size)
            if img.width > self.length:
                self.length = img.width + self.padding_x * 2
            self.images[key] = img

    def calculate_length(self):
        return self.icon_size + self.padding_x * 2

    def get_volume(self):
        try:
            if self.get_volume_command is not None:
                get_volume_cmd = self.get_volume_command
            else:
                get_volume_cmd = self.create_amixer_command("sget", self.channel)

            mixer_out = subprocess.getoutput(get_volume_cmd)
        except subprocess.CalledProcessError:
            return -1, False

        check_mute = mixer_out
        if self.check_mute_command:
            check_mute = subprocess.getoutput(self.check_mute_command)

        muted = self.check_mute_string in check_mute

        volgroups = re_vol.search(mixer_out)
        if volgroups:
            return int(volgroups.groups()[0]), muted
        else:
            # this shouldn't happen
            return -1, muted

    def get_icon_key(self, volume, muted):
        if muted:
            return self.icon_names[0][1]

        for icon_level, icon_name in self.icon_names:
            if volume <= icon_level:
                return icon_name

        return self.icon_names[0][1]

    def create_amixer_command(self, *args):
        cmd = ["amixer"]

        if self.cardid is not None:
            cmd.extend(["-c", str(self.cardid)])

        if self.device is not None:
            cmd.extend(["-D", str(self.device)])

        cmd.extend([x for x in args])
        return subprocess.list2cmdline(cmd)

    @expose_command()
    def increase_vol(self):
        if self.is_mute:
            return

        if self.volume_up_command is not None:
            volume_up_cmd = self.volume_up_command
        else:
            volume_up_cmd = self.create_amixer_command(
                "-q", "sset", self.channel, f"{self.step}%+"
            )

        subprocess.call(volume_up_cmd, shell=True)
        self.update(self.poll())

        if self.volume >= 0:
            text = '{}%'.format(self.volume)
            qtile.widgets_map['notification'].update(text, self.volume / 100)

    @expose_command()
    def decrease_vol(self):
        if self.is_mute:
            return

        if self.volume_down_command is not None:
            volume_down_cmd = self.volume_down_command
        else:
            volume_down_cmd = self.create_amixer_command(
                "-q", "sset", self.channel, f"{self.step}%-"
            )

        subprocess.call(volume_down_cmd, shell=True)
        self.update(self.poll())

        if self.volume >= 0:
            text = '{}%'.format(self.volume)
            qtile.widgets_map['notification'].update(text, self.volume / 100)

    @expose_command()
    def mute(self):
        if self.mute_command is not None:
            mute_cmd = self.mute_command
        else:
            mute_cmd = self.create_amixer_command("-q", "sset", self.channel, "toggle")

        subprocess.call(mute_cmd, shell=True)
        self.update(self.poll())

    @expose_command()
    def run_app(self):
        if self.volume_app is not None:
            logger.error(self.volume_app)
            # subprocess.Popen(self.volume_app, shell=True)
            output = subprocess.getoutput(self.volume_app)
            logger.error(output)

    def poll(self):
        return self.get_volume()

    def update(self, value):
        vol, muted = value
        if vol != self.volume or muted != self.is_mute:
            self.volume = vol
            self.is_mute = muted
            self.text = ''

            icon = self.get_icon_key(vol, muted)
            if icon != self.current_icon:
                self.current_icon = icon

            self.draw()

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)

        if self.current_icon not in self.images:
            return

        image = self.images[self.current_icon]
        self.drawer.ctx.save()
        self.drawer.ctx.translate(self.padding_x, (self.bar.height - image.height) // 2)
        self.drawer.ctx.set_source(image.pattern)
        self.drawer.ctx.paint()
        self.drawer.ctx.restore()

        self.layout.draw(
           self.padding_x + self.icon_size + self.icon_spacing,
           (self.bar.height - self.layout.height) // 2 + 1,
        )

        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.length)
