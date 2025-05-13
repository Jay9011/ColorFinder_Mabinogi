"""
색상 감지 및 분석을 위한 모델 클래스
"""
import numpy as np
from PIL import ImageGrab
from PyQt5.QtCore import QObject, QTimer, QRect, pyqtSignal, QPoint
from PyQt5.QtGui import QColor

from src.utils.color_utils import is_color_in_range


class ColorDetector(QObject):
    """색상 감지 및 분석을 위한 클래스"""
    color_detected = pyqtSignal(list, QColor)  # 색상 감지 시 신호 발생 (위치 목록과 색상)
    debug_pixel_info = pyqtSignal(QPoint, QColor)  # 디버깅 모드에서 픽셀 정보 신호
    
    def __init__(self, target_color=QColor(255, 0, 0), threshold=10):
        super().__init__()
        self.target_color = target_color
        self.threshold = threshold
        self.monitoring_area = QRect(0, 0, 300, 300)
        self.is_monitoring = False
        self.debug_mode = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_colors)
        
        # 이전에 찾은 색상 위치 저장
        self.last_match_points = []
        self.last_target_color = None
    
    def start_monitoring(self):
        """모니터링 시작"""
        self.is_monitoring = True
        self.timer.start(100)  # 100ms 간격으로 체크
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_monitoring = False
        self.timer.stop()
        # 모니터링 중지 시 저장된 포인트 초기화
        self.last_match_points = []
    
    def set_target_color(self, color):
        """타겟 색상 설정"""
        # 타겟 색상이 변경되면 저장된 포인트 초기화
        if self.target_color != color:
            self.last_match_points = []
            self.last_target_color = None
        self.target_color = color
    
    def set_threshold(self, value):
        """색상 감지 임계값 설정"""
        # 임계값이 변경되면 저장된 포인트 초기화
        if self.threshold != value:
            self.last_match_points = []
            self.last_target_color = None
        self.threshold = value
    
    def set_monitoring_area(self, rect):
        """모니터링 영역 설정"""
        # 모니터링 영역이 변경되면 저장된 포인트 초기화
        if self.monitoring_area != rect:
            self.last_match_points = []
            self.last_target_color = None
        self.monitoring_area = rect
    
    def set_debug_mode(self, enabled):
        """디버깅 모드 설정"""
        self.debug_mode = enabled
    
    def check_colors(self):
        """화면에서 색상 체크"""
        if not self.is_monitoring:
            return
            
        try:
            # 모니터링 영역 스크린샷 캡처
            x, y, w, h = self.monitoring_area.x(), self.monitoring_area.y(), self.monitoring_area.width(), self.monitoring_area.height()
            
            # 타겟 색상 RGB 값
            target_r, target_g, target_b = self.target_color.red(), self.target_color.green(), self.target_color.blue()
            
            # 이전에 찾은 위치가 있고 색상이 변경되지 않았으면 해당 위치만 먼저 확인
            if self.last_match_points and self.last_target_color == self.target_color:
                # 각 포인트의 현재 색상 확인
                valid_points = []
                screenshot = None  # 필요할 때만 스크린샷 캡처
                
                for point in self.last_match_points:
                    # 이 포인트가 현재 모니터링 영역 내에 있는지 확인
                    if not self.monitoring_area.contains(point):
                        continue
                    
                    # 스크린샷이 아직 없으면 캡처
                    if screenshot is None:
                        screenshot = ImageGrab.grab(bbox=(x, y, x+w, y+h))
                        img_array = np.array(screenshot)
                    
                    # 화면 좌표에서 스크린샷 상대 좌표로 변환
                    px = point.x() - x
                    py = point.y() - y
                    
                    # 스크린샷 범위 내에 있는지 확인
                    if 0 <= px < w and 0 <= py < h:
                        # 해당 픽셀의 색상 추출
                        pixel_color = img_array[py, px]
                        
                        # 색상이 타겟 색상 범위 내에 있는지 확인
                        if is_color_in_range(pixel_color, self.target_color, self.threshold):
                            valid_points.append(point)
                
                # 이전에 찾은 위치 중 일부가 여전히 유효하면 해당 위치만 신호 발생
                if valid_points:
                    self.color_detected.emit(valid_points, self.target_color)
                    self.last_match_points = valid_points
                    return
            
            # 이전 위치가 없거나 더 이상 유효하지 않으면 전체 스캔
            screenshot = ImageGrab.grab(bbox=(x, y, x+w, y+h))
            img_array = np.array(screenshot)
            
            # 디버그 모드인 경우 마우스 포인터 위치의 픽셀 색상 확인
            if self.debug_mode:
                cursor_pos = QCursor().pos()
                if self.monitoring_area.contains(cursor_pos):
                    # 화면 좌표에서 스크린샷 상대 좌표로 변환
                    px = cursor_pos.x() - x
                    py = cursor_pos.y() - y
                    
                    # 스크린샷 범위 내에 있는지 확인
                    if 0 <= px < w and 0 <= py < h:
                        # 해당 픽셀의 색상 추출
                        pixel_color = img_array[py, px]
                        cursor_color = QColor(pixel_color[0], pixel_color[1], pixel_color[2])
                        
                        # 디버그 정보 신호 발생
                        self.debug_pixel_info.emit(cursor_pos, cursor_color)
                        
                        # 콘솔에 색상 정보 출력
                        hex_color = f"#{pixel_color[0]:02X}{pixel_color[1]:02X}{pixel_color[2]:02X}"
                        print(f"Cursor at ({cursor_pos.x()}, {cursor_pos.y()}) - RGB: {pixel_color} - HEX: {hex_color}")
            
            # 1x1 픽셀 모드로 전체 스캔 (다른 모드는 제거됨)
            match_points = self._check_colors_pixel_mode(img_array, target_r, target_g, target_b, x, y)
            
            # 색상 감지 결과 신호 발생
            if match_points:
                self.color_detected.emit(match_points, self.target_color)
                self.last_match_points = match_points
                self.last_target_color = self.target_color
            else:
                # 감지된 색상이 없으면 목록 초기화
                self.last_match_points = []
                # 신호는 빈 목록으로 발생 (UI 업데이트용)
                self.color_detected.emit([], self.target_color)
        
        except Exception as e:
            print(f"Error in color detection: {e}")
            self.last_match_points = []
    
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
        
        # 이미 하이라이트된 영역 추적 (이미 있는 포인트 주변 10x10 영역 제외)
        excluded_regions = []
        for point in self.last_match_points:
            px = point.x() - base_x  # 상대 좌표로 변환
            py = point.y() - base_y
            # 10x10 네모칸 영역
            excluded_regions.append((px-5, py-5, px+5, py+5))
            
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
                        for ex_x1, ex_y1, ex_x2, ex_y2 in excluded_regions:
                            if ex_x1 <= x <= ex_x2 and ex_y1 <= y <= ex_y2:
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
