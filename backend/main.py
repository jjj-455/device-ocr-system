"""
设备点检数字系统 — OCR API 服务
FastAPI + RapidOCR (PP-OCRv4)
部署在 Render.com 免费版
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr_engine import recognize as ocr_recognize
from templates import templates

app = FastAPI(title="设备点检数字系统 OCR API", version="1.0.0")

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
    """健康检查"""
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
async def ocr_recognize(
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
