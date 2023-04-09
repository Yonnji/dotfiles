import json
import re
import os
import subprocess

from libqtile import bar, widget, images
from libqtile.command.base import expose_command
from libqtile.log_utils import logger
from libqtile.widget import base

from .mixins import IconTextMixin


class Bluetooth(IconTextMixin, base.PaddingMixin, base.ThreadPoolText):
    icon_names = (
        'bluetooth-active-symbolic',
        'bluetooth-disabled-symbolic',
        'bluetooth-disconnected-symbolic',
        'bluetooth-hardware-disabled-symbolic',
    )

    def __init__(self, **config):
        # self.foreground = config.get('foreground', '#ffffff')
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.images = {}
        self.signal = -3
        self.current_icon = 'bluetooth-hardware-disabled-symbolic'

        base.ThreadPoolText.__init__(self, '', **config)
        self.add_defaults(base.PaddingMixin.defaults)

        self.add_callbacks({
            'Button1': self.block,
        })

    def _configure(self, qtile, pbar):
        if self.theme_path:
            self.length_type = bar.STATIC
            self.length = 0
        base.ThreadPoolText._configure(self, qtile, pbar)
        self.setup_images()

    def get_icon_key(self, signal):
        if signal <= -3:
            return 'bluetooth-hardware-disabled-symbolic'
        elif signal <= -2:
            # return 'bluetooth-disabled-symbolic'
            return 'bluetooth-hardware-disabled-symbolic'
        elif signal <= -1:
            # return 'bluetooth-disconnected-symbolic'
            return 'bluetooth-disabled-symbolic'
        else:
            return 'bluetooth-active-symbolic'

    def calculate_length(self):
        return (
            super().calculate_length() +
            self.icon_size + self.icon_spacing)

    @expose_command()
    def block(self):
        subprocess.call(['rfkill', 'toggle', 'bluetooth'])
        self.update(self.get_signal())

    def get_signal(self):
        rfkill = json.loads(subprocess.check_output(['rfkill', '-J']).decode())
        for dev in rfkill['rfkilldevices']:
            if dev['type'] == 'bluetooth' and dev['hard'] == 'blocked':
                return -3
            elif dev['type'] == 'bluetooth' and dev['soft'] == 'blocked':
                return -2

        out = subprocess.check_output(['bluetoothctl', 'devices', 'Connected']).decode()
        devices = tuple(filter(None, out.split('\n')))
        if devices:
            return len(devices)

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
