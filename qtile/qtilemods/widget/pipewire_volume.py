import json
import re
import os
import subprocess

from libqtile import bar, widget, images, qtile
from libqtile.command.base import expose_command
from libqtile.log_utils import logger
from libqtile.widget import base

from .mixins import IconTextMixin


class PipewireVolume(IconTextMixin, base.PaddingMixin, base.InLoopPollText):
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
        ("mute_command", None, "Mute command"),
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
    ]

    icon_names = (
        'audio-volume-high-symbolic',
        'audio-volume-medium-symbolic',
        'audio-volume-low-symbolic',
        'audio-volume-muted-symbolic',
    )

    def __init__(self, **config):
        base.InLoopPollText.__init__(self, **config)
        self.add_defaults(PipewireVolume.defaults)
        self.volume = 0

        # self.foreground = config.get('foreground', '#ffffff')
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.images = {}
        self.current_icon = 'audio-volume-muted-symbolic'

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

    def _configure(self, qtile, pbar):
        if self.theme_path:
            self.length_type = bar.STATIC
            self.length = 0
        base.ThreadPoolText._configure(self, qtile, pbar)
        self.setup_images()

    def calculate_length(self):
        return (
            super().calculate_length() +
            self.icon_size + self.icon_spacing)

    def create_command(self, *args):
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
                get_volume_cmd = self.create_command('sget', self.channel)

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

    @expose_command()
    def increase_vol(self):
        if self.volume < 0:
            return

        if self.volume < 100:
            if self.volume_up_command is not None:
                volume_up_cmd = self.volume_up_command
            else:
                volume_up_cmd = self.create_command(
                    "-q", "sset", self.channel, "{}%+".format(self.step)
                )
            subprocess.call(volume_up_cmd, shell=True)

        self.update(self.poll())

        if self.volume >= 0:
            text = '{}%'.format(self.volume)
            qtile.widgets_map['notification'].update(text, self.volume / 100)

    @expose_command()
    def decrease_vol(self):
        if self.volume < 0:
            return

        if self.volume > 0:
            if self.volume_down_command is not None:
                volume_down_cmd = self.volume_down_command
            else:
                volume_down_cmd = self.create_command(
                    "-q", "sset", self.channel, "{}%-".format(self.step)
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
            mute_cmd = self.create_command("-q", "sset", self.channel, "toggle")
        subprocess.call(mute_cmd, shell=True)

        self.update(self.poll())

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

        # self.timeout_add(self.update_interval, self.update)
