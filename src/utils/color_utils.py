"""
색상 관련 유틸리티 함수 모듈
"""
from PyQt5.QtGui import QColor


def calculate_color_range(color, threshold):
    """
    주어진 색상과 임계값으로 색상 범위를 계산합니다.
    
    Args:
        color (QColor): 기준 색상
        threshold (int): 색상 임계값
        
    Returns:
        tuple: (min_color, max_color, min_hex, max_hex) 형태의 튜플
    """
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
    
    # 최소/최대 QColor 객체 생성
    min_color = QColor(min_r, min_g, min_b)
    max_color = QColor(max_r, max_g, max_b)
    
    return min_color, max_color, min_hex, max_hex


def is_color_in_range(check_color, target_color, threshold):
    """
    주어진 색상이 타겟 색상과 임계값 내에 있는지 확인합니다.
    
    Args:
        check_color (tuple): 확인할 색상 (r, g, b)
        target_color (QColor): 타겟 색상
        threshold (int): 색상 임계값
        
    Returns:
        bool: 범위 내에 있으면 True, 아니면 False
    """
    check_r, check_g, check_b = check_color
    target_r, target_g, target_b = target_color.red(), target_color.green(), target_color.blue()
    
    # 각 채널별로 임계값 내에 있는지 확인 (오버플로우 방지를 위해 int 변환)
    r_in_range = abs(int(check_r) - int(target_r)) <= threshold
    g_in_range = abs(int(check_g) - int(target_g)) <= threshold
    b_in_range = abs(int(check_b) - int(target_b)) <= threshold
    
    # 모든 채널이 임계값 내에 있어야 True
    return r_in_range and g_in_range and b_in_range
