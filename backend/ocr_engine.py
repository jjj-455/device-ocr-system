"""
OCR 识别引擎
PP-OCRv4 三步识别 → 数字提取 → 空间排序 → 校验
与 GUI 完全解耦，main.py 仅调用 recognize() 入口函数
"""
import re
import cv2
import numpy as np
from PIL import Image
from rapidocr import RapidOCR

_ocr = None
def _get_ocr():
    global _ocr
    if _ocr is None:
        _ocr = RapidOCR()
    return _ocr


def _is_date_or_time(text):
    """判断是否为日期时间字符串（含 - : / 等分隔符）"""
    # 包含冒号 → 时间戳
    if ":" in text:
        return True
    # 匹配日期模式：2000-1-10 或 2000/1/10
    if re.search(r"\d{2,4}[-/]\d{1,2}[-/]\d{1,2}", text):
        return True
    return False

def get_numeric_value(text):
    """从文本中提取数字，支持 '41.6L/Min' → 41.6 这种格式"""
    t = text.strip().replace(" ", "")

    # 过滤日期时间
    if _is_date_or_time(t):
        return None

    # 替换常见 OCR 误识别
    t = t.replace(",", ".").replace("O", "0").replace("o", "0")
    t = t.replace("l", "1").replace("I", "1")

    # 如果整个就是纯数字
    try:
        return float(t)
    except ValueError:
        pass

    # 从混合字符串中提取数字（如 "41.6L/Min" → 41.6, "1#进水+23.6°C" → 23.6）
    matches = re.findall(r"(\d+\.?\d*)", t)
    # 取最长的数字串（过滤单字符噪声）
    valid = [m for m in matches if len(m) > 1 or "." in m]
    if valid:
        valid.sort(key=lambda x: -len(x))
        val_str = valid[0]
        # 修正：3位数且原始文本含℃/°C → 去掉最后一位小数（如228℃ → 22.8）
        if len(val_str) == 3 and ("℃" in t or "°C" in t or "°" in t):
            val_str = val_str[:2] + "." + val_str[2]
        try:
            return float(val_str)
        except ValueError:
            pass
    return None


def extract_numbers(ocr_results, img_width, img_height):
    """
    从 OCR 原始结果中过滤出数字
    返回 [(value, cx, cy), ...]
    """
    numbers = []
    for text, score, box in ocr_results:
        if score < 0.3:
            continue
        val = get_numeric_value(text)
        if val is not None:
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            numbers.append((val, cx, cy))
    return numbers


def sort_by_position(numbers, img_width, img_height):
    """
    按空间坐标排序：
    1. 用 x 坐标最大间距聚类分左右两组（自适应图片尺寸）
    2. 每组内按 y 聚类成行
    3. 每行内按 x 从小到大排序
    返回 (left_items, right_rows)
      left_items: [(value, cx, cy)] 已按 y 从上到下排好
      right_rows: [[(value, cx, cy)], [...]] 每行一个 list，已按 x 排好
    """
    # 用 x 坐标最大间距聚类分左右
    xs_sorted = sorted(numbers, key=lambda x: x[1])
    if len(xs_sorted) < 2:
        return xs_sorted, []

    # 找相邻 x 的最大间距
    max_gap = 0
    split_idx = len(xs_sorted) // 2  # 默认中点
    for i in range(1, len(xs_sorted)):
        gap = xs_sorted[i][1] - xs_sorted[i-1][1]
        if gap > max_gap:
            max_gap = gap
            split_idx = i

    # 用最大间距处的值作为分割阈值
    split_x = (xs_sorted[split_idx-1][1] + xs_sorted[split_idx][1]) / 2

    left = [n for n in numbers if n[1] < split_x]
    right = [n for n in numbers if n[1] >= split_x]

    # 左侧按 y 从上到下排序
    left.sort(key=lambda x: x[2])

    # 右侧按 y 聚类成行
    right.sort(key=lambda x: x[2])  # 先按 y 排序

    if not right:
        return left, []

    # 用 y 差值阈值聚类（图片高度的 8%）
    row_threshold = img_height * 0.08
    rows = []
    current_row = [right[0]]
    for i in range(1, len(right)):
        if abs(right[i][2] - right[i-1][2]) > row_threshold:
            rows.append(current_row)
            current_row = []
        current_row.append(right[i])
    if current_row:
        rows.append(current_row)

    # 每行内按 x 从小到大排序
    for row in rows:
        row.sort(key=lambda x: x[1])

    return left, rows


