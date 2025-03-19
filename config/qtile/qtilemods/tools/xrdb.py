import os
import subprocess

from libqtile.log_utils import logger

from qtilemods.tools import shortcuts

XRDB_PATHS = (
    os.path.expanduser('~/.Xresources'),
    os.path.expanduser('~/.Xdefaults'),
)


def xrdb_merge(**opts):
    for fp in XRDB_PATHS:
        with open(fp, 'w') as f:
            for k, v in opts.items():
                f.write(f'{k}: {v}\n')

    if shortcuts.is_x11():
        args = ['xrdb', '-merge', XRDB_PATHS[0]]
        logger.info(' '.join(args))
        subprocess.call(args)
