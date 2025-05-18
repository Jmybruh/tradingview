from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QStackedLayout, QHBoxLayout
from ui.chart_page import ChartPage
from ui.analysis_page import AnalysisPage
from ui.overview_page import OverviewPage


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading View App")
        self.resize(1200, 800)

        main_layout = QHBoxLayout(self)
        self.sidebar = QListWidget()
        self.sidebar.addItems(["Overview", "Analysis", "Chart View"])
        self.sidebar.currentRowChanged.connect(self.display_page)

        self.overview_page = OverviewPage()
        self.analysis_page = AnalysisPage()
        self.chart_page = ChartPage()

        self.analysis_page.symbol_selected.connect(self.chart_page.update_symbol)

        self.pages = QStackedLayout()
        self.pages.addWidget(self.overview_page)
        self.pages.addWidget(self.analysis_page)
        self.pages.addWidget(self.chart_page)

        main_layout.addWidget(self.sidebar, 1)
        container = QWidget()
        container.setLayout(self.pages)
        main_layout.addWidget(container, 4)

    def display_page(self, index):
        self.pages.setCurrentIndex(index)
