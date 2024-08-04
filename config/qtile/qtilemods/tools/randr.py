from libqtile.log_utils import logger

import json
import os
import re
import subprocess


ALL_OPTS = (
    'output', 'mode', 'refresh', 'primary',
    'off', 'above', 'below', 'left-of', 'right-of')


def _randr_query(is_x11=False):
    app = 'xrandr' if is_x11 else 'wlr-randr'

    modes = {}
    output = None

    lines = subprocess.check_output([app]).decode()
    for line in lines.split('\n'):
        if line.startswith(' ' if is_x11 else '    '):
            if not output:
                continue

            if output not in modes:
                modes[output] = {}

            if is_x11:
                mode, *refreshes = filter(None, line.strip().split(' '))
                if not re.match(r'\d+x\d+', mode):
                    continue

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
            if 'disconnected' in line:
                continue
            output = line.split(' ')[0]

    return modes


def _get_output(modes, output):
    for output_preset in modes:
        if re.match(r'{}(-[0-9A-Z])+'.format(output), output_preset):
            return output_preset
    return output


def _get_refresh(modes, output, mode, refresh):
    if output in modes:
        if mode in modes[output]:
            for refresh_preset in modes[output][mode]:
                try:
                    if round(float(refresh)) == round(float(refresh_preset)):
                        return refresh_preset
                except ValueError:
                    pass
    return refresh


def randr(**opts):
    is_x11 = opts.pop('is_x11', False)
    app = 'xrandr' if is_x11 else 'wlr-randr'

    modes = _randr_query(is_x11=is_x11)
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
            if not is_x11:
                continue
            value = refresh

        elif key == 'mode':
            value = mode
            if not is_x11 and refresh:
                value = f'{value}@{refresh}'

        elif key in ('above', 'below', 'left-of', 'right-of'):
            if is_x11:
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
