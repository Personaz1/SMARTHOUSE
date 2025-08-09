import os
import base64
from typing import Any, Dict, List

import httpx
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


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _gv_annotate_api_key(image_path: str, features: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    api_key = os.getenv("GOOGLE_CLOUD_VISION_API_KEY")
    if not api_key:
        return None
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    img_b64 = base64.b64encode(_read_bytes(image_path)).decode()
    body = {"requests": [{"image": {"content": img_b64}, "features": features}]}
    r = httpx.post(url, json=body, timeout=20)
    r.raise_for_status()
    return r.json()


def gv_labels(image_path: str, max_results: int = 10) -> List[str]:
    # Try API key path first
    try:
        data = _gv_annotate_api_key(image_path, [{"type": "LABEL_DETECTION", "maxResults": max_results}])
        if data:
            anns = (data.get("responses") or [{}])[0].get("labelAnnotations") or []
            return [a.get("description", "").strip() for a in anns if a.get("description")]
    except Exception:
        pass

    # Fallback to SDK (service account)
    client = vision.ImageAnnotatorClient()
    img = vision.Image(content=_read_bytes(image_path))
    res = client.label_detection(image=img, max_results=max_results)
    return [l.description for l in (res.label_annotations or [])]


def gv_objects(image_path: str) -> List[str]:
    # Try API key via annotate
    try:
        data = _gv_annotate_api_key(image_path, [{"type": "OBJECT_LOCALIZATION"}])
        if data:
            anns = (data.get("responses") or [{}])[0].get("localizedObjectAnnotations") or []
            return [a.get("name", "").strip() for a in anns if a.get("name")]
    except Exception:
        pass

    # Fallback SDK
    client = vision.ImageAnnotatorClient()
    img = vision.Image(content=_read_bytes(image_path))
    res = client.object_localization(image=img)
    return [o.name for o in (res.localized_object_annotations or [])]


def gv_ocr(image_path: str) -> str:
    # Try API key via annotate
    try:
        data = _gv_annotate_api_key(image_path, [{"type": "TEXT_DETECTION"}])
        if data:
            full = ((data.get("responses") or [{}])[0].get("fullTextAnnotation") or {}).get("text", "")
            return (full or "").strip()
    except Exception:
        pass

    # Fallback SDK
    client = vision.ImageAnnotatorClient()
    img = vision.Image(content=_read_bytes(image_path))
    res = client.text_detection(image=img)
    return (getattr(getattr(res, "full_text_annotation", None), "text", "") or "").strip()


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



