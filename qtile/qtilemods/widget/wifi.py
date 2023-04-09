import json
import re
import os
import subprocess

from libqtile import bar, widget, images
from libqtile.command.base import expose_command
from libqtile.log_utils import logger
from libqtile.widget import base

from .mixins import IconTextMixin


class Wifi(IconTextMixin, base.PaddingMixin, base.ThreadPoolText):
    icon_names = (
        'network-wireless-acquiring-symbolic',
        'network-wireless-connected-symbolic',
        'network-wireless-disabled-symbolic',
        'network-wireless-encrypted-symbolic',
        'network-wireless-hardware-disabled-symbolic',
        'network-wireless-hotspot-symbolic',
        'network-wireless-no-route-symbolic',
        'network-wireless-offline-symbolic',
        'network-wireless-signal-excellent-secure-symbolic',
        'network-wireless-signal-excellent-symbolic',
        'network-wireless-signal-good-secure-symbolic',
        'network-wireless-signal-good-symbolic',
        'network-wireless-signal-none-secure-symbolic',
        'network-wireless-signal-none-symbolic',
        'network-wireless-signal-ok-secure-symbolic',
        'network-wireless-signal-ok-symbolic',
        'network-wireless-signal-weak-secure-symbolic',
        'network-wireless-signal-weak-symbolic',
    )

    def __init__(self, **config):
        # self.foreground = config.get('foreground', '#ffffff')
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.images = {}
        self.signal = -3
        self.current_icon = 'network-wireless-hardware-disabled-symbolic'

        base.ThreadPoolText.__init__(self, '', **config)
        self.add_defaults(base.PaddingMixin.defaults)

        self.add_callbacks({
            'Button1': self.block,
            'Button2': self._setup,
            'Button3': self._setup,
        })

    def _setup(self):
        subprocess.Popen(['nm-connection-editor'], start_new_session=True)

    def _configure(self, qtile, pbar):
        if self.theme_path:
            self.length_type = bar.STATIC
            self.length = 0
        base.ThreadPoolText._configure(self, qtile, pbar)
        self.setup_images()

    def get_icon_key(self, signal):
        if signal <= -3:
            return 'network-wireless-hardware-disabled-symbolic'
        elif signal <= -2:
            return 'network-wireless-disabled-symbolic'
        elif signal <= -1:
            return 'network-wireless-offline-symbolic'
        elif signal < 20:
            strength = 'none'
        elif signal < 40:
            strength = 'weak'
        elif signal < 60:
            strength = 'ok'
        elif signal < 80:
            strength = 'good'
        else:
            strength = 'excellent'

        return f'network-wireless-signal-{strength}-symbolic'

    def calculate_length(self):
        return (
            super().calculate_length() +
            self.icon_size + self.icon_spacing)

    @expose_command()
    def block(self):
        subprocess.call(['rfkill', 'toggle', 'wlan'])
        self.update(self.get_signal())

    def get_signal(self):
        rfkill = json.loads(subprocess.check_output(['rfkill', '-J']).decode())
        for dev in rfkill['rfkilldevices']:
            if dev['type'] == 'wlan' and dev['hard'] == 'blocked':
                return -3
            elif dev['type'] == 'wlan' and dev['soft'] == 'blocked':
                return -2

        out = subprocess.check_output(['nmcli', '-f', 'IN-USE,SIGNAL', 'd', 'wifi']).decode()
        for line in out.split('\n'):
            if line.strip().startswith('*'):
                return int(line.strip().lstrip('*'))

        return -1

    def poll(self):
        return self.get_signal()

    def update(self, signal):
        if signal != self.signal:
            self.signal = signal
            self.text = ''

            icon = self.get_icon_key(signal)
            if icon != self.current_icon:
                self.current_icon = icon
                self.draw()
