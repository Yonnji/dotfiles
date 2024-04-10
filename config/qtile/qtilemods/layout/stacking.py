from libqtile import layout


class Stacking(layout.Floating):
    def focus(self, client):
        super().focus(client)
        client.bring_to_front()


class Unmanaged(layout.Floating):
    def configure(self, client, screen_rect):
        super().configure(client, screen_rect)
        client.floating = True
