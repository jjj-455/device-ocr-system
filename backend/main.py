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
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr_engine import recognize as ocr_recognize
from templates import templates

app = FastAPI(title="设备点检数字系统 OCR API", version="1.2.0")

# ---- 管理员认证 ----
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
_admin_tokens = {}  # token -> expiry datetime


def verify_admin(authorization: str = Header(None)):
    """验证 Bearer token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:]
    expiry = _admin_tokens.get(token)
    if not expiry or datetime.now() > expiry:
        if token in _admin_tokens:
            del _admin_tokens[token]
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return True


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


def read_all_records(include_images=False):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, data FROM records ORDER BY id").fetchall()
    conn.close()
    result = [serialize_record(r) for r in rows]
    if not include_images:
        for r in result:
            r.pop("_img", None)
    return result


def read_one_record(record_id: int):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id, data FROM records WHERE id = ?", (record_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return serialize_record(row)


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


# ===== 管理员认证 API =====


@app.post("/api/auth/login")
def auth_login(data: dict):
    """管理员登录，返回 token"""
    pwd = data.get("password", "")
    if not pwd or pwd != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="密码错误")
    token = secrets.token_hex(32)
    _admin_tokens[token] = datetime.now() + timedelta(hours=24)
    return {"token": token, "admin": True, "expires_in": 86400}


@app.post("/api/auth/logout")
def auth_logout(authorization: str = Header(None)):
    """退出登录"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        _admin_tokens.pop(token, None)
    return {"ok": True}


@app.get("/api/auth/verify")
def auth_verify(authorization: str = Header(None)):
    """验证 token 是否有效"""
    if not authorization or not authorization.startswith("Bearer "):
        return {"valid": False, "admin": False}
    token = authorization[7:]
    expiry = _admin_tokens.get(token)
    if not expiry or datetime.now() > expiry:
        if token in _admin_tokens:
            del _admin_tokens[token]
        return {"valid": False, "admin": False}
    return {"valid": True, "admin": True}


# ===== 记录 API（跨设备共享数据） =====


@app.get("/api/records")
def get_records(images: bool = False):
    """
    获取所有记录（按时间从新到旧排序）。
    ?images=true 时包含 base64 图片数据（默认不包含，加快列表加载）
    """
    return read_all_records(include_images=images)


@app.post("/api/records")
def create_record(data: dict, _=Depends(verify_admin)):
    """
    创建新记录（需要管理员权限）。
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


@app.get("/api/records/{record_id}")
def get_record(record_id: int):
    """获取单条记录（含图片数据）"""
    rec = read_one_record(record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return rec


@app.put("/api/records/{record_id}")
def update_record(record_id: int, data: dict, _=Depends(verify_admin)):
    """更新指定记录（需要管理员权限）"""
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
def delete_record(record_id: int, _=Depends(verify_admin)):
    """删除指定记录（需要管理员权限）"""
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
def clear_records(_=Depends(verify_admin)):
    """清空所有记录（需要管理员权限）"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM records")
    conn.commit()
    conn.close()
    return {"ok": True}
