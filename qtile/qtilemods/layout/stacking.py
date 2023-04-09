from libqtile import layout


class Stacking(layout.Floating):
    # def match(self, win):
    #     return True

    def focus(self, client):
        super().focus(client)
        # if self.focused.floating:
        self.focused.bring_to_front()

    def configure(self, client, screen_rect):
        if client.has_focus:
            bc = self.border_focus
        else:
            bc = self.border_normal

        if client.maximized:
            bw = self.max_border_width
        elif client.fullscreen:
            bw = self.fullscreen_border_width
        else:
            bw = self.border_width

        # 'sun-awt-X11-XWindowPeer' is a dropdown used in Java application,
        # don't reposition it anywhere, let Java app to control it
        cls = client.get_wm_class() or ""
        is_java_dropdown = "sun-awt-X11-XWindowPeer" in cls
        if is_java_dropdown:
            client.paint_borders(bc, bw)
            client.bring_to_front()

        # alternatively, users may have asked us explicitly to leave the client alone
        elif any(m.compare(client) for m in self.no_reposition_rules):
            client.paint_borders(bc, bw)
            client.bring_to_front()

        else:
            above = False

            # We definitely have a screen here, so let's be sure we'll float on screen
            if client.float_x is None or client.float_y is None:
                # this window hasn't been placed before, let's put it in a sensible spot
                above = self.compute_client_position(client, screen_rect)

            # if not client.maximized and not client.fullscreen:
            #     if client.tiled_x is not None and client.tiled_y is not None:
            #         client.x = client.tiled_x
            #         client.y = client.tiled_y
            #         client.width = client.tiled_width
            #         client.height = client.tiled_height
            #         client.tiled_x = None
            #         client.tiled_y = None

            client.place(
                client.x,
                client.y,
                client.width,
                client.height,
                bw,
                bc,
                above,
                respect_hints=True,
            )
        client.unhide()
