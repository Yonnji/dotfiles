from .displaylight import DisplayLight


class KeyboardLight(DisplayLight):
    backlight_dir = '/sys/class/leds'
    icon_names = (
        'keyboard-brightness-symbolic.svg',
    )
