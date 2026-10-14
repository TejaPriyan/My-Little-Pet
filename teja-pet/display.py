"""Window management and crisp nearest-neighbour presentation.

Everything is drawn to a fixed 480x270 canvas which is scaled to the window.
Keeping this isolated means a borderless / transparent "desktop pet" mode can
later be added here without touching any game logic.
"""
import pygame

from config import W, H, START_SCALE, TITLE


class DisplayManager:
    def __init__(self, fullscreen=False):
        self.fullscreen = fullscreen
        self.windowed_size = (W * START_SCALE, H * START_SCALE)
        self.scale = 1.0
        self.offset = (0, 0)
        self.screen = None
        self._create()

    def _create(self):
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        pygame.display.set_caption(TITLE)

    def set_fullscreen(self, on):
        if on == self.fullscreen:
            return
        self.fullscreen = on
        self._create()

    def on_resize(self, size):
        if not self.fullscreen:
            self.windowed_size = (max(320, size[0]), max(180, size[1]))
        self.screen = pygame.display.get_surface() or self.screen

    def _layout(self):
        sw, sh = self.screen.get_size()
        raw = min(sw / W, sh / H)
        whole = int(raw)
        # integer scaling keeps pixels perfectly square; fall back to fractional
        # scaling only when integer scaling would waste a lot of the window.
        self.scale = whole if whole >= 1 and whole / raw > 0.75 else max(raw, 0.5)
        self.offset = ((sw - int(W * self.scale)) // 2, (sh - int(H * self.scale)) // 2)

    def to_internal(self, pos):
        self._layout()
        return ((pos[0] - self.offset[0]) / self.scale, (pos[1] - self.offset[1]) / self.scale)

    def present(self, canvas):
        self.screen = pygame.display.get_surface() or self.screen
        self._layout()
        size = (int(W * self.scale), int(H * self.scale))
        self.screen.fill((14, 10, 24))
        if size == (W, H):
            self.screen.blit(canvas, self.offset)
        else:
            self.screen.blit(pygame.transform.scale(canvas, size), self.offset)
        pygame.display.flip()

    def enter_overlay_mode(self, scale=3):
        from desktop import DesktopWindow
        return DesktopWindow(scale)

    def restore_room(self):
        self._create()
        # SDL can retain WS_POPUP when leaving NOFRAME on Windows. Explicitly
        # restore the native frame and centre the room inside the work area.
        import os
        if os.name == "nt" and hasattr(pygame.display, "get_wm_info") and not self.fullscreen:
            import ctypes
            from ctypes import wintypes
            api = ctypes.WinDLL("user32", use_last_error=True)
            api.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
            api.GetWindowLongW.restype = wintypes.LONG
            api.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
            api.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                        ctypes.c_int, ctypes.c_int, wintypes.UINT]
            api.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                style = api.GetWindowLongW(hwnd, -16)
                api.SetWindowLongW(hwnd, -16, (style & ~0x80000000) | 0x00CF0000)
                area = wintypes.RECT()
                api.SystemParametersInfoW(0x30, 0, ctypes.byref(area), 0)
                aw, ah = area.right - area.left, area.bottom - area.top
                width = min(self.windowed_size[0], max(320, aw - 80))
                height = min(self.windowed_size[1], max(180, ah - 80))
                api.SetWindowPos(hwnd, -2, area.left + (aw - width) // 2, area.top + (ah - height) // 2,
                                 width, height, 0x20 | 0x40)
        self._layout()
