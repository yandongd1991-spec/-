import sys
import os
import requests
import webbrowser
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QLabel, QFrame, QMessageBox, QComboBox, QListView)
from PyQt6.QtCore import QTimer, Qt, QPoint
from PyQt6.QtGui import QGuiApplication, QIcon

# ==================== 1. 強制更新 ====================
CURRENT_VERSION = "1.1"
VERSION_URL = "https://raw.githubusercontent.com/yandongd1991-spec/-/main/version.txt"
DOWNLOAD_URL = "https://pan.baidu.com/s/1O9UUuRmoB0_Nfi7mHuvxUQ"

def check_for_updates():
    try:
        response = requests.get(VERSION_URL, timeout=5)
        if response.text.strip() > CURRENT_VERSION:
            msg = QMessageBox()
            msg.setWindowTitle("版本過舊")
            msg.setText("請更新至最新版本以繼續使用")
            msg.exec()
            webbrowser.open(DOWNLOAD_URL)
            sys.exit()
    except: pass

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'): return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ==================== 2. 資料集 ====================
BOSS_DATA = {
    "維多利亞": ["红宝王", "僵尸猴王", "蘑菇王", "巨居蟹", "沼泽巨鳄", "巴洛古", "樹妖王", "僵尸蘑菇王"],
    "天空之城": ["艾利杰"],
    "冰原雪域": ["雪毛怪人"],
    "玩具城": ["提摩", "九尾妖狐", "葛雷金刚"],
    "武陵桃園": ["肯德熊", "喵怪仙人"],
    "納米爾森林": ["莱西王", "格瑞芬多", "喷火龙"],
    "時間神殿": ["多多", "莱伊卡"],
    "水下世界": ["海怒斯", "塞尔提"]
}
CHANNELS = [f"CH {i}" for i in range(1, 21)]

