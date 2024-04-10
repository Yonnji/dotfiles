import os
import subprocess

XRESOURCES_PATH = os.path.expanduser('~/.Xresources')


def xrdb_merge(**opts):
    with open(XRESOURCES_PATH, 'w') as f:
        for k, v in opts.items():
            f.write(f'{k}: {v}\n')
        subprocess.call(['xrdb', '-merge', XRESOURCES_PATH])
