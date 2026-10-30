"""Windows colour-key desktop companion. Transparent pixels pass clicks through.

Only this application's own HWND is changed. No global hooks or input capture.
Win32 reference: https://learn.microsoft.com/windows/win32/winmsg/window-features
"""
import ctypes
from ctypes import wintypes
import math
import os
import random

import pygame
from config import DESKTOP_KEY, GOLD, INK, WAKE_ENERGY


class DesktopWindow:
    def __init__(self, scale):
        if os.name != "nt":
            raise OSError("Desktop mode is available on Windows.")
        self.scale = scale
        self.api = ctypes.WinDLL("user32", use_last_error=True)
        self.api.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        self.api.GetWindowLongW.restype = wintypes.LONG
        self.api.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
        self.api.SetWindowLongW.restype = wintypes.LONG
        self.api.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.DWORD, wintypes.BYTE, wintypes.DWORD]
        self.api.SetLayeredWindowAttributes.restype = wintypes.BOOL
        self.api.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        self.api.SetWindowPos.restype = wintypes.BOOL
        self.api.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
        self.api.GetCursorPos.restype = wintypes.BOOL
        self.api.SetCapture.argtypes = [wintypes.HWND]
        self.api.SetCapture.restype = wintypes.HWND
        self.api.ReleaseCapture.argtypes = []
        self.api.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]
        area = wintypes.RECT()
        if not self.api.SystemParametersInfoW(0x30, 0, ctypes.byref(area), 0):
            raise ctypes.WinError(ctypes.get_last_error())
        self.origin = area.left, area.top
        self.size = area.right - area.left, area.bottom - area.top
        self.surface = pygame.display.set_mode(self.size, pygame.NOFRAME)
        pygame.display.set_caption("TEJA PET - Desktop")
        self.hwnd = pygame.display.get_wm_info()["window"]
        style = self.api.GetWindowLongW(self.hwnd, -20)
        ctypes.set_last_error(0)
        self.api.SetWindowLongW(self.hwnd, -20, style | 0x80000)  # WS_EX_LAYERED
        if ctypes.get_last_error():
            raise ctypes.WinError(ctypes.get_last_error())
        key = DESKTOP_KEY[0] | DESKTOP_KEY[1] << 8 | DESKTOP_KEY[2] << 16
        if not self.api.SetLayeredWindowAttributes(self.hwnd, key, 255, 1):
            raise ctypes.WinError(ctypes.get_last_error())
        if not self.api.SetWindowPos(self.hwnd, -1, *self.origin, *self.size, 0x10 | 0x40):
            raise ctypes.WinError(ctypes.get_last_error())
        self.canvas = pygame.Surface((self.size[0] // scale, self.size[1] // scale))
        self.ui_canvas = pygame.Surface(self.canvas.get_size())
        self.ui_canvas.set_colorkey(DESKTOP_KEY)
        from desktop_render import DesktopRenderer
        self.renderer = DesktopRenderer()
        self.pets, self.assets, self.pet_scale = [], None, 3
        self.surface.fill(DESKTOP_KEY)
        pygame.display.flip()

    def mouse(self):
        point = wintypes.POINT()
        if self.api.GetCursorPos(ctypes.byref(point)):
            return ((point.x - self.origin[0]) / self.scale, (point.y - self.origin[1]) / self.scale)
        return pygame.mouse.get_pos()[0] / self.scale, pygame.mouse.get_pos()[1] / self.scale

    def present(self):
        self.surface.fill(DESKTOP_KEY)
        self.surface.blit(pygame.transform.scale(self.canvas, (self.canvas.get_width() * self.scale,
                                                              self.canvas.get_height() * self.scale)), (0, 0))
        if self.assets is not None:
            self.renderer.draw(self.surface, self.pets, self.assets, self.scale, self.pet_scale)
        self.surface.blit(pygame.transform.scale(self.ui_canvas, (self.canvas.get_width() * self.scale,
                                                                 self.canvas.get_height() * self.scale)), (0, 0))
        pygame.display.flip()

    def capture(self, on):
        if on: self.api.SetCapture(self.hwnd)
        else: self.api.ReleaseCapture()

    def show(self):
        self.api.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        self.api.ShowWindow.restype = wintypes.BOOL
        self.api.ShowWindow(self.hwnd, 9)
        self.api.SetWindowPos(self.hwnd, -1, *self.origin, *self.size, 0x10 | 0x40)

    def area_changed(self):
        area = wintypes.RECT()
        if not self.api.SystemParametersInfoW(0x30, 0, ctypes.byref(area), 0): return False
        return self.origin != (area.left, area.top) or self.size != (area.right - area.left, area.bottom - area.top)

    def close(self):
        # Remove topmost/layering before SDL restores the ordinary room window.
        style = self.api.GetWindowLongW(self.hwnd, -20)
        self.api.SetWindowLongW(self.hwnd, -20, style & ~0x80000)
        self.api.SetWindowPos(self.hwnd, -2, 0, 0, 0, 0, 0x01 | 0x02 | 0x10)


from desktop_pet import DesktopPet
