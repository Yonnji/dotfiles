import json
import re
import os
import subprocess

from libqtile import bar, widget, images
from libqtile.command.base import expose_command
from libqtile.log_utils import logger
from libqtile.widget import base

from qtilemods.tools import shortcuts

from .mixins import IconTextMixin

POWER_PROFILES = (
    'power-saver',
    'balanced',
    'performance',
)

TUNED_PROFILES = (
    'powersave',
    'balanced-battery',
    'desktop',
)


class Power(IconTextMixin, base.PaddingMixin, base.ThreadPoolText):
    icon_names = (
        'power-profile-power-saver-symbolic',
        'power-profile-balanced-symbolic',
        'power-profile-performance-symbolic',
    )

    def __init__(self, **config):
        # self.foreground = config.get('foreground', '#ffffff')
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.images = {}
        self.profile_index = 0
        self.current_icon = 'power-profile-power-saver-symbolic'
        self.callback = config.get('callback', None)

        base.ThreadPoolText.__init__(self, '', **config)
        self.add_defaults(base.PaddingMixin.defaults)

        self.add_callbacks({
            'Button1': self.switch,
        })

        # profile_index = self.get_profile_index()
        # self.set_profile_index(profile_index)
        self.set_profile_index(1)

    def _configure(self, qtile, pbar):
        if self.theme_path:
            self.length_type = bar.STATIC
            self.length = 0
        base.ThreadPoolText._configure(self, qtile, pbar)
        self.setup_images()

    def get_icon_key(self, profile_index):
        return self.icon_names[profile_index]

    def calculate_length(self):
        return (
            super().calculate_length() +
            self.icon_size + self.icon_spacing)

    @expose_command()
    def switch(self):
        profile_index = self.profile_index + 1
        if profile_index >= 3:
            profile_index = 0

        self.set_profile_index(profile_index)

        if self.callback:
            self.callback(profile_index)

        self.update(self.poll())

    def set_profile_index(self, profile_index):
        if profile_index is None:
            return

        if os.path.exists('/usr/sbin/tuned-adm'):
            profile = TUNED_PROFILES[profile_index]
            logger.error(f'Switching profile to: {profile}')
            subprocess.call(['tuned-adm', 'profile', profile])
        else:
            profile = POWER_PROFILES[profile_index]
            logger.error(f'Switching profile to: {profile}')
            subprocess.call(['powerprofilesctl', 'set', profile])

        if profile_index == 1:  # middle
            shortcuts.spawn('picom')()
        else:
            subprocess.run(['pkill', 'picom'])

    def get_profile_index(self):
        if os.path.exists('/usr/sbin/tuned-adm'):
            output = subprocess.check_output(['tuned-adm', 'active']).decode().strip('\n')
            key, _, value = output.partition(':')
            profile = value.strip()
            logger.error(f'Current profile: {profile}')
            if profile not in TUNED_PROFILES:
                return 1
            return TUNED_PROFILES.index(profile)

        else:
            profile = subprocess.check_output(['powerprofilesctl', 'get']).decode().strip('\n')
            logger.error(f'Current profile: {profile}')
            if profile not in POWER_PROFILES:
                return 1
            return POWER_PROFILES.index(profile)

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
