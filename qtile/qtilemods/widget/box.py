import re
import os
import subprocess

from libqtile import widget, images, bar
from libqtile.command.base import expose_command
from libqtile.log_utils import logger
from libqtile.widget import base

from .mixins import IconTextMixin


class Box(IconTextMixin, base.PaddingMixin, widget.WidgetBox):
    icon_names = (
        'view-conceal-symbolic',
        'visible-symbolic',
    )

    def __init__(self, **config):
        # self.theme_path = config.get('theme_path', None)
        self.foreground = config.get('foreground', '#ffffff')
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.images = {}
        self.current_icon = 'visible-symbolic'

        super().__init__(**config)
        self.add_defaults(base.PaddingMixin.defaults)

    def _configure(self, qtile, pbar):
        super()._configure(qtile, pbar)
        if self.theme_path:
            self.length_type = bar.STATIC
            self.length = 0
        self.setup_images()

    def calculate_length(self):
        return (
            super().calculate_length() +
            self.icon_size + self.icon_spacing)

    def set_box_label(self):
        super().set_box_label()
        self.current_icon = 'view-conceal-symbolic' if self.box_is_open else 'visible-symbolic'
