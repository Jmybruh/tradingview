from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import pyqtSignal


class AnalysisPage(QWidget):
    symbol_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.table = QTableWidget()
        layout.addWidget(self.table)

        headers = ["RANK", "COIN_PAIR", "PERCENT_TO_NEAR_TO_PRICE", "HOURS_SINCE_LAST_TOUCH",
                   "MAX_PERCENT_MOVED_SINCE_LAST_TOUCH"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.populate_table()
        self.table.cellClicked.connect(self.handle_row_click)

    def populate_table(self):
        data = [
            [1, "BTCUSDT", -0.12, 3.5, -2.1],
            [2, "ETHUSDT", 0.03, 6.7, 1.8],
        ]
        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, val in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))

    def handle_row_click(self, row, column):
        symbol_item = self.table.item(row, 1)
        if symbol_item:
            self.symbol_selected.emit(symbol_item.text())
