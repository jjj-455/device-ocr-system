import sys
import os
from PIL import Image

# Import onnxruntime BEFORE PyQt5 (DLL conflict workaround)
import onnxruntime
from ocr_engine import recognize as ocr_recognize

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# ===================== OCR =====================
def extract_date_from_image(pil_img):
    try:
        exif = pil_img._getexif()
        if exif:
            for tag_id in (36867, 36868, 306):
                if tag_id in exif:
                    dt_str = exif[tag_id]
                    import re
                    match = re.match(r"(\d{4}):(\d{2}):(\d{2})\s+(\d{2}):(\d{2})", dt_str)
                    if match:
                        y, m, d, h, mi = match.groups()
                        return f"{y}年{m}月{d}日  {h}:{mi}"
    except Exception:
        pass
    return None

# ===================== GUI =====================
app = QApplication(sys.argv)
app.setFont(QFont("Microsoft YaHei", 10))

window = QWidget()
window.setWindowTitle("设备点检数字系统")
window.setStyleSheet("background-color: #1a1a2e;")
window.resize(1400, 780)
window.setMinimumSize(1100, 650)

main_layout = QHBoxLayout(window)
main_layout.setContentsMargins(15, 12, 15, 12)
main_layout.setSpacing(12)

# ============ Left: Parameter Panel ============
left_panel = QFrame()
left_panel.setStyleSheet("background-color: #16213e; border: 1px solid #0f3460; border-radius: 6px;")
left_layout = QVBoxLayout(left_panel)
left_layout.setContentsMargins(15, 8, 15, 8)
left_layout.setSpacing(6)

# -- Title --
title_text = QLabel("苏州苏试试验集团股份有限公司励磁冷却系统")
title_text.setStyleSheet("color: #00d4ff; font-size: 15px; font-weight: bold;")
title_text.setAlignment(Qt.AlignCenter)
left_layout.addWidget(title_text)

# -- Outer Loop --
group1 = QGroupBox("励磁冷却系统外循环水路参数")
group1.setStyleSheet("""
    QGroupBox {
        background-color: #16213e; border: 1px solid #0f3460; border-radius: 6px;
        margin-top: 14px; padding: 12px 12px 8px 12px; color: #00d4ff; font-size: 13px; font-weight: bold;
    }
    QGroupBox::title {
        subcontrol-origin: margin; subcontrol-position: top center;
        padding: 0 8px;
    }
""")
g1_layout = QVBoxLayout(group1)
g1_layout.setContentsMargins(10, 2, 10, 6)
g1_layout.setSpacing(6)

# Flow row
flow_row = QFrame()
flow_row.setStyleSheet("background-color: transparent;")
flow_row_layout = QHBoxLayout(flow_row)
flow_row_layout.setContentsMargins(5, 2, 5, 2)
flow_row_layout.setSpacing(10)

flow_lbl = QLabel("开式水塔输出流量")
flow_lbl.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; background: transparent;")
flow_lbl.setFixedWidth(120)
flow_row_layout.addWidget(flow_lbl)

flow_main = QLineEdit()
flow_main.setPlaceholderText("")
flow_main.setAlignment(Qt.AlignCenter)
flow_main.setMinimumWidth(80)
flow_main.setStyleSheet("""
    QLineEdit {
        background-color: #0f3460; color: #00ff88; font-size: 16px; font-weight: bold;
        border: 2px solid #00d4ff; border-radius: 4px; padding: 2px 4px;
    }
    QLineEdit:focus { border-color: #33ddff; }
""")
flow_main.setFixedHeight(36)
flow_row_layout.addWidget(flow_main, 1)

flow_unit = QLabel("L/Min")
flow_unit.setStyleSheet("color: #a0a0c0; font-size: 14px; font-weight: bold; background: transparent;")
flow_unit.setFixedWidth(50)
flow_row_layout.addWidget(flow_unit)
g1_layout.addWidget(flow_row)

# Temp row
temp_row = QFrame()
temp_row.setStyleSheet("background-color: transparent;")
temp_row_layout = QHBoxLayout(temp_row)
temp_row_layout.setContentsMargins(5, 2, 5, 2)
temp_row_layout.setSpacing(10)

