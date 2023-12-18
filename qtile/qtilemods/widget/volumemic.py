import re
import os
import subprocess

from libqtile import widget, images
from libqtile.command.base import expose_command
from libqtile.log_utils import logger
from libqtile.widget import base

from .pipewire_volume import PipewireVolume


class VolumeMic(PipewireVolume):
    icon_names = (
        (0, 'microphone-sensitivity-muted-symbolic'),
        (33, 'microphone-sensitivity-low-symbolic'),
        (66, 'microphone-sensitivity-medium-symbolic'),
        (100, 'microphone-sensitivity-high-symbolic'),
    )
