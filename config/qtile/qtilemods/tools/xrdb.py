import os
import subprocess

from libqtile.log_utils import logger

XRESOURCES_PATH = os.path.expanduser('~/.Xresources')


def xrdb_merge(**opts):
    with open(XRESOURCES_PATH, 'w') as f:
        for k, v in opts.items():
            f.write(f'{k}: {v}\n')
    args = ['xrdb', '-merge', XRESOURCES_PATH]
    logger.info(' '.join(args))
    subprocess.call(args)
