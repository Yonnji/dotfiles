import copy

from libqtile import widget
from libqtile.widget import base

from .mixins import IconTextMixin


class Workspaces(IconTextMixin, widget.GroupBox):
    layout_icons = {
        'bsp': 'view-grid-symbolic',
        'columns': 'view-grid-symbolic',
        'floating': 'multiple-events-symbolic',
        'matrix': 'view-app-grid-symbolic',
        'max': 'window-symbolic',
        'monadtall': 'sidebar-show-right-symbolic',
        'monadthreecol': 'sidebar-show-symbolic',
        'monadwide': 'open-menu-symbolic',
        'ratiotile': 'view-restore-symbolic',
        'slice': 'sidebar-show-right-symbolic',
        'spiral': 'object-rotate-right-symbolic',
        'stack': 'multiple-events-symbolic',
        'tile': 'view-grid-symbolic',
        'treetab': 'view-list-bullet-symbolic',
        'verticaltile': 'open-menu-symbolic',
        'zoomy': 'zoom-fit-best-symbolic',
        # custom
        'stacking': 'multiple-events-symbolic',
        'unmanaged': 'multiple-events-symbolic',
        'tiling': 'view-grid-symbolic',
    }

    def __init__(self, **config):
        self.theme_path = config.get('theme_path', None)
        self.icon_ext = config.get('icon_ext', '.png')
        self.icon_size = config.get('icon_size', 0)
        self.icon_spacing = config.get('icon_spacing', 0)
        self.icon_names = tuple(set(self.layout_icons.values()))
        self.images = {}
        self._length = 0
        super().__init__(**config)
        self.foreground = self.active

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        self.setup_images()
        self.images_default = copy.copy(self.images)

        foreground = self.foreground
        self.foreground = self.inactive
        self.setup_images()
        self.foreground = foreground

    def box_width(self, groups):
        return (
            super().box_width(groups) +
            (self.icon_size + self.icon_spacing) * len(groups))

    def drawbox(self, offset, text, bordercolor, textcolor,
                highlight_color=None, width=None, rounded=False, highlighted=False,
                layout=None, active=True):
        self.layout.text = self.fmt.format(text)
        self.layout.font_family = self.font
        self.layout.font_size = self.fontsize
        self.layout.colour = textcolor
        # if width is not None:
        #     self.layout.width = width

        framecolor = bordercolor or self.background or self.bar.background
        framed = self.layout.framed(0, framecolor, self.padding_x, self.padding_y, highlight_color)
        framed.pad_left += self.icon_size + self.icon_spacing
        y = (self.bar.height - framed.height) // 2
        if bordercolor:
            framed.draw_fill(offset, y, rounded)
        else:
            framed.draw(offset, y, rounded)

        if layout in self.layout_icons:
            icon_name = self.layout_icons[layout]
            if active:
                icon = self.images_default[icon_name]
            else:
                icon = self.images[icon_name]
            self.draw_icon(icon.pattern, offset)

    def draw_icon(self, surface, offset):
        if not surface:
            return

        self.drawer.ctx.save()
        self.drawer.ctx.translate(offset + self.padding_x, (self.bar.height - self.icon_size) // 2)
        self.drawer.ctx.set_source(surface)
        self.drawer.ctx.paint()
        self.drawer.ctx.restore()

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)

        offset = self.margin_x
        for i, g in enumerate(self.groups):
            bw = self.box_width([g])
            text_color = self.active if g.windows else self.inactive

            if g.screen:
                # text_color = self.block_highlight_text_color
                if self.bar.screen.group.name == g.name:  # this screen
                    if self.qtile.current_screen == self.bar.screen:  # this screen is active
                        border = self.this_current_screen_border
                    else:
                        border = self.this_screen_border
                else:  # other screen
                    if self.qtile.current_screen == g.screen:  # other screen is active
                        border = self.other_current_screen_border
                    else:
                        border = self.other_screen_border

            elif self.group_has_urgent(g):
                text_color = self.block_highlight_text_color
                border = self.urgent_border
            else:
                border = None

            self.drawbox(
                offset,
                g.name,
                border,
                text_color,
                width=bw,
                rounded=self.rounded,
                layout=g.layout.name,
                active=bool(g.windows),
            )
            offset += bw + self.spacing

        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.width)
