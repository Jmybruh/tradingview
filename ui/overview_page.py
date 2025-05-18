from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout, QHeaderView
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, QObject, Qt
import requests
import websocket
import json

WATCHLIST_SYMBOLS = ["btcusdt", "ethusdt", "bnbusdt"]


class PriceStreamWorker(QObject):
    price_update = pyqtSignal(str, float)

    def __init__(self):
        super().__init__()
        self.ws = None
        self.running = False

    def start_stream(self):
        def on_message(ws, message):
            msg = json.loads(message)
            data = msg.get('data', {})
            symbol = data.get('s', '').lower()
            price = float(data.get('c', 0))
            self.price_update.emit(symbol, price)

        def on_error(ws, error):
            print("WebSocket error:", error)

        def on_close(ws, close_status_code, close_msg):
            print("WebSocket closed")

        stream_url = f"wss://stream.binance.com:9443/stream?streams=" + "/".join(
            [f"{s}@ticker" for s in WATCHLIST_SYMBOLS])
        self.ws = websocket.WebSocketApp(stream_url,
                                         on_message=on_message,
                                         on_error=on_error,
                                         on_close=on_close)
        self.running = True
        self.ws.run_forever()

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()


class OverviewPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Market Overview"))

        self.top_layout = QHBoxLayout()
        layout.addLayout(self.top_layout)

        self.gainers_table = QTableWidget()
        self.losers_table = QTableWidget()
        self.watchlist_table = QTableWidget()

        self.top_layout.addWidget(self.gainers_table)
        self.top_layout.addWidget(self.losers_table)
        self.top_layout.addWidget(self.watchlist_table)

        self.init_watchlist_table()
        self.load_snapshot_data()

        # Timer to refresh gainers/losers every 5 minutes
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_snapshot_data)
        self.timer.start(300000)

        # WebSocket thread for live prices
        self.thread = QThread()
        self.worker = PriceStreamWorker()
        self.worker.moveToThread(self.thread)
        self.worker.price_update.connect(self.update_watchlist_price)
        self.thread.started.connect(self.worker.start_stream)
        self.thread.start()

        self.symbol_to_row = {symbol.upper(): idx for idx, symbol in enumerate(WATCHLIST_SYMBOLS)}

    def init_watchlist_table(self):
        self.watchlist_table.setColumnCount(2)
        self.watchlist_table.setRowCount(len(WATCHLIST_SYMBOLS))
        self.watchlist_table.setHorizontalHeaderLabels(["Symbol", "Last Price"])
        for idx, symbol in enumerate(WATCHLIST_SYMBOLS):
            self.watchlist_table.setItem(idx, 0, QTableWidgetItem(symbol.upper()))
            self.watchlist_table.setItem(idx, 1, QTableWidgetItem("Loading..."))
        self.watchlist_table.setMinimumWidth(250)
        self.watchlist_table.setMaximumWidth(300)
        self.watchlist_table.setStyleSheet("QHeaderView::section { background-color: #2a2a2a; color: #e0e0e0; }")
        self.watchlist_table.horizontalHeader().setStretchLastSection(True)
        self.watchlist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.watchlist_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def update_watchlist_price(self, symbol, price):
        row = self.symbol_to_row.get(symbol.upper())
        if row is not None:
            self.watchlist_table.setItem(row, 1, QTableWidgetItem(f"${price:.2f}"))

    def load_snapshot_data(self):
        url = "https://api.binance.com/api/v3/ticker/24hr"
        try:
            data = requests.get(url).json()
        except Exception as e:
            print("Failed to fetch data:", e)
            return

        df = [
            {
                "symbol": item["symbol"],
                "priceChangePercent": float(item["priceChangePercent"]),
                "lastPrice": float(item["lastPrice"])
            }
            for item in data if item["symbol"].endswith("USDT")
        ]

        top_gainers = sorted(df, key=lambda x: -x["priceChangePercent"])[:5]
        top_losers = sorted(df, key=lambda x: x["priceChangePercent"])[:5]

        self.populate_table(self.gainers_table, top_gainers, "Top Gainers")
        self.populate_table(self.losers_table, top_losers, "Top Losers")

    def populate_table(self, table, data, title):
        table.setColumnCount(3)
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(["Symbol", "% Change", "Last Price"])
        table.setMinimumWidth(250)
        table.setMaximumWidth(300)
        table.setSortingEnabled(False)

        for row, item in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(item["symbol"]))
            table.setItem(row, 1, QTableWidgetItem(f"{item['priceChangePercent']:.2f}%"))
            table.setItem(row, 2, QTableWidgetItem(f"${item['lastPrice']:.2f}"))

        table.setVerticalHeaderLabels([""] * len(data))
        table.setStyleSheet("QHeaderView::section { background-color: #2a2a2a; color: #e0e0e0; }")
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setWindowTitle(title)
