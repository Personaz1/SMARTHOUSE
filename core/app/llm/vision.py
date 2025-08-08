import os
from typing import Any, Dict, List

import google.generativeai as genai
from google.cloud import vision


def _detect_mime(path: str) -> str:
    lp = path.lower()
    if lp.endswith(".png"):
        return "image/png"
    if lp.endswith(".gif"):
        return "image/gif"
    if lp.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


def gv_labels(image_path: str, max_results: int = 10) -> List[str]:
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as f:
        img = vision.Image(content=f.read())
    res = client.label_detection(image=img, max_results=max_results)
    return [l.description for l in (res.label_annotations or [])]


def gv_objects(image_path: str) -> List[str]:
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as f:
        img = vision.Image(content=f.read())
    res = client.object_localization(image=img)
    return [o.name for o in (res.localized_object_annotations or [])]


def gv_ocr(image_path: str) -> str:
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as f:
        img = vision.Image(content=f.read())
    res = client.text_detection(image=img)
    return (res.full_text_annotation.text or "").strip()


def analyze_with_gemini(image_path: str, prompt: str, models=("gemini-1.5-pro", "gemini-1.5-flash")) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API key missing"
    genai.configure(api_key=api_key)
    mime = _detect_mime(image_path)
    last_err = None
    for m in models:
        try:
            model = genai.GenerativeModel(m)
            try:
                up = genai.upload_file(image_path, mime_type=mime)
                parts = [{"text": prompt}, {"file_data": {"file_uri": up.uri, "mime_type": mime}}]
                resp = model.generate_content(parts)
                return getattr(resp, "text", str(resp))
            except Exception:
                with open(image_path, "rb") as f:
                    img = f.read()
                parts = [{"mime_type": mime, "data": img}, {"text": prompt}]
                resp = model.generate_content(parts)
                return getattr(resp, "text", str(resp))
        except Exception as e:
            last_err = str(e)
            continue
    return f"Gemini error: {last_err or 'unknown'}"