temp_lbl = QLabel("开式水塔输出水温")
temp_lbl.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; background: transparent;")
temp_lbl.setFixedWidth(120)
temp_row_layout.addWidget(temp_lbl)

temp_main = QLineEdit()
temp_main.setPlaceholderText("")
temp_main.setAlignment(Qt.AlignCenter)
temp_main.setMinimumWidth(80)
temp_main.setStyleSheet("""
    QLineEdit {
        background-color: #0f3460; color: #00ff88; font-size: 16px; font-weight: bold;
        border: 2px solid #00d4ff; border-radius: 4px; padding: 2px 4px;
    }
    QLineEdit:focus { border-color: #33ddff; }
""")
temp_main.setFixedHeight(36)
temp_row_layout.addWidget(temp_main, 1)

temp_unit = QLabel("°C")
temp_unit.setStyleSheet("color: #a0a0c0; font-size: 14px; font-weight: bold; background: transparent;")
temp_unit.setFixedWidth(50)
temp_row_layout.addWidget(temp_unit)
g1_layout.addWidget(temp_row)

left_layout.addWidget(group1)

# -- Inner Loop --
group2 = QGroupBox("励磁冷却系统内循环水路参数")
group2.setStyleSheet("""
    QGroupBox {
        background-color: #16213e; border: 1px solid #0f3460; border-radius: 6px;
        margin-top: 14px; padding: 12px 12px 8px 12px; color: #00d4ff; font-size: 13px; font-weight: bold;
    }
    QGroupBox::title {
        subcontrol-origin: margin; subcontrol-position: top center;
        padding: 0 8px;
    }
""")
g2_layout = QHBoxLayout(group2)
g2_layout.setContentsMargins(8, 2, 8, 6)
g2_layout.setSpacing(10)

# Input circuit
sub_in = QGroupBox("输入回路")
sub_in.setStyleSheet("""
    QGroupBox {
        background-color: #0f2040; border: 1px solid #1a4a80; border-radius: 4px;
        margin-top: 12px; padding: 10px 10px 6px 10px; color: #88bbdd; font-size: 12px; font-weight: bold;
    }
    QGroupBox::title {
        subcontrol-origin: margin; subcontrol-position: top left;
        padding: 0 6px;
    }
""")
sub_in_layout = QVBoxLayout(sub_in)
sub_in_layout.setContentsMargins(6, 6, 6, 6)
sub_in_layout.setSpacing(4)

field_conductivity = QLineEdit()
field_temp_in = QLineEdit()
field_pressure = QLineEdit()

for name, unit, inp in [
    ("电导率", "us/cm", field_conductivity),
    ("温度",   "°C",    field_temp_in),
    ("压力",   "bar",   field_pressure),
]:
    row = QFrame()
    row.setStyleSheet("background-color: #0f3460; border-radius: 3px;")
    rl = QHBoxLayout(row)
    rl.setContentsMargins(8, 4, 8, 4)
    nl = QLabel(name)
    nl.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; background: transparent;")
    nl.setFixedWidth(55)
    rl.addWidget(nl)
    inp.setPlaceholderText("")
    inp.setAlignment(Qt.AlignCenter)
    inp.setMinimumWidth(60)
    inp.setStyleSheet("""
        QLineEdit {
            background-color: #0f3460; color: #00ff88; font-size: 16px; font-weight: bold;
            border: 2px solid #00d4ff; border-radius: 4px; padding: 2px 4px;
        }
        QLineEdit:focus { border-color: #33ddff; }
    """)
    rl.addWidget(inp, 1)
    ul = QLabel(unit)
    ul.setStyleSheet("color: #a0a0c0; font-size: 13px; background: transparent;")
    ul.setFixedWidth(48)
    rl.addWidget(ul)
    sub_in_layout.addWidget(row)

g2_layout.addWidget(sub_in)

# Output circuit
sub_out = QGroupBox("输出回路")
sub_out.setStyleSheet("""
    QGroupBox {
        background-color: #0f2040; border: 1px solid #1a4a80; border-radius: 4px;
        margin-top: 12px; padding: 10px 10px 6px 10px; color: #88bbdd; font-size: 12px; font-weight: bold;
    }
    QGroupBox::title {
        subcontrol-origin: margin; subcontrol-position: top left;
        padding: 0 6px;
    }
""")
sub_out_layout = QVBoxLayout(sub_out)
sub_out_layout.setContentsMargins(6, 6, 6, 6)
sub_out_layout.setSpacing(4)

