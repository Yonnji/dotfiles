import cairocffi
import copy
import re
import os

from xdg.IconTheme import getIconPath

from libqtile import bar, widget, images, qtile
from libqtile.log_utils import logger
from libqtile.notify import ClosedReason, notifier
from libqtile.widget import base

from .mixins import AppMixin, IconTextMixin
from ..icon_theme import get_icon_path


class App(object):
    cmd = None
    window = None


class PinnedApp(App):
    def __init__(self, desktop, icon, cmd):
        self.desktop = desktop
        self.icon = icon
        self.cmd = cmd

    def clone(self):
        return PinnedApp(desktop=self.desktop, icon=self.icon, cmd=self.cmd)

    def matches_window(self, window):
        win_classes = window.get_wm_class() or []

        if self.get_name() == window.name:
            return True

        if self.get_wm_class() and self.get_wm_class() in win_classes:
            return True

        for cl in win_classes:
            if self.get_name().lower().startswith(cl.lower()):
                return True

            if self.get_icon().lower().startswith(cl.lower()):
                return True

        return False

    def get_name(self):
        return self.desktop['Desktop Entry']['Name']

    def get_icon(self):
        return self.desktop['Desktop Entry']['Icon']

    def get_wm_class(self):
        if 'StartupWMClass' in self.desktop['Desktop Entry']:
            return self.desktop['Desktop Entry']['StartupWMClass']


class UnpinnedApp(App):
    def __init__(self, window):
        self.window = window


