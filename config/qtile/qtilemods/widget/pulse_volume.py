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


ICON_NAMES = (
    (0, 'audio-volume-muted-symbolic'),
    (33, 'audio-volume-low-symbolic'),
    (66, 'audio-volume-medium-symbolic'),
    (100, 'audio-volume-high-symbolic'),
)


class PulseVolume(IconTextMixin, base.PaddingMixin, base.InLoopPollText):
    """Widget that display and change volume

    This widget uses ``pactl`` to get and set the volume so users
    will need to make sure this is installed.

    If theme_path is set it draw widget as icons.
    """
    orientations = base.ORIENTATION_HORIZONTAL
    defaults = [
        ("channel", "@DEFAULT_SINK@", "Channel"),
        ("media_class", "sink", "Channel's media class"),
        ("padding", 3, "Padding left and right. Calculated if None."),
        ("update_interval", 0.2, "Update time in seconds."),
        ("theme_path", None, "Path of the icons"),
        ("step", 2, "Volume change for up an down commands in percentage."),
        ("icon_names", ICON_NAMES, "Icon names."),
    ]

    def __init__(self, **config):
        base.InLoopPollText.__init__(self, **config)
        self.add_defaults(PulseVolume.defaults)

        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.icon_names = config.get('icon_names', ICON_NAMES)
        self.images = {}
        self.volume = 0
        self.current_icon = self.icon_names[0][1]

        self.add_callbacks({
            'Button1': self.mute,
            'Button2': self.next_channel,
            'Button3': self.next_channel,
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
        channel = self._get_current_channel_name()

        data = self._get_data()
        for item in data:
            if item['name'] == channel:
                if item['mute']:
                    return -1
                volume = item['volume']['front-left']['value_percent']
                return int(volume.rstrip('%'))

        return -1

    def get_icon_key(self, volume):
        for icon_level, icon_name in self.icon_names:
            if volume <= icon_level:
                return icon_name

        return self.icon_names[0][1]

    @expose_command()
    def increase_vol(self):
        if self.volume < 100:
            volume = min(self.volume + self.step, 100)
            cmd = subprocess.list2cmdline([
                'pactl', f'set-{self.media_class}-volume', self.channel, f'{volume}%'])
            subprocess.call(cmd, shell=True)
            self.update(self.poll())

        if self.volume >= 0:
            text = '{}%'.format(self.volume)
            qtile.widgets_map['notification'].update(text, self.volume / 100)

    @expose_command()
    def decrease_vol(self):
        if self.volume > 0:
            volume = max(self.volume - self.step, 0)
            cmd = subprocess.list2cmdline([
                'pactl', f'set-{self.media_class}-volume', self.channel, f'{volume}%'])
            subprocess.call(cmd, shell=True)
            self.update(self.poll())

        if self.volume >= 0:
            text = '{}%'.format(self.volume)
            qtile.widgets_map['notification'].update(text, self.volume / 100)

    @expose_command()
    def mute(self):
        cmd = subprocess.list2cmdline([
            'pactl', f'set-{self.media_class}-mute', self.channel, 'toggle'])
        subprocess.call(cmd, shell=True)
        self.update(self.poll())

    def _get_data(self):
        output = subprocess.check_output([
            'pactl', '-f', 'json', 'list', f'{self.media_class}s']).decode()
        return json.loads(output)

    def _get_current_channel_name(self):
        output = subprocess.check_output([
            'pactl', f'get-default-{self.media_class}']).decode()
        return output.strip('\n')

    @expose_command()
    def next_channel(self):
        data = self._get_data()
        current_channel = self._get_current_channel_name()

        current_channel_index = None
        channels = []
        for item in data:
            if not item.get('monitor_source'):
                continue

            if item['name'] == current_channel:
                current_channel_index = len(channels)

            channels.append(item)

        if current_channel_index is None:
            return

        for _ in range(len(channels)):
            current_channel_index += 1
            if current_channel_index >= len(channels):
                current_channel_index = 0

            new_channel = channels[current_channel_index]
            new_name = new_channel['name']
            logger.error(f'Switching to "{new_name}"')
            cmd = ['pactl', f'set-default-{self.media_class}', new_name]
            logger.error(' '.join(cmd))
            subprocess.check_output(cmd)

            current_channel = self._get_current_channel_name()
            if new_channel['name'] == current_channel:
                break
            else:
                logger.error(f'Cannot switch to "{new_name}"')
        else:
            return

        desc = new_channel.get('description')
        desc = desc.replace('Audio Controller', '')
        if len(desc) > 30:
            desc = desc[:30-3] + '...'
        qtile.widgets_map['notification'].update(desc)

        self.update(self.poll())

    @expose_command()
    def run_app(self):
        if self.volume_app is not None:
            subprocess.Popen(self.volume_app, shell=True)

    def poll(self):
        return self.get_volume()

    def update(self, vol):
        if vol != self.volume:
            self.volume = vol
            self.text = ''
            # self.text = f'{vol}%'

            icon = self.get_icon_key(vol)
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