# ==================== 3. 任務單元 (穩定版) ====================
class TimerItem(QFrame):
    def __init__(self, parent_app, area="維多利亞", boss=None, ch="CH 1"):
        super().__init__()
        self.parent_app = parent_app
        self.setFixedSize(370, 30) 
        self.setStyleSheet("""
            QFrame { background-color: #2d2d2d; border: 1px solid #444; border-radius: 2px; }
            QComboBox { background: #1e1e1e; color: white; border: 1px solid #555; font-size: 11px; padding-left: 5px; }
            QComboBox::drop-down { width: 0px; border: 0px; }
            QComboBox QAbstractItemView { background-color: #1e1e1e; color: white; selection-background-color: #444; border: 1px solid #555; outline: none; }
            QLineEdit { background: #1e1e1e; color: #00ff00; border: 1px solid #555; font-weight: bold; font-size: 11px; }
            QPushButton { background-color: #444; color: white; border-radius: 2px; font-weight: bold; font-size: 11px; }
            QPushButton#plus_btn { color: #ffcc00; }
            QPushButton#minus_btn { color: #44aaff; }
            QPushButton#close_btn { color: #ff4444; background-color: #383838; }
            QLabel#unit_label { color: #777; font-size: 10px; border: none; background: transparent; }
        """)
        
        self.seconds = 1800 
        self.is_running = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(4)

        # 下拉選單共通設定 (鎖死寬度 + 去除滾動條)
        def setup_combo(combo, w):
            combo.setFixedSize(w, 22)
            view = QListView()
            view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            combo.setView(view)

        self.area_combo = QComboBox(); setup_combo(self.area_combo, 60)
        self.area_combo.addItems(BOSS_DATA.keys())
        
        self.boss_combo = QComboBox(); setup_combo(self.boss_combo, 80)
        
        self.ch_combo = QComboBox(); setup_combo(self.ch_combo, 55)
        self.ch_combo.addItems(CHANNELS)

        # --- 記憶賦值 ---
        self.area_combo.setCurrentText(area)
        self.update_boss_list(area)
        if boss: self.boss_combo.setCurrentText(boss)
        self.ch_combo.setCurrentText(ch)

        self.area_combo.currentTextChanged.connect(self.update_boss_list)
        
        self.time_display = QLineEdit("30:00")
        self.time_display.setFixedSize(40, 22); self.time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.unit_label = QLabel("分"); self.unit_label.setObjectName("unit_label")
        self.unit_label.setFixedSize(55, 22); self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_sz = 20
        self.plus_btn = QPushButton("+"); self.plus_btn.setObjectName("plus_btn"); self.plus_btn.setFixedSize(btn_sz, btn_sz)
        self.plus_btn.clicked.connect(lambda: self.adjust_time(600))

        self.minus_btn = QPushButton("-"); self.minus_btn.setObjectName("minus_btn"); self.minus_btn.setFixedSize(btn_sz, btn_sz)
        self.minus_btn.clicked.connect(lambda: self.adjust_time(-600))
        
        self.start_btn = QPushButton("GO"); self.start_btn.setFixedSize(28, btn_sz)
        self.start_btn.clicked.connect(self.toggle_timer)

        self.close_btn = QPushButton("✕"); self.close_btn.setObjectName("close_btn"); self.close_btn.setFixedSize(btn_sz, btn_sz)
        self.close_btn.clicked.connect(self.remove_self)

        for w in [self.area_combo, self.boss_combo, self.ch_combo, self.time_display, 
                  self.unit_label, self.plus_btn, self.minus_btn, self.start_btn, self.close_btn]:
            layout.addWidget(w)

        self.timer = QTimer(); self.timer.timeout.connect(self.update_time)

    def update_boss_list(self, area_name):
        self.boss_combo.clear()
        if area_name in BOSS_DATA: self.boss_combo.addItems(BOSS_DATA[area_name])

    def adjust_time(self, delta):
        self.seconds = max(0, self.seconds + delta); self.update_display()

    def toggle_timer(self):
        if not self.is_running:
            self.timer.start(1000); self.start_btn.setText("||")
            self.start_btn.setStyleSheet("background-color: #2e7d32; color: white;")
            self.unit_label.setText("九尾哥哥"); self.unit_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        else:
            self.timer.stop(); self.start_btn.setText("GO")
            self.start_btn.setStyleSheet("background-color: #444; color: white;")
            self.unit_label.setText("分"); self.unit_label.setStyleSheet("color: #777; font-weight: normal;")
        self.is_running = not self.is_running

    def update_display(self):
        m, s = divmod(self.seconds, 60); self.time_display.setText(f"{m:02d}:{s:02d}")

    def update_time(self):
        if self.seconds > 0: self.seconds -= 1; self.update_display()
        else: self.timer.stop(); QMessageBox.information(self, "提醒", "刷新！")

    def remove_self(self):
        self.timer.stop(); self.parent_app.remove_item(self)

# ==================== 4. 主視窗 (記憶邏輯) ====================
class BossTimerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.items = []
        self.setWindowTitle("九尾計時器")
        icon_path = get_resource_path("icon.ico")
        if os.path.exists(icon_path): self.setWindowIcon(QIcon(icon_path))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(0,0,0,0); self.main_layout.setSpacing(1) 
        
        # 初始化第一個
        self.add_task()
        
        self.add_btn = QPushButton("+ 新增任務")
        self.add_btn.setFixedSize(370, 28)
        self.add_btn.clicked.connect(self.click_add_memory)
        self.add_btn.setStyleSheet("background-color: #444; color: white; border-radius: 2px; font-weight: bold;")
        
        self.main_layout.addWidget(self.add_btn)
        self.center_on_screen(); self.old_pos = None

    def add_task(self, area="維多利亞", boss=None, ch="CH 1"):
        item = TimerItem(self, area, boss, ch)
        self.items.append(item)
        self.main_layout.insertWidget(self.main_layout.count() - 1, item)
        self.adjustSize()

    def click_add_memory(self):
        # 記憶邏輯：抓取最後一個 Item 的當前選項
        if self.items:
            last = self.items[-1]
            self.add_task(
                last.area_combo.currentText(),
                last.boss_combo.currentText(),
                last.ch_combo.currentText()
            )
        else:
            self.add_task()

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item); item.setParent(None); item.deleteLater()
            if not self.items: QApplication.quit()
            else: QTimer.singleShot(30, lambda: self.adjustSize())

    def center_on_screen(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - 370) // 2, (screen.height() - self.height()) // 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y()); self.old_pos = event.globalPosition().toPoint()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    check_for_updates()
    window = BossTimerApp()
    window.show()
    sys.exit(app.exec())
