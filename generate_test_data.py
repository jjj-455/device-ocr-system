"""生成30天测试数据 Excel，用于导入验证趋势图功能"""
import random
from datetime import datetime, timedelta

try:
    from openpyxl import Workbook
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl", "-q"])
    from openpyxl import Workbook

random.seed(42)

PARAMS = [
    ("开式水塔输出流量(L/Min)", 110, 150),
    ("开式水塔输出水温(°C)", 18, 28),
    ("电导率(us/cm)", 15, 35),
    ("温度(输入回路)(°C)", 30, 48),
    ("压力(bar)", 2.5, 5.0),
    ("流量(输出回路)(L/Min)", 30, 55),
    ("温度(输出回路)(°C)", 35, 55),
]

wb = Workbook()
ws = wb.active
ws.title = "冷却监测数据"

# Header row
headers = ["序号", "日期时间"] + [p[0] for p in PARAMS] + ["照片"]
ws.append(headers)

# Generate 30 days, 1-2 records per day
base = datetime(2026, 5, 8)  # Start from May 8
row_num = 1

for day in range(30):
    records_today = 1 if day % 3 != 0 else 2  # Every 3rd day has 2 records
    for r in range(records_today):
        row_num += 1
        hour = 8 + random.randint(0, 9)  # 8:00 - 17:00
        minute = random.choice([0, 15, 30, 45])
        dt = base + timedelta(days=day, hours=hour, minutes=minute)
        date_str = dt.strftime("%Y-%m-%d %H:%M")

        # Generate values with slight trending + noise
        trend = (day / 30.0) * 5  # slight upward trend over 30 days
        vals = []
        for i, (_, lo, hi) in enumerate(PARAMS):
            # Each param has its own pattern
            noise = random.uniform(-3, 3)
            v = (lo + hi) / 2 + trend * (0.5 if i % 2 == 0 else -0.3) + noise
            v = round(max(lo - 2, min(hi + 2, v)), 1)
            vals.append(v)

        row = [row_num - 1, date_str] + vals + ["无"]
        ws.append(row)

# Adjust column widths
for col in ws.columns:
    max_len = max(len(str(c.value or "")) for c in col)
    ws.column_dimensions[col[0].column_letter].width = max_len + 2

output_path = "E:/claude/web-app/30天测试数据.xlsx"
wb.save(output_path)
print(f"已生成 {row_num - 1} 条记录 → {output_path}")
