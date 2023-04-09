from libqtile import layout


class Tiling(layout.Bsp):
    def focus(self, client):
        super().focus(client)
        # client.bring_to_front()
