"""
크기 조절 핸들 위젯 모듈
"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt


class ResizeHandle(QWidget):
    """크기 조절 핸들 위젯"""
    
    def __init__(self, parent=None, position="bottom-right"):
        super().__init__(parent)
        self.position = position
        self.setFixedSize(10, 10)
        
        # 위치에 따른 커서 설정
        if position in ["bottom-right", "top-left"]:
            self.setCursor(Qt.SizeFDiagCursor)
        elif position in ["bottom-left", "top-right"]:
            self.setCursor(Qt.SizeBDiagCursor)
        elif position in ["left", "right"]:
            self.setCursor(Qt.SizeHorCursor)
        elif position in ["top", "bottom"]:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.SizeFDiagCursor)