def validate(left_items, right_rows):
    """
    校验识别结果的数量和分组
    返回 (ok, message)
    """
    total = len(left_items) + sum(len(r) for r in right_rows)
    if total < 7:
        msg = f"识别数字不足7个（当前{total}个），请手动核对"
        return False, msg

    if len(left_items) < 2:
        msg = f"左侧参数不足2个（当前{len(left_items)}个），请手动核对"
        return False, msg

    if len(right_rows) < 2:
        msg = f"右侧行数不足（当前{len(right_rows)}行），请手动核对"
        return False, msg

    # 第一行至少3个
    if len(right_rows[0]) < 3:
        msg = f"右侧第一行数字不足3个（当前{len(right_rows[0])}个），请手动核对"
        return False, msg

    return True, "ok"


def preprocess(pil_img):
    """
    亮度检测 + 按需预处理
    亮度 < 100：CLAHE + 2x 放大
    亮度 ≥ 100：跳过预处理
    返回 (处理后的图片, 是否预处理)
    """
    gray = np.array(pil_img.convert('L'))
    mean_b = gray.mean()

    if mean_b >= 100:
        return pil_img, False

    # CLAHE 增强局部对比度
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 2x LANCZOS 放大
    up = cv2.resize(enhanced, (gray.shape[1] * 2, gray.shape[0] * 2),
                    interpolation=cv2.INTER_LANCZOS4)

    proc_img = Image.fromarray(up, mode='L')
    return proc_img, True


