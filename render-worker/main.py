import json
import os
import secrets
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Chill Bros Blender Render Worker", version="1.0.0")


class Room(BaseModel):
    id: str
    name: str = "Room"
    width: float = Field(default=12, gt=0, le=200)
    depth: float = Field(default=12, gt=0, le=200)
    height: float = Field(default=8, gt=0, le=50)
    verified: bool = False


class Brief(BaseModel):
    customer: str = ""
    address: str = ""
    projectTitle: str = ""
    requestedChanges: str = ""
    finishedProduct: str = ""
    fieldNotes: str = ""


class RenderRequest(BaseModel):
    projectName: str = "Chill Bros Project"
    notes: str = ""
    rooms: List[Room]
    brief: Optional[Brief] = None
    environment: str = "clean studio"
    presentation: str = "wide customer presentation"
    samples: int = Field(default=96, ge=16, le=256)
    width: int = Field(default=1536, ge=640, le=2048)
    height: int = Field(default=1024, ge=480, le=1536)


def require_token(authorization: Optional[str]) -> None:
    expected = os.environ.get("BLENDER_RENDER_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Render-worker token is not configured")
    supplied = ""
    if authorization and authorization.lower().startswith("bearer "):
        supplied = authorization[7:].strip()
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid render-worker token")


@app.get("/health")
def health():
    try:
        completed = subprocess.run(
            ["blender", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
            check=False,
        )
        first_line = (completed.stdout or "").splitlines()[0] if completed.stdout else ""
        return {
            "ok": completed.returncode == 0,
            "engine": "blender",
            "mode": "cycles",
            "version": first_line,
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Blender unavailable: {exc}") from exc


@app.post("/render")
def render_scene(payload: RenderRequest, authorization: Optional[str] = Header(default=None)):
    require_token(authorization)
    if not payload.rooms:
        raise HTTPException(status_code=400, detail="At least one room is required")

    temp_dir = tempfile.mkdtemp(prefix="chillbros-blender-")
    request_path = Path(temp_dir) / "scene.json"
    output_path = Path(temp_dir) / "render.png"
    request_path.write_text(json.dumps(payload.model_dump(), indent=2), encoding="utf-8")

    blender_script = Path(__file__).with_name("render_scene.py")
    command = [
        "blender",
        "-b",
        "--python",
        str(blender_script),
        "--",
        str(request_path),
        str(output_path),
    ]

    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=240,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Blender render timed out") from exc

    if completed.returncode != 0 or not output_path.exists():
        tail = (completed.stdout or "")[-3000:]
        raise HTTPException(status_code=500, detail=f"Blender render failed: {tail}")

    return FileResponse(
        path=str(output_path),
        media_type="image/png",
        filename="chill-bros-blender-render.png",
        background=None,
    )
