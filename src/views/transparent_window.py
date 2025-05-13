"""
투명 오버레이 윈도우 모듈
"""
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, QRect, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QGuiApplication
import win32gui

from src.utils.window_utils import set_window_transparent, set_window_topmost, set_window_clickthrough


class TransparentWindow(QMainWindow):
    """투명 오버레이 윈도우"""
    
    def __init__(self):
        super().__init__()
        
        # 윈도우 설정
        self.setWindowTitle("색상 하이라이트 감지기")
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 전체 화면 크기로 설정
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen_geometry.width(), screen_geometry.height())
        
        # 윈도우 핸들 설정
        self.hwnd = None
        self.install_window_hook()
        
        # 하이라이트할 포인트 목록
        self.highlight_points = []
        self.highlight_color = QColor(255, 0, 0, 150)  # 반투명 빨간색
        
        # 하이라이트 점 크기
        self.point_size = 5
        
        # 디버깅 정보 표시용
        self.debug_mode = False
        self.debug_cursor_pos = None
        self.debug_pixel_color = None
        
        # 화면 업데이트 타이머
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(100)  # 100ms 간격으로 화면 갱신
    
    def install_window_hook(self):
        """윈도우 핸들을 가져와서 입력 패스스루 설정"""
        # 윈도우가 표시된 후 핸들 얻기
        self.hwnd = self.winId().__int__()
        
        # 투명 설정 및 클릭 패스스루 설정
        set_window_transparent(self.hwnd)
        set_window_clickthrough(self.hwnd, True)
        
        # 윈도우를 최상위로 설정
        set_window_topmost(self.hwnd)
    
    def toggle_monitoring(self, enabled):
        """모니터링 시작/중지"""
        # 상태만 업데이트, 실제 모니터링은 컨트롤러에서 담당
        if not enabled:
            # 모니터링 중지 시 하이라이트 제거
            self.clear_highlight()
    
    def toggle_area_interaction(self, enabled):
        """모니터링 영역 상호작용 토글"""
        # 상태만 업데이트, 실제 처리는 컨트롤러에서 담당
        pass
    
    def update_monitoring_area(self, rect):
        """모니터링 영역 업데이트"""
        # 영역 정보 업데이트, 실제 영역 변경은 컨트롤러에서 담당
        pass
    
    def highlight_area(self, points, color):
        """색상 발견 위치 하이라이트"""
        self.highlight_points = points
        # 기존 코드처럼 마젠타색 고정 사용 (전달받은 color 무시)
        self.highlight_color = QColor(255, 0, 255, 180)  # 마젠타색, 반투명
        self.update()
    
    def clear_highlight(self):
        """하이라이트 제거"""
        self.highlight_points = []
        self.update()
    
    def set_debug_info(self, cursor_pos, pixel_color):
        """디버깅 정보 설정"""
        self.debug_cursor_pos = cursor_pos
        self.debug_pixel_color = pixel_color
        self.update()
    
    def set_debug_mode(self, enabled):
        """디버깅 모드 설정"""
        self.debug_mode = enabled
        if not enabled:
            self.debug_cursor_pos = None
            self.debug_pixel_color = None
        self.update()
    
    def close_application(self):
        """애플리케이션 종료"""
        self.close()
    
    def paintEvent(self, event):
        """화면 그리기 이벤트"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 하이라이트 포인트 그리기
        if self.highlight_points:
            # 마젠타색 네모 상자 테두리만 그리기 (내부는 투명)
            pen = QPen(self.highlight_color, 2, Qt.SolidLine)  # 더 굵은 테두리(2픽셀)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)  # 내부는 채우지 않음 (투명)
            
            # 사각형 크기 설정
            square_size = 10  # 10x10 사각형
            
            for point in self.highlight_points:
                # 사각형 그리기 (중앙이 point 위치가 되도록)
                x = point.x() - square_size // 2
                y = point.y() - square_size // 2
                painter.drawRect(x, y, square_size, square_size)
        
        # 디버깅 모드 정보 표시
        if self.debug_mode and self.debug_cursor_pos and self.debug_pixel_color:
            # 커서 주변에 박스 그리기
            pen = QPen(QColor(255, 255, 255), 2, Qt.SolidLine)
            painter.setPen(pen)
            
            # 커서 위치에 20x20 사각형 그리기
            rect_size = 40  # 확대해서 보기 위한 크기
            x = self.debug_cursor_pos.x() - rect_size // 2
            y = self.debug_cursor_pos.y() - rect_size // 2
            
            # 테두리가 있는 사각형 그리기
            painter.drawRect(x, y, rect_size, rect_size)
            
            # 현재 픽셀 색상으로 채워진 사각형 그리기
            brush = QBrush(self.debug_pixel_color, Qt.SolidPattern)
            painter.setBrush(brush)
            painter.drawRect(x + 2, y + 2, rect_size - 4, rect_size - 4)
            
            # 색상 정보 텍스트 표시
            pen = QPen(QColor(255, 255, 255), 1, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            
            # 배경 사각형 (텍스트 가독성 향상)
            text_bg_rect = QRect(x, y + rect_size + 5, 150, 45)
            painter.fillRect(text_bg_rect, QColor(0, 0, 0, 180))
            
            # 색상 정보 텍스트
            painter.drawText(x + 5, y + rect_size + 20, 
                          f"RGB: ({self.debug_pixel_color.red()}, " +
                          f"{self.debug_pixel_color.green()}, " +
                          f"{self.debug_pixel_color.blue()})")
            
            hex_color = f"#{self.debug_pixel_color.red():02X}" + \
                        f"{self.debug_pixel_color.green():02X}" + \
                        f"{self.debug_pixel_color.blue():02X}"
            painter.drawText(x + 5, y + rect_size + 40, f"HEX: {hex_color}")
