import sys
import time
import numpy as np
from PIL import ImageGrab
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QColorDialog, QSlider, QSpinBox, QRadioButton, QButtonGroup
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSignal, QObject, QPoint
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QCursor
import win32gui
import win32con
import win32api

class ColorDetector(QObject):
    """색상 감지 및 분석을 위한 클래스"""
    color_detected = pyqtSignal(list, QColor)  # 색상 감지 시 신호 발생 (위치 목록과 색상)
    
    def __init__(self, target_color=QColor(255, 0, 0), threshold=10):
        super().__init__()
        self.target_color = target_color
        self.threshold = threshold
        self.monitoring_area = QRect(0, 0, 300, 300)
        self.is_monitoring = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_colors)
    
    def start_monitoring(self):
        """모니터링 시작"""
        self.is_monitoring = True
        self.timer.start(100)  # 100ms 간격으로 체크
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_monitoring = False
        self.timer.stop()
    
    def set_target_color(self, color):
        """타겟 색상 설정"""
        self.target_color = color
    
    def set_threshold(self, value):
        """색상 감지 임계값 설정"""
        self.threshold = value
    
    def set_monitoring_area(self, rect):
        """모니터링 영역 설정"""
        self.monitoring_area = rect
    
    def check_colors(self):
        """화면에서 색상 체크"""
        if not self.is_monitoring:
            return
            
        try:
            # 모니터링 영역 스크린샷 캡처
            x, y, w, h = self.monitoring_area.x(), self.monitoring_area.y(), self.monitoring_area.width(), self.monitoring_area.height()
            screenshot = ImageGrab.grab(bbox=(x, y, x+w, y+h))
            img_array = np.array(screenshot)
            
            # 타겟 색상 RGB 값
            target_r, target_g, target_b = self.target_color.red(), self.target_color.green(), self.target_color.blue()
            
            # 픽셀 검사
            match_points = self._check_colors_pixel_mode(img_array, target_r, target_g, target_b, x, y)
            
            # 발견된 색상 위치가 있으면 시그널 전송
            if match_points:
                self.color_detected.emit(match_points, self.target_color)
        except Exception as e:
            print(f"오류 발생: {e}")
    
    def _check_colors_pixel_mode(self, img_array, target_r, target_g, target_b, base_x, base_y):
        """1x1 픽셀 모드로 색상 검사 (모든 개별 픽셀 검사)"""
        h, w = img_array.shape[:2]
        
        # 색상별 임계값 적용 (각 채널별로 독립적으로 비교)
        r_min = max(0, target_r - self.threshold)
        r_max = min(255, target_r + self.threshold)
        g_min = max(0, target_g - self.threshold)
        g_max = min(255, target_g + self.threshold)
        b_min = max(0, target_b - self.threshold)
        b_max = min(255, target_b + self.threshold)
        
        # 임계값 범위 내에 있는 픽셀 찾기 (각 채널별로 검사)
        r_match = (img_array[:, :, 0] >= r_min) & (img_array[:, :, 0] <= r_max)
        g_match = (img_array[:, :, 1] >= g_min) & (img_array[:, :, 1] <= g_max)
        b_match = (img_array[:, :, 2] >= b_min) & (img_array[:, :, 2] <= b_max)
        
        # 모든 채널이 일치하는 픽셀만 선택
        all_match = r_match & g_match & b_match
        matches = np.where(all_match)
        
        # 디버깅 정보 출력
        if len(matches[0]) > 0:
            print(f"타겟 색상: R={target_r}, G={target_g}, B={target_b}")
            print(f"검색 범위: R={r_min}~{r_max}, G={g_min}~{g_max}, B={b_min}~{b_max}")
            print(f"총 {len(matches[0])}개의 픽셀 찾음")
            if len(matches[0]) < 10:  # 10개 이하일 경우 각 픽셀 정보 출력
                for i in range(len(matches[0])):
                    y, x = matches[0][i], matches[1][i]
                    pixel = img_array[y, x]
                    print(f"  픽셀[{i}]: 좌표=({base_x+x},{base_y+y}), RGB=({pixel[0]},{pixel[1]},{pixel[2]})")
        
        if len(matches[0]) == 0:
            return []
        
        # 최대 픽셀 수 제한 (너무 많으면 성능 저하 방지)
        max_pixels = 10
        
        if len(matches[0]) > max_pixels:
            # 균등하게 샘플링
            step = len(matches[0]) // max_pixels
            indices = np.arange(0, len(matches[0]), step)[:max_pixels]
            y_coords = matches[0][indices]
            x_coords = matches[1][indices]
        else:
            y_coords = matches[0]
            x_coords = matches[1]
        
        # 발견된 색상 위치 목록 생성
        color_points = []
        for i in range(len(y_coords)):
            point_y = base_y + y_coords[i]
            point_x = base_x + x_coords[i]
            color_points.append(QPoint(point_x, point_y))
        
        return color_points


