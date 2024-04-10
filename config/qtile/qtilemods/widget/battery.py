import re
import os

from libqtile import widget, images, qtile
from libqtile.widget import base
from libqtile.log_utils import logger

from .mixins import IconTextMixin


class Battery(IconTextMixin, widget.Battery):
    icon_names = (
        'battery-level-0-charging-symbolic',
        'battery-level-0-symbolic',
        'battery-level-10-charging-symbolic',
        'battery-level-10-symbolic',
        'battery-level-20-charging-symbolic',
        'battery-level-20-symbolic',
        'battery-level-30-charging-symbolic',
        'battery-level-30-symbolic',
        'battery-level-40-charging-symbolic',
        'battery-level-40-symbolic',
        'battery-level-50-charging-symbolic',
        'battery-level-50-symbolic',
        'battery-level-60-charging-symbolic',
        'battery-level-60-symbolic',
        'battery-level-70-charging-symbolic',
        'battery-level-70-symbolic',
        'battery-level-80-charging-symbolic',
        'battery-level-80-symbolic',
        'battery-level-90-charging-symbolic',
        'battery-level-90-symbolic',
        'battery-level-100-charged-symbolic',
        'battery-level-100-symbolic',
        'battery-low-symbolic',
        'battery-missing-symbolic',
        'battery-action-symbolic',
        'battery-caution-symbolic',
    )

    def __init__(self, **config):
        # self.foreground = config.get('foreground', '#ffffff')
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.images = {}
        self.current_icon = 'battery-missing-symbolic'
        self.padding = config.get('padding', 0)
        self.padding_x = config.get('padding_x') or self.padding
        self.padding_y = config.get('padding_y') or self.padding
        super().__init__(**config)

    def _configure(self, qtile_, bar_):
        super()._configure(qtile_, bar_)
        self.setup_images()

    def get_icon_key(self, status):
        status_state = status.state
        status_level = status.percent * 100

        level = 0
        mode = ''

        if status_state == widget.battery.BatteryState.CHARGING:
            mode = '-charging'

        if status_state == widget.battery.BatteryState.FULL:
            level = 100
        else:
            for level in range(0, 110, 10):
                if status_level <= level:
                    break

        if level == 100:
            mode = '-charged'

        return f'battery-level-{level}{mode}-symbolic'

    def calculate_length(self):
        return (
            super().calculate_length() +
            self.icon_size + self.icon_spacing)

    def update(self, text):
        if text != self.text:
            old_width = self.layout.width
            self.text = text

            status = self._battery.update_status()
            icon = self.get_icon_key(status)
            self.current_icon = icon

            if self.layout.width == old_width:
                self.draw()
            else:
                self.bar.draw()

        images = []
        for (prefix, dirs, files) in os.walk(os.path.expanduser('~/Pictures/Slideshow')):
            for image in files:
                if image.endswith('.png') or image.endswith('.jpg') or image.endswith('.jpeg'):
                    images.append(os.path.join(prefix, image))

        if not hasattr(self, 'image_index'):
            self.image_index = 0
        for screen in qtile.screens:
            screen.paint(images[self.image_index], 'fill')
        self.image_index = self.image_index + 1 if self.image_index < len(images) - 1 else 0
