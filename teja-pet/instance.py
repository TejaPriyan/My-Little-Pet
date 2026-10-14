"""Keep two Windows copies from overwriting the same pet's save."""
import ctypes
import hashlib
import os


class SingleInstance:
    def __init__(self, save_directory):
        self.handle = None
        self.already_running = False
        if os.name != "nt":
            return
        from ctypes import wintypes
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        self.api.CreateMutexW.restype = wintypes.HANDLE
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        key = hashlib.sha256(os.path.normcase(os.path.abspath(save_directory)).encode()).hexdigest()[:24]
        self.handle = self.api.CreateMutexW(None, False, "Local\\MyLittlePet-" + key)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        self.already_running = ctypes.get_last_error() == 183

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None