class ResizeHandle(QWidget):
    """크기 조절 핸들 위젯"""
    def __init__(self, parent=None, position="bottom-right"):
        super().__init__(parent)
        self.position = position
        self.setFixedSize(10, 10)
        self.setCursor(Qt.SizeFDiagCursor)


class MonitoringArea(QWidget):
    """조절 가능한 모니터링 영역 윈도우"""
    area_changed = pyqtSignal(QRect)
    
    def __init__(self):
        super().__init__()
        
        # 윈도우 설정
        self.setWindowTitle("모니터링 영역")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 초기 크기와 위치
        self.setGeometry(100, 100, 300, 300)
        
        # 드래그 관련 변수
        self.dragging = False
        self.drag_start_position = None
        self.resizing = False
        self.resize_handle = None
        self.resize_start_geometry = None
        
        # 상호작용 모드
        self.interaction_enabled = False
        
        # 크기 조절 핸들 생성
        self.resize_handles = {
            "top-left": ResizeHandle(self, "top-left"),
            "top-right": ResizeHandle(self, "top-right"),
            "bottom-left": ResizeHandle(self, "bottom-left"),
            "bottom-right": ResizeHandle(self, "bottom-right")
        }
        
        self.update_handle_positions()
        
        # 윈도우 입력 패스스루 설정
        self.install_window_hook()
    
    def install_window_hook(self):
        """윈도우 핸들을 가져와서 입력 패스스루 설정"""
        hwnd = self.winId()
        
        # 윈도우 스타일 확장 속성 설정 - 투명 + 클릭 패스스루
        ex_style = win32gui.GetWindowLong(int(hwnd), win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(
            int(hwnd),
            win32con.GWL_EXSTYLE,
            ex_style | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
        )
    
    def enable_interaction(self, enable=True):
        """상호작용 활성화/비활성화"""
        self.interaction_enabled = enable
        hwnd = self.winId()
        ex_style = win32gui.GetWindowLong(int(hwnd), win32con.GWL_EXSTYLE)
        
        if enable:
            # 클릭 패스스루 비활성화
            win32gui.SetWindowLong(
                int(hwnd),
                win32con.GWL_EXSTYLE,
                ex_style & ~win32con.WS_EX_TRANSPARENT
            )
        else:
            # 클릭 패스스루 활성화
            win32gui.SetWindowLong(
                int(hwnd),
                win32con.GWL_EXSTYLE,
                ex_style | win32con.WS_EX_TRANSPARENT
            )
        
        # 화면 갱신
        self.update()
    
    def update_handle_positions(self):
        """크기 조절 핸들 위치 업데이트"""
        width = self.width()
        height = self.height()
        
        self.resize_handles["top-left"].move(0, 0)
        self.resize_handles["top-right"].move(width - 10, 0)
        self.resize_handles["bottom-left"].move(0, height - 10)
        self.resize_handles["bottom-right"].move(width - 10, height - 10)
    
    def get_monitoring_rect(self):
        """현재 모니터링 영역 가져오기"""
        return QRect(self.x(), self.y(), self.width(), self.height())
    
    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        if event.button() == Qt.LeftButton:
            # 크기 조절 핸들인지 확인
            for handle_name, handle in self.resize_handles.items():
                if handle.geometry().contains(event.pos()):
                    self.resizing = True
                    self.resize_handle = handle_name
                    self.resize_start_geometry = self.geometry()
                    self.setCursor(Qt.SizeFDiagCursor)
                    return
            
            # 드래그 시작
            self.dragging = True
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트"""
        if self.resizing and event.buttons() == Qt.LeftButton:
            # 크기 조절 로직
            delta = event.globalPos() - self.resize_start_geometry.topLeft()
            new_geometry = QRect(self.resize_start_geometry)
            
            if self.resize_handle == "bottom-right":
                new_width = max(50, self.resize_start_geometry.width() + (event.globalPos().x() - self.resize_start_geometry.right()))
                new_height = max(50, self.resize_start_geometry.height() + (event.globalPos().y() - self.resize_start_geometry.bottom()))
                new_geometry.setWidth(new_width)
                new_geometry.setHeight(new_height)
            elif self.resize_handle == "bottom-left":
                new_x = min(self.resize_start_geometry.right() - 50, event.globalPos().x())
                new_width = self.resize_start_geometry.right() - new_x
                new_height = max(50, self.resize_start_geometry.height() + (event.globalPos().y() - self.resize_start_geometry.bottom()))
                new_geometry.setLeft(new_x)
                new_geometry.setHeight(new_height)
            elif self.resize_handle == "top-right":
                new_y = min(self.resize_start_geometry.bottom() - 50, event.globalPos().y())
                new_width = max(50, self.resize_start_geometry.width() + (event.globalPos().x() - self.resize_start_geometry.right()))
                new_height = self.resize_start_geometry.bottom() - new_y
                new_geometry.setTop(new_y)
                new_geometry.setWidth(new_width)
            elif self.resize_handle == "top-left":
                new_x = min(self.resize_start_geometry.right() - 50, event.globalPos().x())
                new_y = min(self.resize_start_geometry.bottom() - 50, event.globalPos().y())
                new_width = self.resize_start_geometry.right() - new_x
                new_height = self.resize_start_geometry.bottom() - new_y
                new_geometry.setLeft(new_x)
                new_geometry.setTop(new_y)
            
            self.setGeometry(new_geometry)
            self.update_handle_positions()
            self.area_changed.emit(self.get_monitoring_rect())
        
        elif self.dragging and event.buttons() == Qt.LeftButton:
            # 드래그 로직
            self.move(event.globalPos() - self.drag_start_position)
            self.area_changed.emit(self.get_monitoring_rect())
    
    def mouseReleaseEvent(self, event):
        """마우스 릴리즈 이벤트"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_handle = None
            self.setCursor(Qt.ArrowCursor)
            self.area_changed.emit(self.get_monitoring_rect())
    
    def paintEvent(self, event):
        """화면 그리기 이벤트"""
        painter = QPainter(self)
        
        # 테두리 펜 설정 (3픽셀 두께로 증가)
        pen = QPen(QColor(255, 0, 0), 3)
        painter.setPen(pen)
        
        # 상호작용 모드일 때만 반투명 배경 적용
        if self.interaction_enabled:
            painter.setBrush(QBrush(QColor(255, 0, 0, 30)))  # 약간 붉은색 반투명 배경
        else:
            painter.setBrush(Qt.NoBrush)  # 내부 채우기 없음 (완전 투명)
            
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)


