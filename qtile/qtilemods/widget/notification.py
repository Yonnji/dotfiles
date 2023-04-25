from libqtile import bar, pangocffi
from libqtile.command.base import expose_command
from libqtile.log_utils import logger
from libqtile.notify import ClosedReason, notifier
from libqtile.widget import base


class Notification(base.PaddingMixin, base.MarginMixin, base._TextBox):
    def __init__(self, **config):
        base._TextBox.__init__(self, **config)
        self.add_defaults(base.PaddingMixin.defaults)
        self.add_defaults(base.MarginMixin.defaults)

        self.background = config.get('background', '#000000')
        self.selected = config.get('selected', '#ffffff')
        self.rounded = config.get('rounded', True)
        self.size = config.get('size', 64)
        self.borderwidth = config.get('borderwidth', 2)
        self.timeout = config.get('timeout', 2)
        self.timeout_id = None
        self.text = ''
        self.text_length = config.get('text_length', 32)
        self.value = None

    def _configure(self, qtile, pbar):
        base._TextBox._configure(self, qtile, pbar)

    async def _config_async(self):
        if notifier is None:
            return

        await notifier.register(self.on_notification, {'body'}, on_close=self.on_close)

    def on_notification(self, notification):
        logger.warning(notification)
        logger.warning(notification.id)
        logger.warning(notification.app_name)
        logger.warning(notification.body)
        if 'sender-pid' in notification.hints:
            logger.warning(notification.hints.get('sender-pid').value)
        if 'desktop-entry' in notification.hints:
            logger.warning(notification.hints.get('desktop-entry').value)

        text = pangocffi.markup_escape_text(notification.body or notification.summary)
        self.qtile.call_soon_threadsafe(self.update, text)

    def on_close(self, notification_id):
        pass

    def clear(self, *args):
        self.text = ''
        self.value = None
        self.bar.draw()

    @expose_command()
    def update(self, text, value=None):
        if value is None:
            self.value = None
        else:
            self.value = min(max(value, 0), 1)

        if len(text) > self.text_length:
            text = text[:self.text_length - 3] + '...'
        base._TextBox.update(self, text)

        if self.timeout_id:
            self.timeout_id.cancel()
            self.timeout_id = None
        self.timeout_id = self.timeout_add(self.timeout, self.clear)

    def calculate_length(self):
        if self.text:
            if self.value is None:
                return self.layout.width + self.padding_x * 2 + self.margin_x * 2
            else:
                return self.size + self.padding_x * 2 + self.margin_x * 2
        else:
            return 0

    def drawbox(self, offset, text, bordercolor, textcolor, width=None, rounded=False):
        self.layout.text = self.fmt.format(text)
        self.layout.font_family = self.font
        self.layout.font_size = self.fontsize
        self.layout.colour = textcolor

        framed = self.layout.framed(0, bordercolor, 0, self.padding_y, textcolor)
        text_x = offset
        text_y = (self.bar.height - framed.height) // 2

        rect_x = text_x
        rect_y = text_y

        if self.value is None:
            rect_w = framed.width + self.padding_x * 2
            rect_h = framed.height
            text_x += self.padding_x
        else:
            rect_w = self.size + self.padding_x * 2
            rect_h = self.padding_y * 2
            text_x += self.size - framed.width + self.padding_x * 2
            rect_y += framed.height - rect_h

        self.drawer.set_source_rgb(bordercolor or self.bar.background)
        self.drawer.rounded_fillrect(rect_x, rect_y, rect_w, rect_h, self.borderwidth)
        if self.value:
            self.drawer.set_source_rgb(self.selected or self.bar.background)
            self.drawer.rounded_fillrect(rect_x, rect_y, rect_w * self.value, rect_h, self.borderwidth)

        framed.draw(text_x, text_y, rounded)

    def draw(self):
        self.drawer.clear(self.bar.background)

        self.drawbox(
            self.margin_x,
            self.text,
            self.background,
            self.background if self.value is not None else self.foreground,
            rounded=self.rounded,
        )
        self.drawer.draw(offsetx=self.offset, offsety=self.offsety, width=self.width)

    def finalize(self):
        notifier.unregister(self.update)
        super().finalize()
