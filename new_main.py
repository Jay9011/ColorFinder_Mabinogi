"""
색상 하이라이트 감지기 애플리케이션 - 메인 실행 파일
"""
import sys
from PyQt5.QtWidgets import QApplication

from src.controllers.app_controller import AppController


def main():
    """애플리케이션 시작점"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 컨트롤러 생성 및 시작
    controller = AppController()
    controller.start()
    
    # 애플리케이션 실행
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
