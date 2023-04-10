import re
import os
import subprocess

from libqtile import widget, images
from libqtile.command.base import expose_command
from libqtile.log_utils import logger
from libqtile.widget import base

from .volume import Volume


class VolumeMic(Volume):
    icon_names = (
        'microphone-disabled-symbolic',
        'microphone-hardware-disabled-symbolic',
        'microphone-sensitivity-high-symbolic',
        'microphone-sensitivity-low-symbolic',
        'microphone-sensitivity-medium-symbolic',
        'microphone-sensitivity-muted-symbolic',
    )

    def __init__(self, **config):
        # self.foreground = config.get('foreground', '#ffffff')
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.images = {}
        self.current_icon = 'microphone-sensitivity-muted-symbolic'

        base._TextBox.__init__(self, '', **config)
        self.add_defaults(widget.Volume.defaults)
        self.volume = 0
        self.add_callbacks({
            'Button1': self.mute,
            'Button2': self.run_app,
            'Button3': self.run_app,
            'Button4': self.increase_vol,
            'Button5': self.decrease_vol,
        })

        self.add_defaults(base.PaddingMixin.defaults)
        self.channel = config.get('channel', '@DEFAULT_AUDIO_SOURCE@')
        self.check_mute_string = config.get('check_mute_string', '[MUTED]')

    def get_icon_key(self, volume):
        if volume <= 0:
            mode = 'muted'
        elif volume < 33:
            mode = 'low'
        elif volume < 66:
            mode = 'medium'
        else:
            mode = 'high'

        return f'microphone-sensitivity-{mode}-symbolic'
