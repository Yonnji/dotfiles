from libqtile import layout


class Floating(layout.Floating):
    def __init__(self, *args, **kwargs):
        float_rules_exclude = kwargs.pop('float_rules_exclude', None)
        tiling_rules = kwargs.pop('tiling_rules', None)
        super().__init__(*args, **kwargs)
        self.float_rules_exclude = float_rules_exclude or []
        self.tiling_rules = tiling_rules or []

    def focus(self, client):
        super().focus(client)
        client.bring_to_front()

    def match(self, win):
        return ((
            any(win.match(rule) for rule in self.float_rules) and
            not any(win.match(rule) for rule in self.float_rules_exclude)
        ) or not any(win.match(rule) for rule in self.tiling_rules))
