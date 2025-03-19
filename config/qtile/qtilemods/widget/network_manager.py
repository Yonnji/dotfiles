import json
import re
import os
import subprocess

from libqtile import bar, widget, images
from libqtile.command.base import expose_command
from libqtile.log_utils import logger
from libqtile.widget import base

from .mixins import IconTextMixin


class NetworkManager(IconTextMixin, base.MarginMixin, base.PaddingMixin, base.InLoopPollText):
    icon_names = (
        'network-vpn-symbolic',
        'network-idle-symbolic',
        'network-transmit-receive-symbolic',
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
        self.network_app = config.get('network_app')
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.images = {}
        self.signal = -1

        base.InLoopPollText.__init__(self, width=bar.STRETCH, **config)
        self.add_defaults(base.PaddingMixin.defaults)
        self.add_defaults(base.MarginMixin.defaults)

        # self.foreground = config.get('foreground', '#ffffff')
        # self.signal = -3
        # self.current_icon = 'network-wireless-hardware-disabled-symbolic'

        if self.spacing is None:
            self.spacing = self.margin_x

        self.add_callbacks({
            'Button1': self.run_app,
            'Button2': self.run_app,
            'Button3': self.run_app,
        })

    @expose_command()
    def run_app(self):
        if self.network_app is not None:
            logger.error(self.network_app)
            subprocess.Popen(self.network_app, shell=True)
            # shortcuts.spawn(self.volume_app)()

    def calc_box_widths(self):
        interfaces = tuple(self.interfaces)
        if not interfaces:
            return []

        icons = [self.get_icon(interface) for interface in interfaces]
        names = [interface for interface in interfaces]
        width_boxes = [self.icon_size for icon in icons]
        return zip(interfaces, icons, names, width_boxes)

    def calculate_length(self):
        width = 0
        box_widths = [box[3] for box in self.calc_box_widths()]
        if box_widths:
            width += self.spacing * len(box_widths) - 1
            width += sum(w for w in box_widths)
        width += self.margin_x * 2

        return width

    def _configure(self, qtile, pbar):
        if self.theme_path:
            self.length_type = bar.CALCULATED
            self.length = 0
        base.ThreadPoolText._configure(self, qtile, pbar)
        self.setup_images()

    @property
    def interfaces(self):
        has_wifi = False
        out = subprocess.check_output(['nmcli', '-f', 'type', 'c', 'show', '--active']).decode()
        for line in out.split('\n'):
            ctype = line.strip()

            if ctype == 'vpn':
                yield 'network-vpn-symbolic'

            elif ctype == 'ethernet':
                yield 'network-transmit-receive-symbolic'

            elif ctype == 'wifi':
                has_wifi = True
                if self.signal < 20:
                    strength = 'none'
                elif self.signal < 40:
                    strength = 'weak'
                elif self.signal < 60:
                    strength = 'ok'
                elif self.signal < 80:
                    strength = 'good'
                else:
                    strength = 'excellent'
                yield f'network-wireless-signal-{strength}-symbolic'

        if not has_wifi:
            if self.signal <= -3:
                yield 'network-wireless-hardware-disabled-symbolic'
            elif self.signal <= -2:
                yield 'network-wireless-disabled-symbolic'
            elif self.signal <= -1:
                yield 'network-wireless-offline-symbolic'

    def get_signal(self):
        rfkill = json.loads(subprocess.check_output(['rfkill', '-J']).decode())
        for dev in rfkill['rfkilldevices']:
            if dev['type'] == 'wlan' and dev['hard'] == 'blocked':
                return -3
            elif dev['type'] == 'wlan' and dev['soft'] == 'blocked':
                return -2

        out = subprocess.check_output([
            'nmcli', '-f', 'in-use,signal',
            'd', 'wifi', 'list', '--rescan', 'no']).decode()
        for line in out.split('\n'):
            if line.strip().startswith('*'):
                return int(line.strip().lstrip('*'))
        else:
            return -1

    def poll(self):
        return self.get_signal()

    def update(self, signal):
        if signal != self.signal:
            self.signal = signal
            self.draw()

    def box_width(self, interfaces):
        return (self.icon_size + self.icon_spacing) * len(interfaces)

    def draw_icon(self, surface, offset):
        if not surface:
            return

        self.drawer.ctx.save()
        self.drawer.ctx.translate(offset, (self.bar.height - self.icon_size) // 2)
        self.drawer.ctx.set_source(surface.pattern)
        self.drawer.ctx.paint()
        self.drawer.ctx.restore()

    def get_icon(self, interface):
        return self.images.get(interface)

    def drawbox(self, offset, width=None, rounded=False, block=False, icon=None, minimized=False):
        self.drawer.set_source_rgb(self.background or self.bar.background)

        x = offset
        y = (self.bar.height - self.icon_size) // 2
        w = self.icon_size
        h = self.icon_size

        if not block:
            x += w // 2
            if minimized:
                w = w // 8
            else:
                w = w // 2
            x -= w // 2
            y = 0

        if icon:
            self.draw_icon(icon, offset)

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)
        offset = self.margin_x

        for interface, icon, task, bw in self.calc_box_widths():
            # self._box_end_positions.append(offset + bw)
            textwidth = bw - (self.icon_size if icon else 0)
            self.drawbox(
                offset,
                width=textwidth,
                icon=icon
            )
            offset += bw + self.spacing

        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.width)
