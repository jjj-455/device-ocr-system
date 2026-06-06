"""
设备点检数字系统 — OCR API 服务
FastAPI + RapidOCR (PP-OCRv4) + SQLite 记录存储
"""
import os
import sys
import json
import tempfile
import traceback
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr_engine import recognize as ocr_recognize
from templates import templates

app = FastAPI(title="设备点检数字系统 OCR API", version="1.1.0")

# ---- SQLite 数据库 ----
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "records.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def serialize_record(row):
    """将数据库行转换为 dict（data 字段是 JSON 字符串）"""
    rec = json.loads(row[1])
    rec["_serverId"] = row[0]
    return rec


def read_all_records():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, data FROM records ORDER BY id").fetchall()
    conn.close()
    return [serialize_record(r) for r in rows]


@app.on_event("startup")
async def startup():
    init_db()

# CORS — 允许 Vercel 前端或其他来源调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """返回前端页面，找不到才返回 JSON 健康检查"""
    frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
    if os.path.exists(frontend_path):
        from fastapi.responses import FileResponse
        return FileResponse(frontend_path)
    return {
        "status": "ok",
        "message": "设备点检数字系统 OCR API 运行中",
        "devices": list(templates.keys()),
    }


@app.get("/api/devices")
def list_devices():
    """返回支持的设备类型和字段定义"""
    return {
        device: {
            "name": info["name"],
            "fields": [
                {"key": f[0], "label": f[1], "unit": f[2]}
                for f in info["fields"]
            ],
            "strategy": info["ocr_strategy"],
        }
        for device, info in templates.items()
    }


@app.post("/api/ocr")
async def handle_ocr(
    image: UploadFile = File(...),
    device_type: str = Form("chiller"),
):
    """
    上传设备仪表盘图片，返回 OCR 识别结果

    - image: 图片文件 (jpg/png/bmp)
    - device_type: 设备类型，可选 "chiller" 或 "circulating"，默认 "chiller"

    返回:
    ```json
    {
        "values": [130.3, 21.8, 22.2, ...],
        "ok": true,
        "msg": "ok",
        "device_type": "chiller",
        "device_name": "励磁冷却系统",
        "fields": [
            {"key": "flow_main", "label": "开式水塔输出流量", "unit": "L/Min", "value": 130.3}
        ]
    }
    ```
    """
    if device_type not in templates:
        return JSONResponse(
            status_code=400,
            content={"error": f"不支持的设备类型: {device_type}，可选: {list(templates.keys())}"},
        )

    try:
        # 保存上传图片到临时文件
        suffix = Path(image.filename).suffix if image.filename else ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await image.read()
            tmp.write(content)
            tmp_path = tmp.name

        strategy = templates[device_type]["ocr_strategy"]
        values, ok, msg = ocr_recognize(tmp_path, strategy=strategy)

        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

        # 组装带字段信息的返回
        fields = templates[device_type]["fields"]
        field_results = []
        for i, (key, label, unit) in enumerate(fields):
            val = values[i] if i < len(values) else None
            field_results.append({
                "key": key,
                "label": label,
                "unit": unit,
                "value": val,
            })

        return {
            "values": values,
            "ok": ok,
            "msg": msg,
            "device_type": device_type,
            "device_name": templates[device_type]["name"],
            "fields": field_results,
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"OCR 识别失败: {str(e)}"},
        )


# ===== 记录 API（跨设备共享数据） =====


@app.get("/api/records")
def get_records():
    """获取所有记录（按时间从新到旧排序）"""
    return read_all_records()


@app.post("/api/records")
def create_record(data: dict):
    """
    创建新记录。
    请求体示例: {"savedAt": "2026-06-06 10:30", "waterFlow": "130.5", ...}
    支持 _img 字段（base64 数据 URL）
    """
    now = datetime.now().isoformat()
    data_str = json.dumps(data, ensure_ascii=False)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO records (data, created_at) VALUES (?, ?)",
        (data_str, now),
    )
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": record_id, "ok": True}


@app.put("/api/records/{record_id}")
def update_record(record_id: int, data: dict):
    """更新指定记录"""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id FROM records WHERE id = ?", (record_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="记录不存在")
    data_str = json.dumps(data, ensure_ascii=False)
    conn.execute(
        "UPDATE records SET data = ? WHERE id = ?",
        (data_str, record_id),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/api/records/{record_id}")
def delete_record(record_id: int):
    """删除指定记录"""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id FROM records WHERE id = ?", (record_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="记录不存在")
    conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/api/records")
def clear_records():
    """清空所有记录"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM records")
    conn.commit()
    conn.close()
    return {"ok": True}
