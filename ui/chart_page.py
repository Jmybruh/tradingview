from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import mplfinance as mpf
import pandas as pd
import pandas_ta as ta
import websocket
import json
from data.binance_api import get_ohlcv


class KlineStreamWorker(QObject):
    kline_received = pyqtSignal(dict)

    def __init__(self, symbol, interval='1m'):
        super().__init__()
        self.symbol = symbol.lower()
        self.interval = interval
        self.ws = None

    def start_stream(self):
        def on_message(ws, message):
            msg = json.loads(message)
            kline = msg.get("k", {})
            if kline.get("x"):  # only emit on closed candles
                self.kline_received.emit(kline)

        def on_error(ws, error):
            print("WebSocket Error:", error)

        def on_close(ws, code, reason):
            print("WebSocket Closed")

        url = f"wss://stream.binance.com:9443/ws/{self.symbol}@kline_{self.interval}"
        self.ws = websocket.WebSocketApp(url, on_message=on_message,
                                         on_error=on_error, on_close=on_close)
        self.ws.run_forever()

    def stop(self):
        if self.ws:
            self.ws.close()


class ChartPage(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.symbol_box = QComboBox()
        self.symbol_box.addItems(["BTCUSDT", "ETHUSDT", "BNBUSDT"])
        self.symbol_box.currentTextChanged.connect(self.symbol_changed)
        self.layout.addWidget(self.symbol_box)

        self.canvas = None
        self.df = None
        self.thread = None
        self.worker = None

        self.alert_label = QLabel("")
        self.alert_label.setStyleSheet("color: red; font-weight: bold;")
        self.layout.addWidget(self.alert_label)

        self.symbol_changed(self.symbol_box.currentText())

    def symbol_changed(self, symbol):
        self.df = get_ohlcv(symbol, interval='1m', limit=100)
        self.plot_chart()

        if self.thread:
            self.worker.stop()
            self.thread.quit()
            self.thread.wait()

        self.thread = QThread()
        self.worker = KlineStreamWorker(symbol)
        self.worker.moveToThread(self.thread)
        self.worker.kline_received.connect(self.process_kline)
        self.thread.started.connect(self.worker.start_stream)
        self.thread.start()

    def process_kline(self, k):
        dt = pd.to_datetime(k['t'], unit='ms')
        o, h, l, c, v = map(float, [k['o'], k['h'], k['l'], k['c'], k['v']])

        if dt not in self.df.index:
            self.df.loc[dt] = [o, h, l, c, v]
        else:
            self.df.loc[dt] = [o, h, l, c, v]

        self.df = self.df.sort_index().tail(100)

        if len(self.df) > 2:
            prev_close = self.df['Close'].iloc[-2]
            price_change_pct = ((c - prev_close) / prev_close) * 100
            avg_volume = self.df['Volume'].iloc[:-1].mean()
            volume_ratio = v / avg_volume if avg_volume > 0 else 0

            alerts = []
            if abs(price_change_pct) >= 3:
                alerts.append(f"Price Alert: {price_change_pct:+.2f}%")
            if volume_ratio > 2.0:
                alerts.append(f"Volume Spike: {volume_ratio:.1f}x avg")

            if alerts:
                self.alert_label.setText(" | ".join(alerts))
                QTimer.singleShot(7000, lambda: self.alert_label.setText(""))

        self.plot_chart()

    def plot_chart(self):
        df = self.df.copy()
        df['EMA9'] = df['Close'].ewm(span=9).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        df = df.join(macd)

        add_plots = [
            mpf.make_addplot(df['RSI'], panel=1, ylabel='RSI'),
            mpf.make_addplot(df['MACD_12_26_9'], panel=2, ylabel='MACD'),
            mpf.make_addplot(df['MACDs_12_26_9'], panel=2),
        ]

        fig, _ = mpf.plot(
            df,
            type='candle',
            mav=(9, 50),
            volume=True,
            style='charles',
            addplot=add_plots,
            returnfig=True,
            panel_ratios=(2, 1, 1)
        )

        if self.canvas:
            self.layout.removeWidget(self.canvas)
            self.canvas.setParent(None)

        self.canvas = FigureCanvas(fig)
        self.layout.insertWidget(1, self.canvas)  # Insert after symbol_box
    def update_symbol(self, symbol):
        self.symbol_box.setCurrentText(symbol)
