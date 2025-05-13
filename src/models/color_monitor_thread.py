"""
색상 모니터링을 위한 쓰레드 클래스
"""
from PyQt5.QtCore import QThread, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QColor
import numpy as np
from PIL import ImageGrab


class ColorMonitorThread(QThread):
    """색상 모니터링을 담당하는 쓰레드 클래스"""
    
    # 신호 정의
    color_detected = pyqtSignal(list, QColor, int)  # 감지된 포인트 목록, 색상, 색상 인덱스
    
    def __init__(self, color_index, target_color=QColor(255, 0, 0), threshold=10):
        """
        Args:
            color_index: 색상 인덱스 (0, 1, 2 중 하나)
            target_color: 탐지할 타겟 색상
            threshold: 색상 임계값
        """
        super().__init__()
        
        self.color_index = color_index
        self.target_color = target_color
        self.threshold = threshold
        self.monitoring_area = QRect(0, 0, 300, 300)
        
        # 감지 관련 변수
        self.is_monitoring = False
        self.last_match_points = []
        
        # 하이라이트된 영역 추적
        self.highlighted_areas = []
    
    def set_target_color(self, color):
        """타겟 색상 설정"""
        if self.target_color != color:
            self.last_match_points = []
            self.highlighted_areas = []
        self.target_color = color
    
    def set_threshold(self, value):
        """임계값 설정"""
        if self.threshold != value:
            self.last_match_points = []
            self.highlighted_areas = []
        self.threshold = value
    
    def set_monitoring_area(self, rect):
        """모니터링 영역 설정"""
        if self.monitoring_area != rect:
            self.last_match_points = []
            self.highlighted_areas = []
        self.monitoring_area = rect
    
    def start_monitoring(self):
        """모니터링 시작"""
        self.is_monitoring = True
        if not self.isRunning():
            self.start()
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_monitoring = False
        self.last_match_points = []
        self.highlighted_areas = []
    
    def add_highlighted_area(self, point):
        """하이라이트된 영역 추가 (10x10 픽셀 사각형)"""
        x, y = point.x(), point.y()
        self.highlighted_areas.append((x-5, y-5, x+5, y+5))
    
    def run(self):
        """쓰레드 실행 메소드"""
        while True:
            if self.is_monitoring:
                try:
                    # 모니터링 영역 캡처
                    x, y, w, h = self.monitoring_area.x(), self.monitoring_area.y(), self.monitoring_area.width(), self.monitoring_area.height()
                    screenshot = ImageGrab.grab(bbox=(x, y, x+w, y+h))
                    img_array = np.array(screenshot)
                    
                    # 타겟 색상 추출
                    target_r, target_g, target_b = self.target_color.red(), self.target_color.green(), self.target_color.blue()
                    
                    # 색상 검사 수행
                    match_points = self._check_colors_pixel_mode(img_array, target_r, target_g, target_b, x, y)
                    
                    # 감지된 색상이 있으면 신호 발생
                    if match_points:
                        # 신호 발생 및 하이라이트 영역 업데이트
                        for point in match_points:
                            self.add_highlighted_area(point)
                        self.last_match_points = match_points
                        self.color_detected.emit(match_points, self.target_color, self.color_index)
                    elif match_points != self.last_match_points:
                        # 감지된 위치가 변경되면 빈 목록으로 신호 발생
                        self.last_match_points = []
                        self.color_detected.emit([], self.target_color, self.color_index)
                
                except Exception as e:
                    print(f"Thread {self.color_index} error: {str(e)}")
                    self.last_match_points = []
            
            # 잠시 대기 (CPU 사용량 감소)
            self.msleep(100)  # 100ms 대기
    
    def _check_colors_pixel_mode(self, img_array, target_r, target_g, target_b, base_x, base_y):
        """
        1x1 픽셀 모드로 색상 검사 (영역을 4x4로 나누어 각 영역당 최대 1개 포인트만 수집)
        
        Args:
            img_array: 이미지 배열
            target_r, target_g, target_b: 타겟 RGB 값
            base_x, base_y: 기준 좌표 (모니터링 영역의 좌상단)
            
        Returns:
            list: 일치하는 픽셀 위치의 QPoint 목록
        """
        height, width = img_array.shape[:2]
        
        # 4x4 격자로 영역 나누기
        grid_width = width // 4
        grid_height = height // 4
        
        # 각 격자별로 최대 1개의 포인트만 수집
        match_points = []
        
        for grid_row in range(4):
            for grid_col in range(4):
                # 현재 격자 영역 계산
                start_x = grid_col * grid_width
                start_y = grid_row * grid_height
                end_x = start_x + grid_width
                end_y = start_y + grid_height
                
                # 격자 영역 범위 조정 (이미지 범위를 벗어나지 않도록)
                end_x = min(end_x, width)
                end_y = min(end_y, height)
                
                # 현재 격자에서 일치하는 포인트 찾기
                for y in range(start_y, end_y, 2):  # 2픽셀 건너뛰기 (성능 향상)
                    found_in_grid = False
                    for x in range(start_x, end_x, 2):  # 2픽셀 건너뛰기
                        # 이미 하이라이트된 영역인지 확인
                        skip = False
                        for ex_x1, ex_y1, ex_x2, ex_y2 in self.highlighted_areas:
                            if ex_x1 <= x+base_x <= ex_x2 and ex_y1 <= y+base_y <= ex_y2:
                                skip = True
                                break
                        if skip:
                            continue
                        
                        # RGB 값 확인
                        pixel = img_array[y, x]
                        r, g, b = pixel[0], pixel[1], pixel[2]
                        
                        # 각 채널별로 임계값 내에 있는지 확인 (오버플로우 방지)
                        r_match = abs(int(r) - int(target_r)) <= self.threshold
                        g_match = abs(int(g) - int(target_g)) <= self.threshold
                        b_match = abs(int(b) - int(target_b)) <= self.threshold
                        
                        # 모든 채널이 일치하면 위치 추가
                        if r_match and g_match and b_match:
                            # 이 격자에서 처음 발견한 포인트
                            abs_point = QPoint(base_x + x, base_y + y)  # 절대 좌표로 변환
                            match_points.append(abs_point)
                            found_in_grid = True
                            break  # 현재 격자에서 초기 발견 후 나가감
                    
                    if found_in_grid:
                        break  # 다음 격자로 이동
        
        return match_points