class Dock(IconTextMixin, AppMixin, widget.TaskList):
    def __init__(self, **config):
        base._Widget.__init__(self, bar.STRETCH, **config)
        self.add_defaults(widget.TaskList.defaults)
        self.add_defaults(base.PaddingMixin.defaults)
        self.add_defaults(base.MarginMixin.defaults)
        self._notifications = {}
        self._icons_cache = {}
        self._box_end_positions = []
        self.markup = False
        self.clicked = None
        if self.spacing is None:
            self.spacing = self.margin_x

        self.add_callbacks({'Button1': lambda: self.select_window()})
        self.add_callbacks({'Button2': lambda: self.select_window(run=True)})
        self.add_callbacks({'Button3': lambda: self.select_window(run=True)})

        self._fallback_icon = None
        icon = get_icon_path(
            'application-x-executable',
            size=self.icon_size, theme=self.theme_path)
        if icon:
            self._fallback_icon = self.get_icon_surface(icon, self.icon_size)

        self.other_border = config.get('other_border', self.border)

        self.pinned = []
        flatpaks = dict(self.get_flatpaks())
        for pinned_name in config.get('pinned_apps', []):
            if pinned_name in flatpaks:
                desktop = flatpaks[pinned_name]
                surface = self.get_flatpak_icon(pinned_name, desktop)
                if surface:
                    app = PinnedApp(
                        desktop=desktop, icon=surface,
                        cmd=f'flatpak run {pinned_name}')
                    self.pinned.append(app)

            else:
                for desktop_path, desktop in self.get_desktop_files():
                    if os.path.basename(desktop_path) != f'{pinned_name}.desktop':
                        continue

                    icon = get_icon_path(
                        desktop['Desktop Entry']['Icon'], size=self.icon_size,
                        theme=self.theme_path)
                    if icon:
                        cmd = desktop['Desktop Entry']['Exec']
                        cmd = re.sub(r'%[A-Za-z]', '', cmd)
                        surface = self.get_icon_surface(icon, self.icon_size)
                        app = PinnedApp(desktop=desktop, icon=surface, cmd=cmd)
                        self.pinned.append(app)

                    break

    async def _config_async(self):
        if notifier is None:
            return

        await notifier.register(self.on_notification, set(), on_close=self.on_close)

    def on_notification(self, notification):
        pid = -1
        name = None
        if 'sender-pid' in notification.hints:
            pid = notification.hints['sender-pid'].value
        if 'desktop-entry' in notification.hints:
            name = notification.hints['desktop-entry'].value

        window = None
        for app in self.windows:
            if app.window:
                if app.window.get_pid() == pid:
                    window = app.window
                    break

                if app.window.name == name:
                    window = app.window
                    break

                for cl in (app.window.get_wm_class() or []):
                    if cl == name:
                        window = app.window
                        break

        if window:
            if window not in self._notifications:
                self._notifications[window] = 0
            self._notifications[window] += 1

        # logger.warning(notification)
        # logger.warning(notification.id)
        # logger.warning(notification.app_name)
        # logger.warning(notification.body)
        # logger.warning(notification.hints.get('sender-pid'))
        # self.qtile.call_soon_threadsafe(self.update, notification)

    def on_close(self, notification_id):
        pass

    def box_width(self, text):
        return 0

    def get_taskname(self, app):
        if app.window:
            if app.window in self._notifications:
                return str(self._notifications[app.window])

    def calc_box_widths(self):
        apps = self.windows
        if not apps:
            return []

        icons = [self.get_window_icon(app) for app in apps]
        names = [self.get_taskname(app) for app in apps]
        width_boxes = [(self.icon_size + self.padding_x) for icon in icons]
        return zip(apps, icons, names, width_boxes)

    @property
    def windows(self):
        pinned_apps = [app.clone() for app in self.pinned]
        unpinned_apps = []

        for group in self.qtile.groups:
            for window in group.windows:
                for i, app in enumerate(pinned_apps):
                    if app.matches_window(window):
                        if app.window:
                            app = app.clone()
                            pinned_apps.insert(i + 1, app)
                        app.window = window
                        break
                else:
                    unpinned_apps.append(UnpinnedApp(window))

        return pinned_apps + unpinned_apps

    def select_window(self, run=False):
        if self.clicked:
            app = self.clicked
            w = app.window
            self._notifications.pop(w, None)

            if (run and app.cmd) or not w:
                qtile.spawn(app.cmd)
                return

            if w is w.group.current_window and self.bar.screen.group.name == w.group.name:
                # if not w.minimized:
                #     w.minimized = True
                w.toggle_minimize()

            else:
                for i, screen in enumerate(qtile.screens):
                    if screen == w.group.screen:
                        qtile.focus_screen(i)
                        break
                w.group.toscreen()
                w.group.focus(w, False)

                if w.minimized:
                    w.minimized = False
                if w.floating:
                    w.bring_to_front()

    def get_window_icon(self, app):
        if isinstance(app, PinnedApp):
            return app.icon

        w = app.window
        icon = super().get_window_icon(w)
        if icon:
            return icon

        for cl in w.get_wm_class() or []:
            for appid, desktop in self.get_flatpaks():
                name = desktop['Desktop Entry']['Name']
                wmclass = desktop['Desktop Entry'].get('StartupWMClass')
                if cl.lower() == name.lower() or cl.lower() == wmclass:
                    icon = desktop['Desktop Entry']['Icon']
                    surface = self.get_flatpak_icon(appid, desktop)
                    if surface:
                        self._icons_cache[w.wid] = surface
                        return surface

            for desktop_path, desktop in self.get_desktop_files():
                name = desktop['Desktop Entry']['Name']
                wmclass = desktop['Desktop Entry'].get('StartupWMClass')
                if cl.lower() == name.lower() or cl.lower() == wmclass:
                    icon = desktop['Desktop Entry']['Icon']
                    surface = self.get_icon_surface(icon, self.icon_size)
                    if surface:
                        self._icons_cache[w.wid] = surface
                        return surface

        return self._fallback_icon

    def drawbox(self, offset, text, bordercolor, textcolor, width=None, rounded=False,
                block=False, icon=None):
        self.drawer.set_source_rgb(bordercolor or self.background or self.bar.background)

        x = offset
        y = (self.bar.height - (self.icon_size + self.padding_y * 2)) // 2
        w = self.icon_size + self.padding_x * 2
        h = self.icon_size + self.padding_y * 2

        if not block:
            x += w // 4
            y = 0
            w = w // 2
            h = self.padding_y

        if bordercolor:
            if rounded:
                self.drawer.rounded_fillrect(x, y, w, h, self.borderwidth)
            else:
                self.drawer.fillrect(x, y, w, h, self.borderwidth)

        if icon:
            self.draw_icon(icon, offset)

        if text:
            self.layout.text = text
            framed = self.layout.framed(self.borderwidth, self.urgent_border, self.padding_x, self.padding_y / 2, textcolor)
            framed.draw_fill(offset, self.padding_y * 2 + self.icon_size - framed.height, rounded)

    def draw_icon(self, surface, offset):
        if not surface:
            return

        self.drawer.ctx.save()
        self.drawer.ctx.translate(offset + self.padding, (self.bar.height - self.icon_size) // 2)
        self.drawer.ctx.set_source(surface)
        self.drawer.ctx.paint()
        self.drawer.ctx.restore()

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)
        offset = self.margin_x

        self._box_end_positions = []
        for app, icon, task, bw in self.calc_box_widths():
            self._box_end_positions.append(offset + bw)
            border = self.unfocused_border or None

            w = app.window
            if w:
                if w.urgent:
                    border = self.urgent_border
                elif w is w.group.current_window:
                    if self.bar.screen.group.name == w.group.name and self.qtile.current_screen == self.bar.screen:
                        border = self.border
                    elif self.qtile.current_screen == w.group.screen:
                        border = self.other_border
            else:
                border = None

            textwidth = (
                bw - 2 * self.padding_x - ((self.icon_size + self.padding_x) if icon else 0)
            )
            self.drawbox(
                offset,
                task,
                border,
                border,
                rounded=self.rounded,
                block=self.highlight_method == 'block',
                width=textwidth,
                icon=icon,
            )
            offset += bw + self.spacing

        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.width)
