from libqtile import layout


class RuleMatchMixin(object):
    def configure(self, client, screen_rect):
        super().configure(client, screen_rect)
        client.floating = client.group.floating_layout.match(client)


class Bsp(RuleMatchMixin, layout.Bsp):
    pass


class Max(RuleMatchMixin, layout.Max):
    pass


class MonadTall(RuleMatchMixin, layout.MonadTall):
    pass