field_flow_out = QLineEdit()
field_temp_out = QLineEdit()

for name, unit, inp in [
    ("流量", "L/Min", field_flow_out),
    ("温度", "°C",    field_temp_out),
]:
    row = QFrame()
    row.setStyleSheet("background-color: #0f3460; border-radius: 3px;")
    rl = QHBoxLayout(row)
    rl.setContentsMargins(8, 4, 8, 4)
    nl = QLabel(name)
    nl.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; background: transparent;")
    nl.setFixedWidth(55)
    rl.addWidget(nl)
    inp.setPlaceholderText("")
    inp.setAlignment(Qt.AlignCenter)
    inp.setMinimumWidth(60)
    inp.setStyleSheet("""
        QLineEdit {
            background-color: #0f3460; color: #00ff88; font-size: 16px; font-weight: bold;
            border: 2px solid #00d4ff; border-radius: 4px; padding: 2px 4px;
        }
        QLineEdit:focus { border-color: #33ddff; }
    """)
    rl.addWidget(inp, 1)
    ul = QLabel(unit)
    ul.setStyleSheet("color: #a0a0c0; font-size: 13px; background: transparent;")
    ul.setFixedWidth(48)
    rl.addWidget(ul)
    sub_out_layout.addWidget(row)

g2_layout.addWidget(sub_out)
g2_layout.addStretch()

left_layout.addWidget(group2, 1)
main_layout.addWidget(left_panel, 7)

# ============ Right: Controls + Image ============
right_panel = QFrame()
right_panel.setStyleSheet("background-color: #16213e; border: 1px solid #0f3460; border-radius: 6px;")
right_layout = QVBoxLayout(right_panel)
right_layout.setContentsMargins(12, 12, 12, 12)
right_layout.setSpacing(10)

btn_import = QPushButton("导入点检图片")
btn_import.setStyleSheet("""
    QPushButton {
        background-color: #0f3460; color: #00d4ff; font-size: 14px; font-weight: bold;
        border: 1px solid #00d4ff; border-radius: 4px; padding: 10px;
    }
    QPushButton:hover { background-color: #1a4a80; }
""")
right_layout.addWidget(btn_import)

btn_query = QPushButton("查询点检图片")
btn_query.setStyleSheet("""
    QPushButton {
        background-color: #0f3460; color: #00d4ff; font-size: 14px; font-weight: bold;
        border: 1px solid #00d4ff; border-radius: 4px; padding: 10px;
    }
    QPushButton:hover { background-color: #1a4a80; }
""")
right_layout.addWidget(btn_query)

btn_save = QPushButton("保存数据")
btn_save.setStyleSheet("""
    QPushButton {
        background-color: #00d4ff; color: #1a1a2e; font-size: 14px; font-weight: bold;
        border: none; border-radius: 4px; padding: 10px;
    }
    QPushButton:hover { background-color: #33ddff; }
""")
right_layout.addWidget(btn_save)

# Image display - auto-scaling label
class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()
        self._pix = None
    def set_image(self, path):
        self._pix = QPixmap(path)
        self.scale_pixmap()
    def clear_image(self):
        self._pix = None
        super().setPixmap(QPixmap())
    def scale_pixmap(self):
        if self._pix:
            scaled = self._pix.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            super().setPixmap(scaled)
    def resizeEvent(self, event):
        self.scale_pixmap()
        super().resizeEvent(event)

img_label = ImageLabel()
img_label.setAlignment(Qt.AlignCenter)
img_label.setText("图片显示区域\n导入点检图片后自动显示")
img_label.setStyleSheet("""
    background-color: #0a1628; border: 2px dashed #1a4a80; border-radius: 6px;
    color: #556677; font-size: 15px;
""")
img_label.setMinimumHeight(280)
right_layout.addWidget(img_label, 1)

# Date
date_label = QLabel("")
date_label.setAlignment(Qt.AlignRight)
date_label.setStyleSheet("color: #a0a0c0; font-size: 16px; font-weight: bold;")
date_label.setVisible(False)
right_layout.addStretch()
right_layout.addWidget(date_label)

main_layout.addWidget(right_panel, 3)

