from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from io import BytesIO
from PIL import Image, ImageDraw

app = FastAPI()

# generate tiny JPEG placeholder once
_buf = BytesIO()
_img = Image.new("RGB", (320, 240), color=(10, 10, 10))
_draw = ImageDraw.Draw(_img)
_draw.rectangle([(20, 20), (300, 220)], outline=(200, 200, 200), width=2)
_draw.text((30, 30), "sim-cam", fill=(220, 220, 220))
_img.save(_buf, format="JPEG", quality=70)
JPEG_BYTES = _buf.getvalue()


@app.get("/sim/health")
async def sim_health():
    return {"ok": True}


@app.post("/sim/time")
async def sim_time(payload: dict):
    return JSONResponse({"ok": True, **payload})


@app.get("/sim/camera/{cam_id}/frame")
async def camera_frame(cam_id: str):
    return Response(content=JPEG_BYTES, media_type="image/jpeg")


