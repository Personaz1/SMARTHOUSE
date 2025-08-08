import os
from typing import Any, Dict, Optional
import httpx


GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


async def generate_with_gemini(prompt: str) -> Optional[str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    headers = {"Content-Type": "application/json"}
    body: Dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ]
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{GEMINI_API}?key={api_key}", headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts)
            return text or None
        except Exception:
            return None


async def generate_response(query: str, snapshot: Dict[str, Any], recent_events: Any) -> str:
    context = (
        f"System: devices={len(snapshot.get('devices', {}))}, "
        f"zones={len(snapshot.get('zones', {}))}, "
        f"security_mode={snapshot.get('security_mode')}\n"
        f"Recent events: " + ", ".join([e.get("type", "event") for e in (recent_events or [])][-10:])
    )
    prompt = context + "\n\nUser: " + query
    text = await generate_with_gemini(prompt)
    if not text:
        # Fallback minimal heuristic
        return "Пока без модели: «" + query + "». Система активна; данных достаточно для ответа после включения модели."
    return text


