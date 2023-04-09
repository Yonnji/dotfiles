import os

from functools import partial

from libqtile.widget.backlight import ChangeDirection

from .displaylight import DisplayLight


class KeyboardLight(DisplayLight):
    backlight_dir = '/sys/class/leds'
    icon_names = (
        'keyboard-brightness-symbolic.svg',
    )