class TransparentWindow(QMainWindow):
    """투명 오버레이 윈도우"""
    def __init__(self):
        super().__init__()
        
        # 윈도우 설정
        self.setWindowTitle("색상 하이라이트 감지기")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 윈도우 크기 설정
        screen_rect = QApplication.desktop().screenGeometry()
        self.setGeometry(0, 0, screen_rect.width(), screen_rect.height())
        
        # 콘트롤 패널 생성
        self.control_panel = ControlPanel()
        self.control_panel.show()
        
        # 모니터링 영역 창 생성
        self.monitoring_area_window = MonitoringArea()
        self.monitoring_area_window.area_changed.connect(self.update_monitoring_area)
        
        # 색상 감지기 생성
        self.detector = ColorDetector()
        self.detector.color_detected.connect(self.highlight_area)
        
        # 컨트롤 패널 시그널 연결
        self.control_panel.color_changed.connect(self.detector.set_target_color)
        self.control_panel.threshold_changed.connect(self.detector.set_threshold)
        self.control_panel.monitoring_toggled.connect(self.toggle_monitoring)
        self.control_panel.area_interaction_toggled.connect(self.toggle_area_interaction)
        self.control_panel.exit_requested.connect(self.close_application)
        
        # 하이라이트 정보와 타이머
        self.highlight_points = []  # 하이라이트할 색상 위치 목록
        self.highlight_timer = QTimer()
        self.highlight_timer.timeout.connect(self.clear_highlight)
        
        # 윈도우 입력 패스스루 설정
        self.install_window_hook()
        
        # 초기 모니터링 영역 설정
        self.update_monitoring_area(self.monitoring_area_window.get_monitoring_rect())
    
    def install_window_hook(self):
        """윈도우 핸들을 가져와서 입력 패스스루 설정"""
        hwnd = self.winId()
        
        # 윈도우 스타일 확장 속성 설정 - 투명 + 클릭 패스스루
        ex_style = win32gui.GetWindowLong(int(hwnd), win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(
            int(hwnd),
            win32con.GWL_EXSTYLE,
            ex_style | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
        )
    
    def toggle_monitoring(self, enabled):
        """모니터링 시작/중지"""
        if enabled:
            self.detector.set_monitoring_area(self.monitoring_area_window.get_monitoring_rect())
            self.detector.start_monitoring()
        else:
            self.detector.stop_monitoring()
    
    def toggle_area_interaction(self, enabled):
        """모니터링 영역 상호작용 토글"""
        if enabled:
            self.monitoring_area_window.enable_interaction(True)
            self.monitoring_area_window.show()
        else:
            self.monitoring_area_window.enable_interaction(False)
    
    def update_monitoring_area(self, rect):
        """모니터링 영역 업데이트"""
        self.detector.set_monitoring_area(rect)
        self.control_panel.update_selection_info(rect)
    
    def highlight_area(self, points, color):
        """색상 발견 위치 하이라이트"""
        self.highlight_points = points
        self.update()
        
        # 하이라이트 타이머 설정
        self.highlight_timer.start(500)  # 0.5초 동안 하이라이트 표시
    
    def clear_highlight(self):
        """하이라이트 제거"""
        self.highlight_points = []
        self.highlight_timer.stop()
        self.update()
    
    def close_application(self):
        """애플리케이션 종료"""
        self.detector.stop_monitoring()
        self.close()
        self.control_panel.close()
        self.monitoring_area_window.close()
        QApplication.quit()
    
    def paintEvent(self, event):
        """화면 그리기 이벤트"""
        painter = QPainter(self)
        
        # 발견된 색상 위치에 마젠타색 테두리 정사각형 그리기
        if self.highlight_points:
            # 마젠타색 펜 설정 (굵기 2픽셀)
            pen = QPen(QColor(255, 0, 255), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)  # 채우기 없음
            
            # 각 위치에 10x10 크기의 정사각형 그리기
            for point in self.highlight_points:
                rect = QRect(point.x() - 5, point.y() - 5, 10, 10)  # 포인트를 중심으로 10x10 사각형
                painter.drawRect(rect)


class ControlPanel(QWidget):
    """컨트롤 패널 위젯"""
    color_changed = pyqtSignal(QColor)
    threshold_changed = pyqtSignal(int)
    monitoring_toggled = pyqtSignal(bool)
    area_interaction_toggled = pyqtSignal(bool)
    exit_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # 윈도우 설정
        self.setWindowTitle("컨트롤 패널")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setFixedSize(300, 250)  # 크기 조금 줄임
        
        # 레이아웃 설정
        layout = QVBoxLayout()
        
        # 색상 선택 버튼
        color_layout = QHBoxLayout()
        self.color_label = QLabel("타겟 색상:")
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setStyleSheet("background-color: #FF0000; border: 1px solid black;")
        self.color_btn = QPushButton("색상 선택")
        self.color_btn.clicked.connect(self.select_color)
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_btn)
        layout.addLayout(color_layout)
        
        # 임계값 슬라이더
        threshold_layout = QHBoxLayout()
        self.threshold_label = QLabel("색상 인식 임계값:")
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(1)
        self.threshold_slider.setMaximum(50)
        self.threshold_slider.setValue(10)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        self.threshold_display = QLabel("10")
        threshold_layout.addWidget(self.threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_display)
        layout.addLayout(threshold_layout)
        
        # 색상 범위 표시
        self.color_range_label = QLabel("색상 감지 범위:")
        self.color_range_display = QLabel()
        self.color_range_display.setWordWrap(True)
        color_range_layout = QHBoxLayout()
        color_range_layout.addWidget(self.color_range_label)
        color_range_layout.addWidget(self.color_range_display)
        layout.addLayout(color_range_layout)
        
        # 최소/최대 색상 미리보기
        min_max_preview_layout = QHBoxLayout()
        self.min_color_preview = QLabel()
        self.min_color_preview.setFixedSize(30, 30)
        self.min_color_preview.setStyleSheet("border: 1px solid black;")
        self.max_color_preview = QLabel()
        self.max_color_preview.setFixedSize(30, 30)
        self.max_color_preview.setStyleSheet("border: 1px solid black;")
        min_max_preview_layout.addWidget(QLabel("최소:"))
        min_max_preview_layout.addWidget(self.min_color_preview)
        min_max_preview_layout.addWidget(QLabel("최대:"))
        min_max_preview_layout.addWidget(self.max_color_preview)
        min_max_preview_layout.addStretch()
        layout.addLayout(min_max_preview_layout)
        
        # 모니터링 영역 버튼
        self.area_select_btn = QPushButton("모니터링 영역 조절 모드")
        self.area_select_btn.setCheckable(True)
        self.area_select_btn.toggled.connect(self.area_interaction_toggled)
        layout.addWidget(self.area_select_btn)
        
        # 선택 영역 정보
        self.selection_info = QLabel("모니터링 영역: [100, 100, 300x300]")
        layout.addWidget(self.selection_info)
        
        # 모니터링 토글 버튼
        self.monitor_btn = QPushButton("모니터링 시작")
        self.monitor_btn.setCheckable(True)
        self.monitor_btn.toggled.connect(self.toggle_monitoring)
        layout.addWidget(self.monitor_btn)
        
        # 상태 표시
        self.status_label = QLabel("대기 중...")
        layout.addWidget(self.status_label)
        
        # 종료 버튼
        self.exit_btn = QPushButton("종료")
        self.exit_btn.clicked.connect(self.exit_requested)
        layout.addWidget(self.exit_btn)
        
        self.setLayout(layout)
        
        # 현재 타겟 색상
        self.current_color = QColor(255, 0, 0)
        
        # 초기 색상 범위 표시 업데이트
        self.update_color_range(self.current_color, 10)
    
    def select_color(self):
        """색상 선택 다이얼로그 표시"""
        color = QColorDialog.getColor(self.current_color, self, "타겟 색상 선택")
        if color.isValid():
            self.current_color = color
            self.color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
            self.update_color_range(color, self.threshold_slider.value())
            self.color_changed.emit(color)
    
    def update_threshold(self, value):
        """임계값 업데이트 및 색상 범위 표시 업데이트"""
        self.threshold_display.setText(str(value))
        self.update_color_range(self.current_color, value)
        self.threshold_changed.emit(value)
    
    def update_color_range(self, color, threshold):
        """색상 범위 업데이트 및 표시"""
        # RGB 값 가져오기
        r, g, b = color.red(), color.green(), color.blue()
        
        # 임계값을 반영한 최소/최대 RGB 계산
        min_r = max(0, r - threshold)
        min_g = max(0, g - threshold)
        min_b = max(0, b - threshold)
        
        max_r = min(255, r + threshold)
        max_g = min(255, g + threshold)
        max_b = min(255, b + threshold)
        
        # 최소/최대 HEX 색상 생성
        min_hex = f"#{min_r:02X}{min_g:02X}{min_b:02X}"
        max_hex = f"#{max_r:02X}{max_g:02X}{max_b:02X}"
        
        # UI 업데이트
        self.color_range_display.setText(f"{min_hex} ~ {max_hex}")
        self.min_color_preview.setStyleSheet(f"background-color: {min_hex}; border: 1px solid black;")
        self.max_color_preview.setStyleSheet(f"background-color: {max_hex}; border: 1px solid black;")
    
    def toggle_monitoring(self, enabled):
        """모니터링 시작/중지"""
        if enabled:
            self.monitor_btn.setText("모니터링 중지")
            self.status_label.setText("모니터링 중...")
        else:
            self.monitor_btn.setText("모니터링 시작")
            self.status_label.setText("대기 중...")
        self.monitoring_toggled.emit(enabled)
    
    def update_selection_info(self, rect):
        """선택 영역 정보 업데이트"""
        if rect:
            self.selection_info.setText(f"모니터링 영역: [{rect.x()}, {rect.y()}, {rect.width()}x{rect.height()}]")
        else:
            self.selection_info.setText("모니터링 영역: 없음")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()
    sys.exit(app.exec_())
