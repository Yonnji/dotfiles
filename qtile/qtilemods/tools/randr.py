from libqtile.log_utils import logger

import json
import os
import subprocess


IS_X11 = os.getenv('XDG_SESSION_TYPE').lower() == 'x11'
ALL_OPTS = (
    'output', 'mode', 'refresh', 'primary',
    'off', 'above', 'below', 'left-of', 'right-of')


def _randr_query():
    app = 'xrandr' if IS_X11 else 'wlr-randr'

    modes = {}
    output = None

    lines = subprocess.check_output([app]).decode()
    for line in lines.split('\n'):
        if line.startswith(' ' if IS_X11 else '    '):
            if not output:
                continue

            if output not in modes:
                modes[output] = {}

            if IS_X11:
                mode, *refreshes = filter(None, line.split(' '))
                for refresh in refreshes:
                    if mode not in modes[output]:
                        modes[output][mode] = []

                    refresh = refresh.replace('*', '').replace('+', '')
                    if not refresh:
                        continue

                    modes[output][mode].append(refresh)

            else:
                mode, px, refresh, *_ = filter(None, line.split(' '))
                if mode not in modes[output]:
                    modes[output][mode] = []
                modes[output][mode].append(refresh)

        elif line.startswith('Screen'):
            continue

        else:
            output = line.split(' ')[0]

    return modes


def _get_output(modes, output):
    for output_preset in modes:
        if output in output_preset:
            return output_preset
    return output


def _get_refresh(modes, output, mode, refresh):
    if output in modes:
        if mode in modes[output]:
            for refresh_preset in modes[output][mode]:
                if round(float(refresh)) == round(float(refresh_preset)):
                    return refresh_preset
    return refresh


def randr(**opts):
    app = 'xrandr' if IS_X11 else 'wlr-randr'

    modes = _randr_query()
    logger.error(json.dumps(modes, indent=4))

    output = _get_output(modes, opts.get('output'))
    mode = (opts.get('mode') or '0x0')
    width, _, height = mode.partition('x')
    refresh = _get_refresh(modes, output, mode, opts.get('refresh'))

    args = [app]
    for key in ALL_OPTS:
        if key not in opts:
            continue

        value = opts[key]

        if key == 'output':
            value = output

        elif key == 'refresh':
            if not IS_X11:
                continue
            value = refresh

        elif key == 'mode':
            value = mode
            if not IS_X11 and refresh:
                value = f'{value}@{refresh}'

        elif key in ('above', 'below', 'left-of', 'right-of'):
            if IS_X11:
                value = _get_output(modes, value)
            else:
                if key == 'above':
                    value = f'0,-{height}'
                elif key == 'below':
                    value = f'0,{height}'
                elif key == 'left-of':
                    value = f'-{width},0'
                elif key == 'right-of':
                    value = f'{width},0'
                key = 'pos'

        if value is True:
            args += [f'--{key}']
        else:
            args += [f'--{key}', value]

    logger.error(' '.join(args))
    subprocess.call(args)
