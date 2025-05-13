"""
컨트롤 패널 위젯 모듈
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QColorDialog, QSlider, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QColor


class ControlPanel(QWidget):
    """컨트롤 패널 위젯"""
    color_changed = pyqtSignal(QColor)
    threshold_changed = pyqtSignal(int)
    monitoring_toggled = pyqtSignal(bool)
    area_interaction_toggled = pyqtSignal(bool)
    debug_mode_toggled = pyqtSignal(bool)
    exit_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # 윈도우 설정
        self.setWindowTitle("컨트롤 패널")
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(300)
        
        # 레이아웃 생성
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 색상 선택 영역
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("타겟 색상:"))
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setStyleSheet("background-color: #FF0000; border: 1px solid black;")
        color_layout.addWidget(self.color_preview)
        self.color_btn = QPushButton("색상 선택")
        self.color_btn.clicked.connect(self.select_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # 임계값 조절 영역
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("임계값:"))
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(1, 50)
        self.threshold_slider.setValue(10)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        threshold_layout.addWidget(self.threshold_slider)
        self.threshold_display = QSpinBox()
        self.threshold_display.setRange(1, 50)
        self.threshold_display.setValue(10)
        self.threshold_display.valueChanged.connect(self.threshold_slider.setValue)
        threshold_layout.addWidget(self.threshold_display)
        layout.addLayout(threshold_layout)
        
        # 색상 범위 표시
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("색상 범위:"))
        self.color_range_display = QLabel("#000000 ~ #000000")
        range_layout.addWidget(self.color_range_display)
        layout.addLayout(range_layout)
        
        # 색상 범위 미리보기
        min_max_preview_layout = QHBoxLayout()
        self.min_color_preview = QLabel()
        self.min_color_preview.setFixedSize(30, 30)
        self.min_color_preview.setStyleSheet("background-color: #000000; border: 1px solid black;")
        self.max_color_preview = QLabel()
        self.max_color_preview.setFixedSize(30, 30)
        self.max_color_preview.setStyleSheet("background-color: #000000; border: 1px solid black;")
        min_max_preview_layout.addWidget(QLabel("최소:"))
        min_max_preview_layout.addWidget(self.min_color_preview)
        min_max_preview_layout.addWidget(QLabel("최대:"))
        min_max_preview_layout.addWidget(self.max_color_preview)
        min_max_preview_layout.addStretch()
        layout.addLayout(min_max_preview_layout)
        
        # 디버깅 모드 토글 버튼
        self.debug_checkbox = QCheckBox("디버깅 모드 (마우스 아래 픽셀 색상 확인)")
        self.debug_checkbox.toggled.connect(self.debug_toggled)
        layout.addWidget(self.debug_checkbox)
        
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
        self.threshold_display.setValue(value)
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
    
    def debug_toggled(self, enabled):
        """디버깅 모드 토글"""
        self.debug_mode_toggled.emit(enabled)
        if enabled:
            self.status_label.setText("디버깅 모드 활성화 - 마우스 아래 픽셀 색상 확인 중...")
        else:
            if self.monitor_btn.isChecked():
                self.status_label.setText("모니터링 중...")
            else:
                self.status_label.setText("대기 중...")
    
    def update_selection_info(self, rect):
        """선택 영역 정보 업데이트"""
        if rect:
            self.selection_info.setText(f"모니터링 영역: [{rect.x()}, {rect.y()}, {rect.width()}x{rect.height()}]")
        else:
            self.selection_info.setText("모니터링 영역: 없음")
