from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
import sys


def main():
    app = QApplication(sys.argv)
    with open("resources/style.qss", "r") as f:
        app.setStyleSheet(f.read())
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
