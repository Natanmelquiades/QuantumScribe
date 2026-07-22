"""Módulo de Integração com APIs Win32 (Windows)."""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from dataclasses import dataclass

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = wintypes.LPVOID
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.c_void_p]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.c_void_p]
user32.GetGUIThreadInfo.restype = wintypes.BOOL
user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsIconic.restype = wintypes.BOOL
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.SetFocus.argtypes = [wintypes.HWND]
user32.SetFocus.restype = wintypes.HWND
user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_size_t]
user32.keybd_event.restype = None
user32.AllowSetForegroundWindow.argtypes = [wintypes.DWORD]
user32.AllowSetForegroundWindow.restype = wintypes.BOOL
kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.GetLastError.restype = wintypes.DWORD
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
SW_RESTORE = 9
ERROR_ALREADY_EXISTS = 183
ASFW_ANY = 0xFFFFFFFF

_instance_mutex: int | None = None


@dataclass(frozen=True, slots=True)
class WindowTarget:
    """Representa a janela de destino onde o texto deve ser inserido."""
    window: int
    focus: int = 0


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT),
    ]


def foreground_window() -> int:
    """Retorna o manipulador (HWND) da janela ativa em primeiro plano."""
    return int(user32.GetForegroundWindow())


def capture_input_target() -> WindowTarget:
    """Captura a janela ativa e o controle focado no momento exato da chamada."""
    hwnd = foreground_window()
    if not hwnd or not user32.IsWindow(hwnd):
        return WindowTarget(0)

    target_thread = user32.GetWindowThreadProcessId(hwnd, None)
    info = GUITHREADINFO()
    info.cbSize = ctypes.sizeof(GUITHREADINFO)
    if target_thread and user32.GetGUIThreadInfo(target_thread, ctypes.byref(info)):
        focus = int(info.hwndFocus or info.hwndCaret or 0)
        if focus and user32.IsWindow(focus):
            return WindowTarget(hwnd, focus)

    return WindowTarget(hwnd)


def acquire_single_instance() -> bool:
    """Garante que apenas uma instância do LocalWhisper esteja rodando no Windows."""
    global _instance_mutex
    handle = kernel32.CreateMutexW(None, False, "LocalWhisper.SingleInstance")
    if not handle:
        return False

    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return False

    _instance_mutex = handle
    return True


def set_clipboard_text(text: str) -> None:
    """Escreve um texto formatado em UTF-16 na área de transferência global do Windows."""
    if not user32.OpenClipboard(None):
        raise OSError("Não foi possível abrir a área de transferência.")
    memory = None
    try:
        user32.EmptyClipboard()
        encoded = text.encode("utf-16-le") + b"\x00\x00"
        memory = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
        if not memory:
            raise MemoryError("Falha ao alocar memória para o clipboard.")
        pointer = kernel32.GlobalLock(memory)
        ctypes.memmove(pointer, encoded, len(encoded))
        kernel32.GlobalUnlock(memory)
        if not user32.SetClipboardData(CF_UNICODETEXT, memory):
            raise OSError("Falha ao escrever na área de transferência.")
        memory = None
    finally:
        user32.CloseClipboard()
        if memory:
            kernel32.GlobalFree(memory)


def type_into_window(target: WindowTarget, text: str) -> bool:
    """Injeta texto na janela ativa via Ctrl+V."""
    set_clipboard_text(text)

    current_hwnd = foreground_window()
    target_hwnd = target.window
    use_hwnd = target_hwnd

    if current_hwnd and user32.IsWindow(current_hwnd):
        current_pid = ctypes.c_ulong(0)
        target_pid = ctypes.c_ulong(0)
        user32.GetWindowThreadProcessId(current_hwnd, ctypes.byref(current_pid))
        user32.GetWindowThreadProcessId(target_hwnd, ctypes.byref(target_pid))

        if current_hwnd == target_hwnd or current_pid.value == target_pid.value:
            use_hwnd = current_hwnd
        else:
            user32.SetForegroundWindow(target_hwnd)
            time.sleep(0.1)
            use_hwnd = target_hwnd

    if not use_hwnd or not user32.IsWindow(use_hwnd):
        return False

    time.sleep(0.05)

    VK_CONTROL = 0x11
    VK_V = 0x56
    KEYEVENTF_KEYUP = 0x0002

    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    return True


def press_enter() -> None:
    """Simula a tecla Enter no Windows."""
    VK_RETURN = 0x0D
    KEYEVENTF_KEYUP = 0x0002

    time.sleep(0.08)
    user32.keybd_event(VK_RETURN, 0, 0, 0)
    user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)


def wait_for_process_exit(pid: int, timeout_ms: int = 15000) -> None:
    """Aguarda o encerramento do processo com o PID informado no Windows."""
    if pid <= 0:
        return
    try:
        handle = kernel32.OpenProcess(0x00100000, False, pid)
        if handle:
            kernel32.WaitForSingleObject(handle, timeout_ms)
            kernel32.CloseHandle(handle)
    except Exception:
        pass
