"""
윈도우 관련 유틸리티 함수 모듈
"""
import win32gui
import win32con
from PyQt5.QtCore import Qt


def set_window_transparent(hwnd):
    """윈도우를 투명하게 설정하는 함수"""
    # 윈도우 스타일 설정
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(
        hwnd, 
        win32con.GWL_EXSTYLE, 
        ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
    )


def set_window_clickthrough(hwnd, enable=True):
    """윈도우 클릭 패스스루 설정하는 함수"""
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if enable:
        # 클릭 패스스루 활성화
        win32gui.SetWindowLong(
            hwnd, 
            win32con.GWL_EXSTYLE, 
            ex_style | win32con.WS_EX_TRANSPARENT
        )
    else:
        # 클릭 패스스루 비활성화
        win32gui.SetWindowLong(
            hwnd, 
            win32con.GWL_EXSTYLE, 
            ex_style & ~win32con.WS_EX_TRANSPARENT
        )


def set_window_topmost(hwnd):
    """윈도우를 항상 위에 표시하는 함수"""
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
    )
