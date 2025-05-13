"""
애플리케이션 컨트롤러 모듈
"""
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, Qt, QRect
from PyQt5.QtGui import QCursor, QColor

from src.models.color_detector import ColorDetector
from src.views.control_panel import ControlPanel
from src.views.monitoring_area import MonitoringArea
from src.views.transparent_window import TransparentWindow


class AppController(QObject):
    """애플리케이션 컨트롤러"""
    
    def __init__(self):
        super().__init__()
        
        # 컴포넌트 초기화
        self.color_detector = ColorDetector()
        self.control_panel = ControlPanel()
        self.monitoring_area = MonitoringArea()
        self.overlay_window = TransparentWindow()
        
        # 컨트롤 패널 신호 연결
        self.control_panel.color_changed.connect(self.on_color_changed)
        self.control_panel.threshold_changed.connect(self.on_threshold_changed)
        self.control_panel.monitoring_toggled.connect(self.on_monitoring_toggled)
        self.control_panel.area_interaction_toggled.connect(self.on_area_interaction_toggled)
        self.control_panel.debug_mode_toggled.connect(self.on_debug_mode_toggled)
        self.control_panel.exit_requested.connect(self.on_exit_requested)
        
        # 모니터링 영역 신호 연결
        self.monitoring_area.area_changed.connect(self.on_area_changed)
        
        # 색상 감지기 신호 연결
        self.color_detector.color_detected.connect(self.on_color_detected)
        self.color_detector.debug_pixel_info.connect(self.on_debug_pixel_info)
        
        # 초기 모니터링 영역 설정
        initial_rect = self.monitoring_area.get_monitoring_rect()
        self.color_detector.set_monitoring_area(initial_rect)
        self.control_panel.update_selection_info(initial_rect)
    
    def start(self):
        """애플리케이션 시작"""
        # 모든 창 표시
        self.control_panel.show()
        self.monitoring_area.show()
        self.overlay_window.show()
    
    def on_color_changed(self, color):
        """타겟 색상 변경 처리"""
        self.color_detector.set_target_color(color)
    
    def on_threshold_changed(self, value):
        """임계값 변경 처리"""
        self.color_detector.set_threshold(value)
    
    def on_monitoring_toggled(self, enabled):
        """모니터링 토글 처리"""
        if enabled:
            self.color_detector.start_monitoring()
        else:
            self.color_detector.stop_monitoring()
            self.overlay_window.clear_highlight()
        
        self.overlay_window.toggle_monitoring(enabled)
    
    def on_area_interaction_toggled(self, enabled):
        """모니터링 영역 상호작용 토글 처리"""
        self.monitoring_area.enable_interaction(enabled)
    
    def on_debug_mode_toggled(self, enabled):
        """디버깅 모드 토글 처리"""
        self.color_detector.set_debug_mode(enabled)
        self.overlay_window.set_debug_mode(enabled)
    
    def on_area_changed(self, rect):
        """모니터링 영역 변경 처리"""
        self.color_detector.set_monitoring_area(rect)
        self.control_panel.update_selection_info(rect)
    
    def on_color_detected(self, points, color):
        """색상 감지 처리"""
        self.overlay_window.highlight_area(points, color)
    
    def on_debug_pixel_info(self, cursor_pos, pixel_color):
        """디버그 픽셀 정보 처리"""
        self.overlay_window.set_debug_info(cursor_pos, pixel_color)
    
    def on_exit_requested(self):
        """종료 요청 처리"""
        # 모든 창 닫기
        self.control_panel.close()
        self.monitoring_area.close()
        self.overlay_window.close()
        # 애플리케이션 종료
        QApplication.quit()
