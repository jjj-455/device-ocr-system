"""OCR recognition engine for equipment inspection system.
Uses RapidOCR (PP-OCRv4) with spatial number extraction.

Returns: (values_list, ok, msg)
  values_list: list of 7 floats or None
  ok: True if all 7 values found
  msg: status message
"""

import re
from rapidocr_onnxruntime import RapidOCR

# Global engine instance (lazy init)
_engine = None

FIELD_ORDER = [
    "flow_main", "temp_main",           # left side, top to bottom
    "conductivity", "temp_in", "pressure",  # right row 1, left to right
    "flow_out", "temp_out",             # right row 2, left to right
]

# Image width threshold: left half vs right half
LEFT_RATIO = 0.45  # left group when x < width * LEFT_RATIO
RIGHT_RATIO = 0.55  # right group when x > width * RIGHT_RATIO

# Y clustering threshold (pixels) - items within this distance are same row
Y_THRESHOLD = 30


def _get_engine():
    global _engine
    if _engine is None:
        _engine = RapidOCR()
    return _engine


def extract_numbers(results):
    """Filter OCR results: keep only pure numbers (with decimal point)."""
    numbers = []
    img_width = 0
    for item in results:
        box, text, confidence = item
        # text is str or None
        if text is None:
            continue
        text = text.strip()
        # Match pure number (int or decimal), possibly negative
        if re.match(r'^-?\d+(\.\d+)?$', text):
            # box: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            # Find bounding box center
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            # Track max x for image width
            img_width = max(img_width, max(xs))
            try:
                val = float(text)
                numbers.append((cx, cy, val))
            except ValueError:
                pass

    return numbers, img_width


def sort_by_position(numbers, img_width):
    """Split into left/right groups, cluster by row, sort left-to-right."""
    if not numbers or img_width == 0:
        return [], []

    left = []
    right = []
    for cx, cy, val in numbers:
        ratio = cx / img_width
        if ratio < LEFT_RATIO:
            left.append((cx, cy, val))
        elif ratio > RIGHT_RATIO:
            right.append((cx, cy, val))

    def group_and_sort(group):
        if not group:
            return []
        # Sort by y first
        group.sort(key=lambda x: x[1])
        # Cluster into rows
        rows = [[group[0]]]
        for item in group[1:]:
            if abs(item[1] - rows[-1][-1][1]) < Y_THRESHOLD:
                rows[-1].append(item)
            else:
                rows.append([item])
        # Sort each row by x
        for row in rows:
            row.sort(key=lambda x: x[0])
        # Flatten rows (top to bottom)
        return [val for row in rows for _, _, val in row]

    left_sorted = group_and_sort(left)
    right_sorted = group_and_sort(right)

    return left_sorted, right_sorted


def validate(left_vals, right_vals):
    """Check expected count: left=2, right=5 (row1=3, row2=2)."""
    if len(left_vals) == 2 and len(right_vals) == 5:
        return True, "识别成功"
    if len(left_vals) != 2 and len(right_vals) != 5:
        msg = f"校验不通过：左侧识别到 {len(left_vals)} 个数字（期望2个），右侧识别到 {len(right_vals)} 个数字（期望5个）"
    elif len(left_vals) != 2:
        msg = f"校验不通过：左侧识别到 {len(left_vals)} 个数字（期望2个）"
    else:
        msg = f"校验不通过：右侧识别到 {len(right_vals)} 个数字（期望5个）"
    return False, msg


def recognize(file_path):
    """Run OCR on image, extract 7 parameters by spatial layout.

    Returns:
        (values, ok, msg)
        - values: list of 7 floats or None
        - ok: True/False
        - msg: description string
    """
    engine = _get_engine()
    result, elapse = engine(file_path)

    if result is None:
        return [None] * 7, False, "OCR识别失败：未检测到任何文字"

    # Extract pure numbers with positions
    numbers, img_width = extract_numbers(result)

    if not numbers:
        return [None] * 7, False, "OCR识别失败：未检测到数字"

    # Sort by spatial position
    left_vals, right_vals = sort_by_position(numbers, img_width)

    # Validate
    ok, msg = validate(left_vals, right_vals)

    # Assemble final 7-value list
    values = []
    # Left: 2 values
    for i in range(2):
        if i < len(left_vals):
            values.append(left_vals[i])
        else:
            values.append(None)
    # Right: 5 values (row1: 3, row2: 2)
    for i in range(5):
        if i < len(right_vals):
            values.append(right_vals[i])
        else:
            values.append(None)

    return values, ok, msg
