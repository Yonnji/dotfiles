import cairocffi
import configparser
import os
import re

from libqtile import images
from libqtile.log_utils import logger

from ..icon_theme import get_icon_path


def get_subdir_size(subdir):
    if subdir == 'scalable':
        return 1024
    elif 'x' in subdir:
        w, _, h = subdir.partition('x')
        if w.isdigit():
            return int(w)
    return 0


class IconTextMixin(object):
    def _replace_svg_attr(self, match):
        attr = match.group(0)
        color = match.group(1)
        delta = 255

        if re.match(r'#[A-Fa-f0-9]{6}', color):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            delta = max((abs(r - g), abs(r - b), abs(g - b)))

        elif color in ('gray', 'grey', 'black', 'white'):
            delta = 0

        if delta < 32:
            return attr.replace(color, self.foreground)
        return attr

    def setup_images(self):
        d_imgs = {}
        for icon_name in self.icon_names:
            icon = get_icon_path(
                icon_name, size=self.icon_size,
                theme=self.theme_path, extensions=(self.icon_ext.lstrip('.'),))
            if icon:
                if icon.endswith('.svg'):  # symbolic icon
                    with open(icon, 'r') as f:
                        data = re.sub(r'fill="(#?[A-Za-z0-9]+)"', self._replace_svg_attr, f.read())
                        d_imgs[icon_name] = images.Img(data.encode(), icon_name, icon)
                else:
                    with open(icon, 'rb') as f:
                        d_imgs[icon_name] = images.Img(f.read(), icon_name, icon)

        for key, img in d_imgs.items():
            img.resize(height=self.icon_size)
            if img.width > self.length:
                self.length = img.width + self.padding_x * 2
            self.images[key] = img

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)

        image = self.images[self.current_icon]
        self.drawer.ctx.save()
        self.drawer.ctx.translate(self.padding_x, (self.bar.height - image.height) // 2)
        self.drawer.ctx.set_source(image.pattern)
        self.drawer.ctx.paint()
        self.drawer.ctx.restore()

        self.layout.draw(
           self.padding_x + self.icon_size + self.icon_spacing,
           (self.bar.height - self.layout.height) // 2 + 1,
        )

        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.length)


class AppMixin(object):
    def read_desktop_file(self, filepath):
        config = configparser.ConfigParser()

        try:
            with open(os.path.join(filepath), 'r') as f:
                data = f.read().replace('%', '%%')
                config.read_string(data)

        except (configparser.InterpolationSyntaxError, KeyError):
            logger.exception(f'Cannot read file {filepath}:')

        return config

    def get_icons(self, themepath):
        results = []

        for size in reversed(sorted(os.listdir(themepath), key=get_subdir_size)):
            cats = os.path.join(themepath, size)
            if not os.path.isdir(cats):
                continue

            for cat in os.listdir(cats):
                icons = os.path.join(themepath, size, cat)
                if not os.path.isdir(icons):
                    continue

                for icon in os.listdir(icons):
                    iconpath = os.path.join(themepath, size, cat, icon)
                    if not os.path.isfile(iconpath):
                        continue

                    results.append(iconpath)

        return results

    def get_flatpaks(self):
        desktops = []

        flatpaks_path = '/var/lib/flatpak/app'
        if not os.path.isdir(flatpaks_path):
            return []

        for appid in os.listdir(flatpaks_path):
            apps_path = os.path.join(flatpaks_path, appid, 'current/active/files/share/applications')
            if not os.path.isdir(apps_path):
                continue
            for filename in os.listdir(apps_path):
                if not filename.endswith('.desktop'):
                    continue

                if not filename.startswith(appid):
                    continue

                desktop = self.read_desktop_file(os.path.join(apps_path, filename))
                desktops.append((appid, desktop))

        return desktops

    def get_flatpak_icon(self, appid, desktop):
        desktop_icon = desktop['Desktop Entry']['Icon']
        hicolor = os.path.join(
            '/var/lib/flatpak/app', appid,
            'current/active/files/share/icons/hicolor')
        if not os.path.isdir(hicolor):
            return

        for icon_path in self.get_icons(hicolor):
            if not os.path.basename(icon_path).startswith(desktop_icon):
                continue

            # if icon_path.endswith('.svg'):
            #     continue

            surface = self.get_icon_surface(icon_path, self.icon_size)
            return surface

    def get_desktop_files(self):
        desktops = []

        apps_paths = (
            os.path.expanduser('~/.local/share/applications'),
            '/usr/local/share/applications',
            '/usr/share/applications',
        )

        for apps_path in apps_paths:
            if not os.path.isdir(apps_path):
                continue

            for filename in os.listdir(apps_path):
                if not filename.endswith('.desktop'):
                    continue

                filepath = os.path.join(apps_path, filename)
                desktop = self.read_desktop_file(filepath)
                desktops.append((filepath, desktop))

        return desktops

    def get_icon_surface(self, filepath, size):
        icon = images.Img.from_path(filepath)
        img = icon.surface
        surface = cairocffi.SurfacePattern(img)
        height = img.get_height()
        width = img.get_width()
        scaler = cairocffi.Matrix()
        if height != size:
            sp = height / size
            height = size
            width /= sp
            scaler.scale(sp, sp)
        surface.set_matrix(scaler)
        return surface
