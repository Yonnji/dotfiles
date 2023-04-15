import json
import re
import os
import subprocess

from libqtile import widget, images, qtile
from libqtile.command.base import expose_command
from libqtile.log_utils import logger
from libqtile.widget import base

from .mixins import IconTextMixin


class Volume(IconTextMixin, base.PaddingMixin, widget.Volume):
    icon_names = (
        'audio-volume-high-symbolic',
        'audio-volume-medium-symbolic',
        'audio-volume-low-symbolic',
        'audio-volume-muted-symbolic',
    )

    def __init__(self, **config):
        # self.foreground = config.get('foreground', '#ffffff')
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.images = {}
        self.current_icon = 'audio-volume-muted-symbolic'

        base._TextBox.__init__(self, '', **config)
        self.add_defaults(widget.Volume.defaults)
        self.volume = 0
        self.add_callbacks({
            'Button1': self.mute,
            'Button2': self.next_channel,
            'Button3': self.next_channel,
            'Button4': self.increase_vol,
            'Button5': self.decrease_vol,
        })

        self.add_defaults(base.PaddingMixin.defaults)
        self.channel = config.get('channel', '@DEFAULT_AUDIO_SINK@')
        self.media_class = 'Audio/Sink'
        self.check_mute_string = config.get('check_mute_string', '[MUTED]')

    def create_amixer_command(self, *args):
        cmd = ['wpctl']

        for arg in args:
            if arg.startswith('-'):
                continue
            elif arg == 'sget':
                cmd.append('get-volume')
            elif arg == 'sset':
                if 'toggle' in args:
                    cmd.append('set-mute')
                else:
                    cmd.append('set-volume')
            else:
                cmd.append(arg)

        return subprocess.list2cmdline(cmd)

    def get_volume(self):
        try:
            if self.get_volume_command is not None:
                get_volume_cmd = self.get_volume_command
            else:
                get_volume_cmd = self.create_amixer_command('sget', self.channel)

            mixer_out = subprocess.getoutput(get_volume_cmd)
        except subprocess.CalledProcessError:
            return -1

        check_mute = mixer_out
        if self.check_mute_command:
            check_mute = subprocess.getoutput(self.check_mute_command)

        if self.check_mute_string in check_mute:
            return -1

        volgroups = mixer_out and mixer_out.split(' ')
        if not volgroups:
            return -1

        volgroup = volgroups[1]
        if not re.match(r'[0-9]+\.?[0-9]*', volgroup):
            return -1

        return int(float(volgroup) * 100)

    def get_icon_key(self, volume):
        if volume <= 0:
            mode = 'muted'
        elif volume < 33:
            mode = 'low'
        elif volume < 66:
            mode = 'medium'
        else:
            mode = 'high'

        return f'audio-volume-{mode}-symbolic'

    def calculate_length(self):
        return (
            super().calculate_length() +
            self.icon_size + self.icon_spacing)

    @expose_command()
    def increase_vol(self):
        if self.volume < 0:
            return

        if self.volume < 100:
            super().increase_vol()
        self.update()

        if self.volume >= 0:
            text = '{}%'.format(self.volume)
            qtile.widgets_map['notification'].update(text, self.volume / 100)

    @expose_command()
    def decrease_vol(self):
        if self.volume < 0:
            return

        if self.volume > 0:
            super().decrease_vol()
        self.update()

        if self.volume >= 0:
            text = '{}%'.format(self.volume)
            qtile.widgets_map['notification'].update(text, self.volume / 100)

    @expose_command()
    def mute(self):
        super().mute()
        self.update()

    @expose_command()
    def next_channel(self):
        output = subprocess.check_output(['pw-dump', '--no-colors']).decode()
        data = json.loads(output)

        metadata = []
        for item in data:
            if item.get('type') == 'PipeWire:Interface:Metadata':
                if item.get('props', {}).get('metadata.name') == 'default':
                    metadata = item.get('metadata', [])

        channel_metadata = {}
        key = 'default.{}'.format(self.media_class.replace('/', '.').lower())
        for option in metadata:
            if option.get('key') == key:
                channel_metadata = option.get('value')

        channel_id = None
        channels = []
        for item in data:
            props = item.get('info', {}).get('props', {})
            if props.get('media.class') == self.media_class:
                channels.append(item)
                if channel_metadata and channel_metadata.get('name') == props.get('node.name'):
                    channel_id = len(channels) - 1

        if channel_id is None:
            return

        channel_id += 1
        if channel_id >= len(channels):
            channel_id = 0
        channel = channels[channel_id]

        subprocess.check_output([
            'wpctl', 'set-default', str(channel['id'])])

        props = channel.get('info', {}).get('props', {})
        desc = props.get('node.description')
        if len(desc) > 30:
            desc = desc[:30-3] + '...'
        qtile.widgets_map['notification'].update(desc)

    def update(self):
        vol = self.get_volume()
        if vol != self.volume:
            self.volume = vol
            self.text = ''
            # self.text = f'{vol}%'

            icon = self.get_icon_key(vol)
            if icon != self.current_icon:
                self.current_icon = icon

            self.draw()

        self.timeout_add(self.update_interval, self.update)
