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


class PipewireVolume(IconTextMixin, base.PaddingMixin, base.InLoopPollText):
    """Widget that display and change volume

    This widget uses ``wpctl`` to get and set the volume so users
    will need to make sure this is installed.

    If theme_path is set it draw widget as icons.
    """
    orientations = base.ORIENTATION_HORIZONTAL
    defaults = [
        ("channel", "@DEFAULT_AUDIO_SINK@", "Channel"),
        ("media_class", "Audio/Sink", "Channel's media class"),
        ("padding", 3, "Padding left and right. Calculated if None."),
        ("update_interval", 0.2, "Update time in seconds."),
        ("theme_path", None, "Path of the icons"),
        ("step", 2, "Volume change for up an down commands in percentage."),
        ("icon_names", ICON_NAMES, "Icon names."),
    ]


    def __init__(self, **config):
        base.InLoopPollText.__init__(self, **config)
        self.add_defaults(PipewireVolume.defaults)

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
        try:
            cmd = subprocess.list2cmdline(['wpctl', 'get-volume', self.channel])
            mixer_out = subprocess.getoutput(cmd)
        except subprocess.CalledProcessError:
            return -1

        if '[MUTED]' in mixer_out:
            return -1

        volgroups = mixer_out and mixer_out.split(' ')
        if not volgroups:
            return -1

        volgroup = volgroups[1]
        if not re.match(r'[0-9]+\.?[0-9]*', volgroup):
            return -1

        return int(float(volgroup) * 100)

    def get_icon_key(self, volume):
        for icon_level, icon_name in self.icon_names:
            if volume <= icon_level:
                return icon_name

        return self.icon_names[0][1]

    @expose_command()
    def increase_vol(self):
        if self.volume < 100:
            value = '100%'
            if self.volume + self.step < 100:
                value = '{}%+'.format(self.step)

            cmd = subprocess.list2cmdline(['wpctl', 'set-volume', self.channel, str(value)])
            subprocess.call(cmd, shell=True)
            self.update(self.poll())

        if self.volume >= 0:
            text = '{}%'.format(self.volume)
            qtile.widgets_map['notification'].update(text, self.volume / 100)

    @expose_command()
    def decrease_vol(self):
        if self.volume > 0:
            value = '0%'
            if self.volume - self.step > 0:
                value = '{}%-'.format(self.step)

            cmd = subprocess.list2cmdline(['wpctl', 'set-volume', self.channel, str(value)])
            subprocess.call(cmd, shell=True)
            self.update(self.poll())

        if self.volume >= 0:
            text = '{}%'.format(self.volume)
            qtile.widgets_map['notification'].update(text, self.volume / 100)

    @expose_command()
    def mute(self):
        cmd = subprocess.list2cmdline(['wpctl', 'set-mute', self.channel, 'toggle'])
        subprocess.call(cmd, shell=True)
        self.update(self.poll())

    def _get_data(self):
        output = subprocess.check_output(['pw-dump', '--no-colors']).decode()
        # merge multiple arrays to fix invalid json
        output = output.replace(']\n[', ',')
        return json.loads(output)

    def _get_metadata(self, data):
        metadata = []
        for item in data:
            if item.get('type') == 'PipeWire:Interface:Metadata':
                if item.get('props', {}).get('metadata.name') == 'default':
                    metadata = item.get('metadata', [])

        return metadata

    def _get_current_channel_name(self, data):
        key = 'default.{}'.format(self.media_class.replace('/', '.').lower())
        for option in self._get_metadata(data):
            if option.get('key') == key:
                return option.get('value', {}).get('name')

    def _get_current_channel(self, data):
        current_channel_name = self._get_current_channel_name(data)
        for item in data:
            if not item.get('info'):
                continue

            props = item['info'].get('props', {})
            if props.get('media.class') != self.media_class:
                continue

            name = props.get('node.name')
            if name == current_channel_name:
                return item

    @expose_command()
    def next_channel(self):
        data = self._get_data()
        current_channel = self._get_current_channel(data)

        current_channel_index = None
        channels = []
        for item in data:
            if not item.get('info'):
                continue

            props = item['info'].get('props', {})
            if props.get('media.class') != self.media_class:
                continue

            if item['id'] == current_channel['id']:
                current_channel_index = len(channels)

            channels.append(item)

        if current_channel_index is None:
            return

        for _ in range(len(channels)):
            current_channel_index += 1
            if current_channel_index >= len(channels):
                current_channel_index = 0

            new_channel = channels[current_channel_index]
            new_props = new_channel.get('info', {}).get('props', {})
            new_id = str(new_channel['id'])
            new_name = new_props.get('node.name')
            logger.error(f'Switching to "{new_id}. {new_name}"')
            cmd = ['wpctl', 'set-default', new_id]
            logger.error(' '.join(cmd))
            subprocess.check_output(cmd)

            data = self._get_data()
            current_channel = self._get_current_channel(data)
            if new_channel['id'] == current_channel['id']:
                break
            else:
                logger.error(f'Cannot switch to "{new_id}. {new_name}"')
        else:
            return

        props = current_channel.get('info', {}).get('props', {})
        desc = props.get('node.description')
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
