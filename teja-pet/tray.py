"""An optional Windows notification icon. Only owns this app's hidden window.

API reference: https://learn.microsoft.com/windows/win32/shell/notification-area
"""
import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path


class Tray:
    ACTIONS = (("rescue", "Bring my pets back"), ("showhome", "Show house"),
               ("showitems", "Show desktop items"), ("showpets", "Show pets"),
               ("showall", "Show everything"), ("hideall", "Hide everything (keep Pet Menu)"),
               ("quiet", "Quiet time on / off"), ("pause", "Pause / resume"),
               ("room", "Open pet room"), ("quit", "Save and quit"))

    def __init__(self, handler):
        if os.name != "nt": raise OSError("Windows notification area only")
        self.handler, self.pending = handler, []
        self.u, self.s, self.k = C.WinDLL("user32"), C.WinDLL("shell32"), C.WinDLL("kernel32")
        result = C.c_ssize_t
        self.proc_type = C.WINFUNCTYPE(result, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
        class WindowClass(C.Structure):
            _fields_ = [("style", W.UINT), ("proc", self.proc_type), ("extra_class", C.c_int), ("extra_window", C.c_int),
                        ("instance", W.HINSTANCE), ("icon", W.HICON), ("cursor", W.HANDLE), ("background", W.HBRUSH),
                        ("menu", W.LPCWSTR), ("name", W.LPCWSTR)]
        class IconData(C.Structure):
            _fields_ = [("size", W.DWORD), ("hwnd", W.HWND), ("id", W.UINT), ("flags", W.UINT), ("message", W.UINT),
                        ("icon", W.HICON), ("tip", W.WCHAR * 128), ("state", W.DWORD), ("state_mask", W.DWORD),
                        ("info", W.WCHAR * 256), ("version", W.UINT), ("title", W.WCHAR * 64), ("info_flags", W.DWORD),
                        ("guid", C.c_byte * 16), ("balloon_icon", W.HICON)]
        def signature(lib, name, args, ret):
            fn = getattr(lib, name); fn.argtypes, fn.restype = args, ret
        signature(self.k, "GetModuleHandleW", [W.LPCWSTR], W.HMODULE)
        signature(self.u, "RegisterClassW", [C.POINTER(WindowClass)], W.ATOM)
        signature(self.u, "UnregisterClassW", [W.LPCWSTR, W.HINSTANCE], W.BOOL)
        signature(self.u, "CreateWindowExW", [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD, C.c_int, C.c_int, C.c_int, C.c_int, W.HWND, W.HMENU, W.HINSTANCE, C.c_void_p], W.HWND)
        signature(self.u, "DefWindowProcW", [W.HWND, W.UINT, W.WPARAM, W.LPARAM], result)
        signature(self.u, "LoadImageW", [W.HINSTANCE, W.LPCWSTR, W.UINT, C.c_int, C.c_int, W.UINT], W.HANDLE)
        signature(self.u, "LoadIconW", [W.HINSTANCE, C.c_void_p], W.HICON)
        signature(self.u, "CreatePopupMenu", [], W.HMENU)
        signature(self.u, "AppendMenuW", [W.HMENU, W.UINT, C.c_size_t, W.LPCWSTR], W.BOOL)
        signature(self.u, "TrackPopupMenu", [W.HMENU, W.UINT, C.c_int, C.c_int, C.c_int, W.HWND, C.c_void_p], W.UINT)
        signature(self.u, "DestroyMenu", [W.HMENU], W.BOOL)
        signature(self.u, "SetForegroundWindow", [W.HWND], W.BOOL)
        signature(self.u, "PostMessageW", [W.HWND, W.UINT, W.WPARAM, W.LPARAM], W.BOOL)
        signature(self.u, "GetCursorPos", [C.POINTER(W.POINT)], W.BOOL)
        signature(self.u, "DestroyWindow", [W.HWND], W.BOOL)
        signature(self.u, "DestroyIcon", [W.HICON], W.BOOL)
        signature(self.u, "PeekMessageW", [C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT, W.UINT], W.BOOL)
        signature(self.u, "TranslateMessage", [C.POINTER(W.MSG)], W.BOOL)
        signature(self.u, "DispatchMessageW", [C.POINTER(W.MSG)], result)
        signature(self.u, "RegisterWindowMessageW", [W.LPCWSTR], W.UINT)
        signature(self.s, "Shell_NotifyIconW", [W.DWORD, C.POINTER(IconData)], W.BOOL)
        self.restart_message = self.u.RegisterWindowMessageW("TaskbarCreated")
        self.callback = self.proc_type(self._window_proc)
        self.instance = self.k.GetModuleHandleW(None)
        self.class_name = "MyLittlePetTray_" + str(os.getpid())
        self.wc = WindowClass(0, self.callback, 0, 0, self.instance, None, None, None, None, self.class_name)
        if not self.u.RegisterClassW(C.byref(self.wc)): raise OSError("Could not register tray window")
        self.hwnd = self.u.CreateWindowExW(0, self.class_name, "My Little Pet controls", 0, 0, 0, 0, 0, None, None, self.instance, None)
        if not self.hwnd:
            self.u.UnregisterClassW(self.class_name, self.instance)
            raise OSError("Could not create tray window")
        path = str(Path(__file__).resolve().parent.parent / "packaging" / "pet.ico")
        self.icon = self.u.LoadImageW(None, path, 1, 16, 16, 0x10)
        self.custom_icon = bool(self.icon)
        self.icon = self.icon or self.u.LoadIconW(None, C.c_void_p(32512))
        self.data = IconData()
        self.data.size, self.data.hwnd, self.data.id = C.sizeof(IconData), self.hwnd, 1
        self.data.flags, self.data.message, self.data.icon = 1 | 2 | 4, 0x8001, self.icon
        self.data.tip = "My Little Pet - click to find pets; right-click for controls"
        if not self.s.Shell_NotifyIconW(0, C.byref(self.data)):
            self.close()
            raise OSError("Could not add notification icon")

    def _window_proc(self, hwnd, message, wp, lp):
        if message == self.restart_message and hasattr(self, "data"):
            self.s.Shell_NotifyIconW(0, C.byref(self.data)); return 0
        if message == 0x8001:
            event = lp & 0xffff
            if event == 0x202: self.pending.append("rescue")
            elif event in (0x205, 0x7b):
                menu = self.u.CreatePopupMenu()
                try:
                    for i, (_, label) in enumerate(self.ACTIONS, 1): self.u.AppendMenuW(menu, 0, i, label)
                    point = W.POINT(); self.u.GetCursorPos(C.byref(point))
                    self.u.SetForegroundWindow(hwnd)
                    chosen = self.u.TrackPopupMenu(menu, 0x100 | 0x2, point.x, point.y, 0, hwnd, None)
                    self.u.PostMessageW(hwnd, 0, 0, 0)
                    if 1 <= chosen <= len(self.ACTIONS): self.pending.append(self.ACTIONS[chosen - 1][0])
                finally: self.u.DestroyMenu(menu)
            return 0
        return self.u.DefWindowProcW(hwnd, message, wp, lp)

    def poll(self):
        message = W.MSG()
        while self.u.PeekMessageW(C.byref(message), self.hwnd, 0, 0, 1):
            self.u.TranslateMessage(C.byref(message)); self.u.DispatchMessageW(C.byref(message))
        actions, self.pending = self.pending, []
        for key in actions: self.handler(key)

    def close(self):
        if getattr(self, "data", None): self.s.Shell_NotifyIconW(2, C.byref(self.data))
        if getattr(self, "hwnd", None): self.u.DestroyWindow(self.hwnd); self.hwnd = None
        if getattr(self, "custom_icon", False): self.u.DestroyIcon(self.icon); self.custom_icon = False
        self.u.UnregisterClassW(self.class_name, self.instance)