# ===================== Image Viewer =====================
current_img_path = None

class ImageViewer(QDialog):
    def __init__(self, pixmap, title=""):
        super().__init__()
        self.setWindowTitle(f"图片查看 - {title}")
        self.resize(1000, 700)
        self.pixmap = pixmap
        self.scale = 1.0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setStyleSheet("background-color: #0a1628; border: none;")
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setCursor(Qt.OpenHandCursor)
        self.update_image()
        self.scroll.setWidget(self.img_label)
        self.scroll.setWidgetResizable(False)
        layout.addWidget(self.scroll)
        info = QLabel("鼠标滚轮缩放  |  拖动查看")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #556677; font-size: 12px; padding: 4px; background-color: #16213e;")
        layout.addWidget(info)

    def update_image(self):
        size = self.pixmap.size() * self.scale
        scaled = self.pixmap.scaled(size.toSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.img_label.setPixmap(scaled)
        self.img_label.resize(scaled.size())

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0: self.scale *= 1.15
        else: self.scale /= 1.15
        self.scale = max(0.1, min(10.0, self.scale))
        self.update_image()


# ===================== Functions =====================
field_map = {
    "flow_main": flow_main,
    "temp_main": temp_main,
    "conductivity": field_conductivity,
    "temp_in": field_temp_in,
    "pressure": field_pressure,
    "flow_out": field_flow_out,
    "temp_out": field_temp_out,
}

field_labels = {
    "flow_main": "开式水塔输出流量",
    "temp_main": "开式水塔输出水温",
    "conductivity": "电导率",
    "temp_in": "温度(输入回路)",
    "pressure": "压力",
    "flow_out": "流量(输出回路)",
    "temp_out": "温度(输出回路)",
}

field_keys_order = ["flow_main", "temp_main", "conductivity", "temp_in",
                     "pressure", "flow_out", "temp_out"]
RECORDS_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "records.csv")

def set_buttons_enabled(enabled):
    """统一控制三个操作按钮的启用/禁用"""
    btn_import.setEnabled(enabled)
    btn_query.setEnabled(enabled)
    btn_save.setEnabled(enabled)


def clear_all_data():
    """清除所有参数框、图片、日期"""
    for inp in field_map.values():
        inp.clear()
    img_label.clear_image()
    img_label.setText("图片显示区域\n导入点检图片后自动显示")
    img_label.setStyleSheet("""
        background-color: #0a1628; border: 2px dashed #1a4a80; border-radius: 6px;
        color: #556677; font-size: 15px;
    """)
    date_label.clear()
    date_label.setVisible(False)

def show_warning_dialog(parent, title, text):
    """带亮色样式的警告弹窗"""
    dlg = QMessageBox(parent)
    dlg.setWindowTitle(title)
    dlg.setText(text)
    dlg.setIcon(QMessageBox.Warning)
    dlg.setStyleSheet("""
        QMessageBox {
            background-color: #1a1a2e; color: #e0e0e0;
        }
        QMessageBox QLabel {
            color: #e0e0e0; font-size: 13px;
        }
        QPushButton {
            background-color: #0f3460; color: #00d4ff;
            border: 1px solid #00d4ff; border-radius: 4px;
            padding: 6px 20px; font-size: 13px; font-weight: bold;
        }
        QPushButton:hover { background-color: #1a4a80; }
    """)
    dlg.exec_()

def get_field_values():
    """读取界面上所有参数值，返回 {key: value_str}"""
    vals = {}
    for key in field_keys_order:
        text = field_map[key].text().strip()
        vals[key] = text
    return vals

