#!/usr/bin/env python3
import os


def link(target, location):
    path = os.path.dirname(location)
    if not os.path.exists(path):
        os.makedirs(path)

    if os.path.exists(location):
        if os.path.islink(location):
            os.remove(location)
        else:
            raise RuntimeError(f'File "{location}" exists!')

    print(f'{location} -> {target}')
    os.symlink(target, location)


for c in os.listdir('config'):
    target = os.path.abspath(os.path.join('config', c))
    location = os.path.expanduser(os.path.join('~', '.config', c))
    link(target, location)

for s in os.listdir(os.path.join('local', 'share')):
    target = os.path.abspath(os.path.join('local', 'share', s))
    location = os.path.expanduser(os.path.join('~', '.local', 'share', s))
    link(target, location)

for s in os.listdir(os.path.join('local', 'bin')):
    target = os.path.abspath(os.path.join('local', 'bin', s))
    location = os.path.expanduser(os.path.join('~', '.local', 'bin', s))
    link(target, location)
