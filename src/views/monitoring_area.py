"""
모니터링 영역 윈도우 모듈
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QGuiApplication
from PyQt5.QtCore import QTimer
import win32gui
import win32con

from src.views.resize_handle import ResizeHandle
from src.utils.window_utils import set_window_clickthrough, set_window_topmost


class MonitoringArea(QMainWindow):
    """조절 가능한 모니터링 영역 윈도우"""
    area_changed = pyqtSignal(QRect)  # 영역 변경 시 신호
    
    def __init__(self):
        super().__init__()
        
        # 윈도우 설정
        self.setWindowTitle("모니터링 영역")
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        
        # 초기 크기 및 위치 설정
        self.resize(300, 300)
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.move(
            (screen_geometry.width() - self.width()) // 2,
            (screen_geometry.height() - self.height()) // 2
        )
        
        # 크기 조절 핸들 생성
        self.handles = {}
        self.handles["top-left"] = ResizeHandle(self, "top-left")
        self.handles["top-right"] = ResizeHandle(self, "top-right")
        self.handles["bottom-left"] = ResizeHandle(self, "bottom-left")
        self.handles["bottom-right"] = ResizeHandle(self, "bottom-right")
        
        # 핸들 위치 업데이트
        self.update_handle_positions()
        
        # 드래그 관련 변수
        self.dragging = False
        self.drag_position = None
        self.resizing = False
        self.resize_handle = None
        
        # 윈도우 핸들 설정
        self.hwnd = None
        self.install_window_hook()
        # 클릭 패스스루 보장
        if self.hwnd:
            set_window_clickthrough(self.hwnd, True)
        
        # 상호작용 활성화 상태
        self.interaction_enabled = False
    
    def install_window_hook(self):
        """윈도우 핸들을 가져와서 입력 패스스루 설정"""
        # 윈도우가 생성된 후 핸들 얻기
        self.hwnd = self.winId().__int__()
        
        # 윈도우를 최상위로 설정
        set_window_topmost(self.hwnd)
        
        # 초기화 시 클릭 패스스루 활성화 (상호작용 불가능)
        self.enable_interaction(False)
    
    def enable_interaction(self, enable=True):
        """상호작용 활성화/비활성화"""
        if enable:
            # 상호작용 활성화
            self.interaction_enabled = True
            
            # 핸들 표시
            for handle in self.handles.values():
                handle.show()
            
            # 클릭 패스스루 해제(드래그/리사이즈 가능)
            if self.hwnd:
                set_window_clickthrough(self.hwnd, False)
            
            # 윈도우 포커스 설정
            self.activateWindow()
            self.raise_()
        else:
            # 상호작용 비활성화
            self.interaction_enabled = False
            
            # 핸들 숨기기
            for handle in self.handles.values():
                handle.hide()
            
            # 클릭 패스스루 활성화(완전 투명)
            if self.hwnd:
                set_window_clickthrough(self.hwnd, True)
                
        # 화면 강제 갱신 - 즉시 다시 그리기
        self.repaint()
                
    
    def update_handle_positions(self):
        """크기 조절 핸들 위치 업데이트"""
        # 각 핸들의 위치 설정
        self.handles["top-left"].move(0, 0)
        self.handles["top-right"].move(self.width() - 10, 0)
        self.handles["bottom-left"].move(0, self.height() - 10)
        self.handles["bottom-right"].move(self.width() - 10, self.height() - 10)
    
    def get_monitoring_rect(self):
        """현재 모니터링 영역 가져오기"""
        return QRect(self.pos().x(), self.pos().y(), self.width(), self.height())
    
    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        if not self.interaction_enabled:
            return
        
        if event.button() == Qt.LeftButton:
            # 드래그 위치 저장
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            
            # 핸들 위에서 클릭했는지 확인
            for position, handle in self.handles.items():
                if handle.geometry().contains(event.pos()):
                    self.resizing = True
                    self.resize_handle = position
                    self.drag_position = event.globalPos()
                    break
            
            event.accept()
    
    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트"""
        if not self.interaction_enabled:
            return
        
        if event.buttons() & Qt.LeftButton:
            if self.resizing and self.resize_handle:
                # 크기 조절 처리
                delta = event.globalPos() - self.drag_position
                self.drag_position = event.globalPos()
                
                # 현재 위치와 크기
                current_pos = self.pos()
                current_size = self.size()
                
                # 핸들 위치에 따른 크기 조절
                if self.resize_handle == "bottom-right":
                    self.resize(current_size.width() + delta.x(), current_size.height() + delta.y())
                
                elif self.resize_handle == "bottom-left":
                    new_width = current_size.width() - delta.x()
                    if new_width > 50:
                        self.resize(new_width, current_size.height() + delta.y())
                        self.move(current_pos.x() + delta.x(), current_pos.y())
                
                elif self.resize_handle == "top-right":
                    new_height = current_size.height() - delta.y()
                    if new_height > 50:
                        self.resize(current_size.width() + delta.x(), new_height)
                        self.move(current_pos.x(), current_pos.y() + delta.y())
                
                elif self.resize_handle == "top-left":
                    new_width = current_size.width() - delta.x()
                    new_height = current_size.height() - delta.y()
                    if new_width > 50 and new_height > 50:
                        self.resize(new_width, new_height)
                        self.move(current_pos.x() + delta.x(), current_pos.y() + delta.y())
                
                # 핸들 위치 업데이트
                self.update_handle_positions()
                
                # 영역 변경 신호 발생
                self.area_changed.emit(self.get_monitoring_rect())
            
            elif self.dragging:
                # 드래그로 이동
                self.move(event.globalPos() - self.drag_position)
                
                # 영역 변경 신호 발생
                self.area_changed.emit(self.get_monitoring_rect())
            
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """마우스 릴리즈 이벤트"""
        if not self.interaction_enabled:
            return
        
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_handle = None
            
            # 영역 변경 신호 발생
            self.area_changed.emit(self.get_monitoring_rect())
    
    def paintEvent(self, event):
        """화면 그리기 이벤트"""
        painter = QPainter(self)
        
        # 시작하기 전에 화면 완전히 지우기
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    
        if self.interaction_enabled:
            # 상호작용 활성화 시 반투명 배경 그리기
            painter.fillRect(self.rect(), QColor(0, 0, 255, 50))
            # 테두리 그리기
            pen = QPen(QColor(0, 0, 255), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
        else:
            # 상호작용 비활성화 시엔 초경한 테두리만
            pen = QPen(QColor(255, 255, 255, 50), 1, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(0, 0, self.width() - 1, self.height() - 1)