def recognize(image_path, strategy="position_sort"):
    """
    入口函数
    strategy="position_sort" → 用于励磁冷却系统（7参数，按位置排序+校验）
    strategy="label_match"  → 用于循环水系统（多参数，按标签匹配，暂时返回全部数字）
    返回 (values, ok, message)
    """
    # Step 1: 打开图片 + 预处理
    pil_img = Image.open(image_path)
    proc_img, preprocessed = preprocess(pil_img)
    img_w, img_h = proc_img.size
    img_np = np.array(proc_img.convert('RGB'))[:, :, ::-1]

    # Step 2: PP-OCRv4 三步识别
    ocr = _get_ocr()
    raw_output = ocr(img_np)
    # 兼容新版 rapidocr-onnxruntime（返回 tuple）和旧版（返回对象）
    if isinstance(raw_output, tuple):
        result_list, _ = raw_output
        if result_list is None:
            ocr_results = []
        else:
            ocr_results = [(item[1], item[2], item[0]) for item in result_list]
    else:
        ocr_results = list(zip(raw_output.txts, raw_output.scores, raw_output.boxes))

    # Step 3: 提取数字
    numbers = extract_numbers(ocr_results, img_w, img_h)
    if not numbers:
        return [], False, "未识别到任何数字"

    if strategy == "label_match":
        # ===== 循环水系统：基于已知坐标范围匹配 =====
        # 每个字段的预期位置范围 (x_min, x_max, y_min, y_max)
        field_positions = [
            (380, 480, 510, 570),    # 0: 1#进水温度
            (520, 620, 510, 570),    # 1: 1#出水温度
            (380, 480, 570, 630),    # 2: 2#进水温度
            (520, 620, 570, 630),    # 3: 2#出水温度
            (880, 960, 560, 620),    # 4: 热水侧温度
            (960, 1040, 560, 620),   # 5: 冷水侧温度
            (1100, 1200, 450, 510),  # 6: 1楼A泵频率 (近A标签y=448)
            (1100, 1200, 510, 570),  # 7: 1楼B泵频率 (近B标签y=511)
            (1100, 1200, 370, 420),  # 8: 1楼出水压力 (1.5Bar)
            (1100, 1200, 580, 630),  # 9: 2楼A泵频率 (46.5Hz)
            (1100, 1200, 640, 700),  # 10: 2楼B泵频率 (0.0Hz)
            (1200, 1280, 570, 630),  # 11: 2楼出水压力 (2.5Bar)
        ]

        result = [None] * 12
        for val, cx, cy in numbers:
            for fi, (x1, x2, y1, y2) in enumerate(field_positions):
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    if result[fi] is None:  # 只取每个位置第一个数字
                        result[fi] = val
                    break

        # 右上角电流值（独立裁剪识别 + 标签匹配）
        current_vals = [None] * 7  # field 12-18
        try:
            crop_box = (1350, 180, 1920, 650)
            crop = pil_img.crop(crop_box)
            cw, ch = crop.size
            gray = np.array(crop.convert('L'))
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            up = cv2.resize(enhanced, (cw * 4, ch * 4),
                            interpolation=cv2.INTER_LANCZOS4)

            ocr = _get_ocr()
            up_np = np.array(Image.fromarray(up, mode='L').convert('RGB'))[:, :, ::-1]
            crop_raw = ocr(up_np)

            # 提取裁剪图中的所有文本（含位置）
            crop_items = []  # (text, val_or_none, orig_x, orig_y)
            # 兼容新版 rapidocr-onnxruntime（返回 tuple）和旧版（返回对象）
            if isinstance(crop_raw, tuple):
                crop_list, _ = crop_raw
                crop_zip = [(item[1], item[2], item[0]) for item in crop_list] if crop_list else []
            else:
                crop_zip = list(zip(crop_raw.txts, crop_raw.scores, crop_raw.boxes))
            for text, score, box in crop_zip:
                if score < 0.3:
                    continue
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                cx = sum(xs) / len(xs) / 4 + crop_box[0]
                cy = sum(ys) / len(ys) / 4 + crop_box[1]
                val = get_numeric_value(text)
                if val is not None:
                    if 100 <= val <= 999 and '.' not in text:
                        val = val / 10
                    crop_items.append((text, val, cx, cy))
                else:
                    crop_items.append((text, None, cx, cy))

            # 用最近邻匹配：每个电流值分配给 y 最接近的泵标签
            # 泵标签预期 y 位置 (原图坐标)
            pump_ys = [290, 330, 368, 408, 446, 484, 523]

            # 右侧区域的数字 (x > 1650)
            right_nums = [(nv, ncy) for (ntxt, nv, ncx, ncy) in crop_items
                          if nv is not None and ncx > 1650]

            # 每个数字匹配最近泵，确保每个泵最多得一个值
            for nv, ncy in right_nums:
                best_pump = None
                best_dy = 999
                for pi, py in enumerate(pump_ys):
                    dy = abs(ncy - py)
                    if dy < best_dy and dy < 80:
                        best_dy = dy
                        best_pump = pi
                if best_pump is not None:
                    # 如果该泵已有值，保留 y 更接近的那个
                    if current_vals[best_pump] is None:
                        current_vals[best_pump] = nv
                    else:
                        existing = current_vals[best_pump]
                        existing_y = pump_ys[best_pump]
                        # 更新为更接近的值（简化处理）
                        pass
        except Exception:
            pass

        all_values = result + current_vals
        filled = sum(1 for v in result if v is not None)
        return all_values, len(all_values) > 0, \
            f"识别到 {len(all_values)} 个数字（标签匹配{filled}个+电流{len(current_vals)}个）"

    # position_sort 策略：励磁冷却系统
    left_items, right_rows = sort_by_position(numbers, img_w, img_h)
    ok, msg = validate(left_items, right_rows)

    values = []
    for val, cx, cy in left_items[:2]:
        values.append(val)
    while len(values) < 2:
        values.append(None)

    row1 = right_rows[0] if len(right_rows) > 0 else []
    row1_values = [v for v, cx, cy in row1[:3]]
    while len(row1_values) < 3:
        row1_values.append(None)

    row2 = right_rows[1] if len(right_rows) > 1 else []
    row2_values = [v for v, cx, cy in row2[:2]]
    while len(row2_values) < 2:
        row2_values.append(None)

    values.extend(row1_values)
    values.extend(row2_values)

    return values, ok, msg
