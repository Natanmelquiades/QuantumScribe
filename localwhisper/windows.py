"""Módulo de Integração com APIs Win32 (Windows).

Este módulo concentra toda a lógica de baixo nível do Windows usando ctypes.
Ele gerencia as capturas de foco de janelas ativas, envia sequências de teclas
físicas usando SendInput (para simular a ação de colar com Ctrl+V), escreve na
área de transferência de forma thread-safe, e implementa garantias de instância
única com Mutex do sistema operacional.
"""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from dataclasses import dataclass

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Configuração de assinaturas e retornos da API Win32
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

# Constantes da API Win32
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


# Estruturas do Windows API para o SendInput (simulação de teclado)

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
    """Captura a janela ativa e o controle focado no momento exato da chamada.

    Ele inspeciona a Thread GUI ativa do Windows para identificar caixas de texto.
    """
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
    """Garante que apenas uma instância do LocalWhisper esteja rodando no Windows.

    Cria um Mutex global com nome persistente no sistema operacional.
    """
    global _instance_mutex
    handle = kernel32.CreateMutexW(None, False, "LocalWhisper.SingleInstance")
    if not handle:
        return False

    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        # Não retenha um segundo handle: isso impediria a nova tentativa feita
        # depois que o usuário confirma a reinicialização do aplicativo.
        kernel32.CloseHandle(handle)
        return False

    _instance_mutex = handle
    return True


def set_clipboard_text(text: str) -> None:
    """Escreve um texto formatado em UTF-16 na área de transferência global do Windows.

    Abre, limpa e escreve de forma exclusiva, fechando o canal logo em seguida.
    """
    if not user32.OpenClipboard(None):
        raise OSError("Não foi possível abrir a área de transferência.")
    memory = None
    try:
        user32.EmptyClipboard()
        # Converte a string Python para codificação UTF-16 LE com terminador nulo duplo
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
    """Injeta texto na janela ativa por meio de simulação do atalho de colar (Ctrl+V).

    Copia o texto para a área de transferência do Windows e envia os eventos
    de simulação de teclas físicas 'Ctrl' e 'V' usando keybd_event. Como a
    nossa janela flutuante não é ativada (WS_EX_NOACTIVATE), o atalho é processado
    diretamente no campo onde o cursor já estava posicionado.

    Args:
        target: Alvo originalmente capturado (ignorado se uma janela diferente estiver ativa).
        text: String de texto transcrita a ser colada.

    Returns:
        True se a injeção de teclas foi enviada com sucesso, False caso contrário.
    """
    # 1. Garante que o texto transcrito atual está carregado na área de transferência
    set_clipboard_text(text)

    # 2. Verifica se a janela em foco ainda é a mesma (ou pertence ao mesmo processo)
    current_hwnd = foreground_window()
    target_hwnd = target.window
    use_hwnd = target_hwnd  # Por padrão, usa sempre a janela capturada

    if current_hwnd and user32.IsWindow(current_hwnd):
        # Obtém o PID de ambas as janelas para comparação por processo
        current_pid = ctypes.c_ulong(0)
        target_pid = ctypes.c_ulong(0)
        user32.GetWindowThreadProcessId(current_hwnd, ctypes.byref(current_pid))
        user32.GetWindowThreadProcessId(target_hwnd, ctypes.byref(target_pid))

        if current_hwnd == target_hwnd or current_pid.value == target_pid.value:
            # Mesma janela ou mesmo processo — seguro usar a janela atual
            use_hwnd = current_hwnd
        else:
            # Usuário trocou de app — restaura o foco para a janela original
            # antes de injetar, para evitar colar no app errado
            user32.SetForegroundWindow(target_hwnd)
            time.sleep(0.1)  # Aguarda o foco ser estabelecido
            use_hwnd = target_hwnd

    if not use_hwnd or not user32.IsWindow(use_hwnd):
        return False

    # Atraso de 50ms para que o buffer de entrada do Windows limpe o atalho físico pressionado pelo usuário
    time.sleep(0.05)

    # 3. Simula a combinação de teclas de colagem (Ctrl + V) usando keybd_event
    VK_CONTROL = 0x11
    VK_V = 0x56
    KEYEVENTF_KEYUP = 0x0002

    # Ctrl Down
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    # V Down
    user32.keybd_event(VK_V, 0, 0, 0)
    # V Up
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    # Ctrl Up
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    return True


def press_enter() -> None:
    """Simula o pressionamento físico da tecla Enter (Return) no Windows.

    Insere um pequeno delay (80ms) antes de enviar o evento para garantir
    que o texto colado via Ctrl+V já esteja processado na caixa de texto alvo.
    """
    VK_RETURN = 0x0D
    KEYEVENTF_KEYUP = 0x0002

    time.sleep(0.08)
    # Enter Down
    user32.keybd_event(VK_RETURN, 0, 0, 0)
    # Enter Up
    user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)
