import pygame as pg
import moderngl as mgl
import numpy as np
from settings import *


# colors for each block type (R, G, B) — used as simple icons in hotbar slots
BLOCK_COLORS = {
    SAND:   (237, 201, 142),
    GRASS:  (89,  166, 60),
    DIRT:   (134, 96,  67),
    STONE:  (136, 136, 136),
    SNOW:   (240, 240, 255),
    LEAVES: (56,  118, 29),
    WOOD:   (101, 67,  33),
}


class HotBar:
    """Renders a Minecraft-style 9-slot hotbar and centre crosshair."""

    SLOT_SIZE = 44           # pixels per slot (square)
    SLOT_GAP = 4             # gap between slots
    BORDER = 3               # selection border thickness
    BAR_PADDING = 6          # padding inside the bar background
    BOTTOM_MARGIN = 40       # pixels above the screen bottom

    CROSS_SIZE = 24          # crosshair total size in pixels
    CROSS_THICK = 2          # crosshair line thickness

    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx

        # shared shader
        self.program = self._load_shader()

        # hotbar
        self.hotbar_vao = self._build_hotbar_quad()
        self.hotbar_tex = None

        # crosshair
        self.crosshair_vao = self._build_crosshair_quad()
        self.crosshair_tex = self._build_crosshair_texture()

        # font (created once)
        self.font = pg.font.SysFont(None, 18)

        self._rebuild_hotbar_texture()

    def _load_shader(self):
        with open('shaders/hotbar.vert') as f:
            vert = f.read()
        with open('shaders/hotbar.frag') as f:
            frag = f.read()
        return self.ctx.program(vertex_shader=vert, fragment_shader=frag)

    # ------------------------------------------------------------------ #
    #  Crosshair                                                           #
    # ------------------------------------------------------------------ #
    def _build_crosshair_quad(self):
        w, h = int(WIN_RES.x), int(WIN_RES.y)
        s = self.CROSS_SIZE
        # NDC for a small quad centred on screen
        hw = s / w
        hh = s / h
        x0, x1 = -hw, hw
        y0, y1 = -hh, hh

        verts = np.array([
            x0, y1, 0.0, 0.0,
            x1, y1, 1.0, 0.0,
            x0, y0, 0.0, 1.0,
            x1, y0, 1.0, 1.0,
        ], dtype='f4')
        vbo = self.ctx.buffer(verts)
        return self.ctx.vertex_array(self.program, [(vbo, '2f 2f', 'in_position', 'in_texcoord')])

    def _build_crosshair_texture(self):
        s = self.CROSS_SIZE
        t = self.CROSS_THICK
        surf = pg.Surface((s, s), pg.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        mid = s // 2
        # horizontal bar
        pg.draw.rect(surf, (255, 255, 255, 200),
                     (0, mid - t // 2, s, t))
        # vertical bar
        pg.draw.rect(surf, (255, 255, 255, 200),
                     (mid - t // 2, 0, t, s))
        # dark outline for contrast
        pg.draw.rect(surf, (0, 0, 0, 100),
                     (0, mid - t // 2 - 1, s, 1))
        pg.draw.rect(surf, (0, 0, 0, 100),
                     (0, mid + t // 2, s, 1))
        pg.draw.rect(surf, (0, 0, 0, 100),
                     (mid - t // 2 - 1, 0, 1, s))
        pg.draw.rect(surf, (0, 0, 0, 100),
                     (mid + t // 2, 0, 1, s))

        raw = pg.image.tostring(surf, 'RGBA', True)
        tex = self.ctx.texture((s, s), 4, raw)
        tex.filter = (mgl.NEAREST, mgl.NEAREST)
        return tex

    # ------------------------------------------------------------------ #
    #  Hotbar                                                              #
    # ------------------------------------------------------------------ #
    def _build_hotbar_quad(self):
        total_w = 9 * self.SLOT_SIZE + 8 * self.SLOT_GAP + 2 * self.BAR_PADDING
        total_h = self.SLOT_SIZE + 2 * self.BAR_PADDING

        w, h = int(WIN_RES.x), int(WIN_RES.y)

        x0 = (w / 2 - total_w / 2) / w * 2.0 - 1.0
        x1 = (w / 2 + total_w / 2) / w * 2.0 - 1.0
        y0 = -1.0 + self.BOTTOM_MARGIN / h * 2.0
        y1 = y0 + total_h / h * 2.0

        verts = np.array([
            x0, y1, 0.0, 0.0,
            x1, y1, 1.0, 0.0,
            x0, y0, 0.0, 1.0,
            x1, y0, 1.0, 1.0,
        ], dtype='f4')
        vbo = self.ctx.buffer(verts)
        return self.ctx.vertex_array(self.program, [(vbo, '2f 2f', 'in_position', 'in_texcoord')])

    def _rebuild_hotbar_texture(self):
        selected = self.app.player.selected_slot

        total_w = 9 * self.SLOT_SIZE + 8 * self.SLOT_GAP + 2 * self.BAR_PADDING
        total_h = self.SLOT_SIZE + 2 * self.BAR_PADDING

        surf = pg.Surface((total_w, total_h), pg.SRCALPHA)
        surf.fill((0, 0, 0, 0))

        # dark background bar
        pg.draw.rect(surf, (30, 30, 30, 180), (0, 0, total_w, total_h), border_radius=6)

        for i in range(9):
            x = self.BAR_PADDING + i * (self.SLOT_SIZE + self.SLOT_GAP)
            y = self.BAR_PADDING

            # slot background (perfect square)
            bg = (120, 120, 120, 220) if i == selected else (60, 60, 60, 200)
            pg.draw.rect(surf, bg, (x, y, self.SLOT_SIZE, self.SLOT_SIZE), border_radius=4)

            # selection border
            if i == selected:
                pg.draw.rect(surf, (255, 255, 255, 255),
                             (x - self.BORDER, y - self.BORDER,
                              self.SLOT_SIZE + 2 * self.BORDER,
                              self.SLOT_SIZE + 2 * self.BORDER),
                             width=self.BORDER, border_radius=5)

            # block color icon (centred, square)
            block_id = HOTBAR_BLOCKS[i]
            color = BLOCK_COLORS.get(block_id, (128, 128, 128))
            icon_size = self.SLOT_SIZE - 14
            icon_x = x + (self.SLOT_SIZE - icon_size) // 2
            icon_y = y + (self.SLOT_SIZE - icon_size) // 2
            pg.draw.rect(surf, color, (icon_x, icon_y, icon_size, icon_size), border_radius=3)

            # subtle bevel highlight
            pg.draw.line(surf, (255, 255, 255, 60),
                         (icon_x, icon_y), (icon_x + icon_size - 1, icon_y))
            pg.draw.line(surf, (255, 255, 255, 60),
                         (icon_x, icon_y), (icon_x, icon_y + icon_size - 1))

            # slot number label
            num_surf = self.font.render(str(i + 1), True, (200, 200, 200))
            surf.blit(num_surf, (x + 3, y + 2))

        raw = pg.image.tostring(surf, 'RGBA', True)
        if self.hotbar_tex:
            self.hotbar_tex.release()
        self.hotbar_tex = self.ctx.texture((total_w, total_h), 4, raw)
        self.hotbar_tex.filter = (mgl.NEAREST, mgl.NEAREST)

    # ------------------------------------------------------------------ #
    #  Update / Render                                                     #
    # ------------------------------------------------------------------ #
    def update(self):
        self._rebuild_hotbar_texture()

    def render(self):
        self.ctx.disable(mgl.DEPTH_TEST | mgl.CULL_FACE)
        self.ctx.enable(mgl.BLEND)

        # draw crosshair
        self.crosshair_tex.use(location=5)
        self.program['u_texture'] = 5
        self.crosshair_vao.render(mgl.TRIANGLE_STRIP)

        # draw hotbar
        self.hotbar_tex.use(location=5)
        self.program['u_texture'] = 5
        self.hotbar_vao.render(mgl.TRIANGLE_STRIP)

        # restore
        self.ctx.enable(mgl.DEPTH_TEST | mgl.CULL_FACE)