def save_current_record():
    """保存当前参数到 CSV（相同时间覆盖旧记录）"""
    try:
        set_buttons_enabled(False)
        vals = get_field_values()

        # 检查是否全部填写
        empty_fields = [field_labels[k] for k in field_keys_order if not vals[k]]
        if empty_fields:
            msg = "以下参数为空，请全部填写后再保存：\n" + "\n".join(f"  • {f}" for f in empty_fields)
            show_warning_dialog(window, "保存失败", msg)
            return

        # 获取日期和图片名
        dt = date_label.text().strip() if date_label.isVisible() else ""
        if not dt:
            show_warning_dialog(window, "保存失败", "缺少日期信息，请先导入图片")
            return

        img_name = os.path.basename(current_img_path) if current_img_path else ""

        header = ["日期时间", "图片", "输出流量", "输出水温", "电导率",
                  "输入温度", "压力", "输出流量2", "输出温度"]
        new_row = [dt, img_name,
                   vals["flow_main"], vals["temp_main"],
                   vals["conductivity"], vals["temp_in"],
                   vals["pressure"], vals["flow_out"], vals["temp_out"]]

        import csv
        # 检查是否已有相同时间的记录
        records = []
        duplicate_idx = -1
        if os.path.exists(RECORDS_CSV):
            with open(RECORDS_CSV, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                all_rows = list(reader)
            if len(all_rows) > 0:
                header_existing = all_rows[0]
                records = all_rows[1:]
                for i, row in enumerate(records):
                    if len(row) > 0 and row[0] == dt:
                        duplicate_idx = i
                        break
            else:
                header_existing = header
        else:
            header_existing = header

        if duplicate_idx >= 0:
            # 相同时间已存在 → 确认是否覆盖
            old_vals = records[duplicate_idx]
            old_summary = ", ".join([f"{h}={old_vals[i]}" if i < len(old_vals) else ""
                                     for i, h in enumerate(header) if i > 0])

            confirm = QMessageBox(window)
            confirm.setWindowTitle("确认覆盖")
            confirm.setText(f"已存在 {dt} 的记录，是否覆盖？")
            confirm.setInformativeText(f"旧数据：{old_summary}")
            confirm.setIcon(QMessageBox.Question)
            confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            confirm.setDefaultButton(QMessageBox.No)
            confirm.setStyleSheet("""
                QMessageBox { background-color: #1a1a2e; color: #e0e0e0; }
                QMessageBox QLabel { color: #e0e0e0; font-size: 13px; }
                QPushButton { background-color: #0f3460; color: #00d4ff;
                    border: 1px solid #00d4ff; border-radius: 4px;
                    padding: 6px 20px; font-size: 13px; font-weight: bold; }
                QPushButton:hover { background-color: #1a4a80; }
            """)
            result = confirm.exec_()
            if result != QMessageBox.Yes:
                return

            records[duplicate_idx] = new_row
        else:
            records.insert(0, new_row)

        # 写回 CSV
        with open(RECORDS_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(header_existing)
            writer.writerows(records)

        # 成功提示
        action = "覆盖" if duplicate_idx >= 0 else "新增"
        dlg = QMessageBox(window)
        dlg.setWindowTitle("保存成功")
        dlg.setText(f"数据已{action}保存\n{RECORDS_CSV}")
        dlg.setIcon(QMessageBox.Information)
        dlg.setStyleSheet("""
            QMessageBox { background-color: #1a1a2e; color: #e0e0e0; }
            QMessageBox QLabel { color: #e0e0e0; font-size: 13px; }
            QPushButton { background-color: #0f3460; color: #00d4ff;
                border: 1px solid #00d4ff; border-radius: 4px;
                padding: 6px 20px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background-color: #1a4a80; }
        """)
        dlg.exec_()
    finally:
        set_buttons_enabled(True)

def load_records():
    """从 CSV 读取所有记录，返回列表，每项为 dict"""
    if not os.path.exists(RECORDS_CSV):
        return []
    import csv
    records = []
    with open(RECORDS_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def show_query_dialog():
    """弹出查询历史记录窗口（按年/月筛选）"""
    set_buttons_enabled(False)
    all_records = load_records()
    if not all_records:
        show_warning_dialog(window, "查询", "暂无历史记录")
        return
    # 按日期时间降序（最新在最上）
    all_records.sort(key=lambda r: r.get("日期时间", ""), reverse=True)

    dlg = QDialog(window)
    dlg.setWindowTitle("查询历史记录")
    dlg.resize(900, 500)
    dlg.setStyleSheet("background-color: #1a1a2e; color: #e0e0e0;")

    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(15, 15, 15, 15)

    # ===== 筛选行 =====
    filter_layout = QHBoxLayout()

    # 收集所有年份/月份
    years = set()
    months = set()
    for rec in all_records:
        try:
            dt_str = rec.get("日期时间", "").replace("  ", " ")
            from datetime import datetime
            dt = datetime.strptime(dt_str, "%Y年%m月%d日 %H:%M")
            years.add(dt.year)
            months.add(dt.month)
        except:
            pass
    years = sorted(years, reverse=True)
    months = sorted(months)

    from datetime import datetime
    now = datetime.now()
    default_year = now.year
    default_month = now.month

    cb_year = QComboBox()
    cb_year.addItem("全部", 0)
    for y in years:
        cb_year.addItem(str(y), y)
    cb_year.setCurrentIndex(0 if default_year not in years else years.index(default_year) + 1)
    cb_year.setStyleSheet("""
        QComboBox { background-color: #0f3460; color: #ffffff;
            border: 1px solid #1a4a80; border-radius: 4px;
            padding: 6px 10px; font-size: 13px; min-width: 80px; }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView { background-color: #0f3460; color: #ffffff; }
    """)
    filter_layout.addWidget(QLabel("年份:"))
    filter_layout.addWidget(cb_year)

    cb_month = QComboBox()
    cb_month.addItem("全部", 0)
    for m in months:
        cb_month.addItem(f"{m}月", m)
    cb_month.setCurrentIndex(0)
    cb_month.setStyleSheet(cb_year.styleSheet())
    filter_layout.addWidget(QLabel("月份:"))
    filter_layout.addWidget(cb_month)

    btn_filter = QPushButton("查询")
    btn_filter.setStyleSheet("""
        QPushButton { background-color: #0f3460; color: #00d4ff;
            border: 1px solid #00d4ff; border-radius: 4px;
            padding: 6px 16px; font-size: 13px; font-weight: bold; }
        QPushButton:hover { background-color: #1a4a80; }
    """)
    filter_layout.addWidget(btn_filter)

    lbl_count = QLabel("")
    lbl_count.setStyleSheet("color: #8899aa; font-size: 13px; padding-left: 10px;")
    filter_layout.addWidget(lbl_count)
    filter_layout.addStretch()

    layout.addLayout(filter_layout)

    # ===== 表格 =====
    headers = ["日期时间", "图片", "输出流量", "输出水温", "电导率",
               "输入温度", "压力", "输出流量2", "输出温度"]
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setStyleSheet("""
        QTableWidget { background-color: #0f3460; color: #ffffff;
            font-size: 13px; border: none; gridline-color: #1a1a3e; }
        QHeaderView::section { background-color: #0a1628; color: #00d4ff;
            font-weight: bold; padding: 6px; border: 1px solid #1a1a3e; }
        QTableWidget::item { padding: 4px; }
        QTableWidget::item:selected { background-color: #1a4a80; }
    """)
    layout.addWidget(table)

    # ===== 按钮行 =====
    btn_layout = QHBoxLayout()

    btn_load = QPushButton("加载该次数据")
    btn_load.setStyleSheet("""
        QPushButton { background-color: #0f3460; color: #00d4ff;
            border: 1px solid #00d4ff; border-radius: 4px;
            padding: 8px 16px; font-size: 13px; font-weight: bold; }
        QPushButton:hover { background-color: #1a4a80; }
    """)
    btn_layout.addWidget(btn_load)

    btn_layout.addStretch()

    btn_close = QPushButton("关闭")
    btn_close.setStyleSheet("""
        QPushButton { background-color: #00d4ff; color: #1a1a2e;
            border: none; border-radius: 4px;
            padding: 8px 16px; font-size: 13px; font-weight: bold; }
        QPushButton:hover { background-color: #33ddff; }
    """)
    btn_layout.addWidget(btn_close)
    btn_close.clicked.connect(dlg.accept)

    layout.addLayout(btn_layout)

    # ===== 刷新表格 =====
    def refresh_table():
        year_val = cb_year.currentData()
        month_val = cb_month.currentData()

        filtered = []
        for rec in all_records:
            try:
                dt_str = rec.get("日期时间", "").replace("  ", " ")
                dt = datetime.strptime(dt_str, "%Y年%m月%d日 %H:%M")
                if year_val and dt.year != year_val:
                    continue
                if month_val and dt.month != month_val:
                    continue
            except:
                pass
            filtered.append(rec)

        table.setRowCount(len(filtered))
        for r, rec in enumerate(filtered):
            for c, h in enumerate(headers):
                item = QTableWidgetItem(rec.get(h, ""))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(r, c, item)
        table.resizeColumnsToContents()

        lbl_count.setText(f"当前显示 {len(filtered)} 条记录")

        # 返回 filtered 供按钮使用
        return filtered

    filtered_records = refresh_table()
    btn_filter.clicked.connect(lambda: refresh_table())

    # ===== 加载该次数据 =====
    def on_load_data():
        row = table.currentRow()
        if row < 0:
            show_warning_dialog(dlg, "提示", "请先选择一条记录")
            return
        # 重新获取当前显示的数据
        year_val = cb_year.currentData()
        month_val = cb_month.currentData()
        cur = []
        for rec in all_records:
            try:
                dt_str = rec.get("日期时间", "").replace("  ", " ")
                dt = datetime.strptime(dt_str, "%Y年%m月%d日 %H:%M")
                if year_val and dt.year != year_val:
                    continue
                if month_val and dt.month != month_val:
                    continue
            except:
                pass
            cur.append(rec)
        if row >= len(cur):
            return
        rec = cur[row]

        key_to_col = {"flow_main": "输出流量", "temp_main": "输出水温",
                      "conductivity": "电导率", "temp_in": "输入温度",
                      "pressure": "压力", "flow_out": "输出流量2",
                      "temp_out": "输出温度"}
        for fid, col in key_to_col.items():
            val = rec.get(col, "")
            field_map[fid].setText(val)

        img_name = rec.get("图片", "")
        if img_name:
            global current_img_path
            img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), img_name)
            if os.path.exists(img_path):
                current_img_path = img_path
                img_label.set_image(img_path)
                img_label.setStyleSheet("background-color: #0a1628; border: 1px solid #1a4a80; border-radius: 6px;")
                img_label.setText("")

        dt = rec.get("日期时间", "")
        if dt:
            date_label.setText(dt)
            date_label.setVisible(True)

        dlg.accept()

    btn_load.clicked.connect(on_load_data)

    dlg.exec_()
    set_buttons_enabled(True)


def on_import():
    global current_img_path
    file_path, _ = QFileDialog.getOpenFileName(
        window, "选择点检图片", "",
        "图片文件 (*.jpg *.jpeg *.png *.bmp);;所有文件 (*)")
    if not file_path:
        return

    current_img_path = file_path

    # 清除旧数据
    clear_all_data()

    # 立即显示图片
    img_label.set_image(file_path)
    img_label.setStyleSheet("background-color: #0a1628; border: 1px solid #1a4a80; border-radius: 6px;")
    img_label.setText("")
    QApplication.processEvents()

    set_buttons_enabled(False)
    btn_import.setText("识别中...")
    QApplication.processEvents()

    try:
        # OCR 识别
        pil_img = Image.open(file_path)
        values, ok, msg = ocr_recognize(file_path)

        # 填入数字
        field_keys = ["flow_main", "temp_main", "conductivity", "temp_in",
                       "pressure", "flow_out", "temp_out"]
        for fid, val in zip(field_keys, values):
            inp = field_map[fid]
            if val is not None:
                if val == int(val):
                    inp.setText(str(int(val)))
                else:
                    inp.setText(f"{val:.1f}")

        # 校验不通过时弹窗提示
        if not ok:
            nums_str = ", ".join([f"{v:.1f}" if v is not None else "?" for v in values])
            show_warning_dialog(window, "识别提醒",
                f"{msg}\n\n已识别的数字：{nums_str}\n\n请手动核对修正")

        # 显示日期
        dt = extract_date_from_image(pil_img)
        if dt:
            date_label.setText(dt)
        else:
            mtime = os.path.getmtime(file_path)
            from datetime import datetime
            dt_obj = datetime.fromtimestamp(mtime)
            date_label.setText(f"{dt_obj.year}年{dt_obj.month:02d}月{dt_obj.day:02d}日  {dt_obj.hour:02d}:{dt_obj.minute:02d}")
        date_label.setVisible(True)

    except Exception as e:
        show_warning_dialog(window, "识别错误", f"图片识别失败：{str(e)}")
    finally:
        set_buttons_enabled(True)
        btn_import.setText("导入点检图片")

btn_import.clicked.connect(on_import)
btn_save.clicked.connect(save_current_record)
btn_query.clicked.connect(show_query_dialog)

window.show()
sys.exit(app.exec_())
