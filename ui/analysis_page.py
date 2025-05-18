from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import pyqtSignal, QTimer
from data.binance_api import get_ohlcv
import pandas as pd


class AnalysisPage(QWidget):
    symbol_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.headers = [
            "RANK", "COIN_PAIR", "PERCENT_TO_NEAR_TO_PRICE",
            "HOURS_SINCE_LAST_TOUCH", "MAX_PERCENT_MOVED_SINCE_LAST_TOUCH"
        ]
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)

        self.symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"]
        self.timer = QTimer()
        self.timer.timeout.connect(self.populate_table)
        self.timer.start(300000)  # every 5 minutes
        self.populate_table()

        self.table.cellClicked.connect(self.handle_row_click)

    def populate_table(self):
        results = []

        for symbol in self.symbols:
            try:
                df = get_ohlcv(symbol, interval='1h', limit=200)
                df['EMA50'] = df['Close'].ewm(span=50).mean()

                current_price = df['Close'].iloc[-1]
                current_ema = df['EMA50'].iloc[-1]
                percent_to_ema = ((current_price - current_ema) / current_price) * 100

                # Find last touch to EMA
                touch_index = None
                for i in range(len(df) - 2, 0, -1):
                    if abs(df['Close'].iloc[i] - df['EMA50'].iloc[i]) / df['Close'].iloc[i] < 0.01:
                        touch_index = i
                        break

                if touch_index is not None:
                    hours_since = (len(df) - 1 - touch_index)
                    max_move = ((df['Close'].iloc[-1] - df['Close'].iloc[touch_index]) / df['Close'].iloc[
                        touch_index]) * 100
                else:
                    hours_since = -1
                    max_move = 0.0

                results.append([symbol, percent_to_ema, hours_since, max_move])

            except Exception as e:
                print(f"Error loading {symbol}: {e}")
                results.append([symbol, 0.0, -1, 0.0])

        # Sort by proximity to EMA
        sorted_data = sorted(results, key=lambda x: abs(x[1]))
        self.table.setRowCount(len(sorted_data))

        for i, row in enumerate(sorted_data):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(row[0]))
            self.table.setItem(i, 2, QTableWidgetItem(f"{row[1]:.2f}%"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{row[2]}h" if row[2] >= 0 else "N/A"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{row[3]:.2f}%"))

    def handle_row_click(self, row, column):
        symbol_item = self.table.item(row, 1)
        if symbol_item:
            self.symbol_selected.emit(symbol_item.text())
