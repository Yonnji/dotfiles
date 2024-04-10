import json
import re
import os
import subprocess

from libqtile import bar, widget, images
from libqtile.command.base import expose_command
from libqtile.log_utils import logger
from libqtile.widget import base

from .mixins import IconTextMixin


class Power(IconTextMixin, base.PaddingMixin, base.ThreadPoolText):
    icon_names = (
        'power-profile-power-saver-symbolic',
        'power-profile-balanced-symbolic',
        'power-profile-performance-symbolic',
    )
    profiles = (
        'power-saver',
        'balanced',
        'performance',
    )

    def __init__(self, **config):
        # self.foreground = config.get('foreground', '#ffffff')
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.images = {}
        self.profile_index = 0
        self.current_icon = 'power-profile-power-saver-symbolic'

        base.ThreadPoolText.__init__(self, '', **config)
        self.add_defaults(base.PaddingMixin.defaults)

        self.add_callbacks({
            'Button1': self.switch,
        })

    def _configure(self, qtile, pbar):
        if self.theme_path:
            self.length_type = bar.STATIC
            self.length = 0
        base.ThreadPoolText._configure(self, qtile, pbar)
        self.setup_images()

    def get_icon_key(self, profile_index):
        profile = self.profiles[profile_index]
        return f'power-profile-{profile}-symbolic'

    def calculate_length(self):
        return (
            super().calculate_length() +
            self.icon_size + self.icon_spacing)

    @expose_command()
    def switch(self):
        profile_index = self.profile_index + 1
        if profile_index >= len(self.profiles):
            profile_index = 0

        profile = self.profiles[profile_index]
        subprocess.call(['powerprofilesctl', 'set', profile])

        if profile == 'balanced':
            subprocess.Popen(['picom'], start_new_session=True)
        else:
            subprocess.run(['pkill', 'picom'])

        self.update(self.get_profile_index())

    def get_profile_index(self):
        profile = subprocess.check_output(['powerprofilesctl', 'get']).decode().strip('\n')
        return self.profiles.index(profile)

    def poll(self):
        return self.get_profile_index()

    def update(self, profile_index):
        if profile_index != self.profile_index:
            self.profile_index = profile_index
            self.text = ''

            icon = self.get_icon_key(profile_index)
            if icon != self.current_icon:
                self.current_icon = icon
                self.draw()
