import json
import os
import secrets
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import jwt
import requests
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from jwt import PyJWKClient
from pydantic import BaseModel, Field

app = FastAPI(title="Chill Bros Blender Render Worker", version="1.2.0")

VERCEL_OWNER_ID = "team_dDuPw261pT7tztxFcv8fA0aw"
VERCEL_PROJECT_ID = "prj_PhQvuJOVigfQZpnx71re7o1rnGpl"
VERCEL_TEAM_SLUG = "chill-pros"
VERCEL_AUDIENCE = f"https://vercel.com/{VERCEL_TEAM_SLUG}"
ALLOWED_ISSUERS = {
    f"https://oidc.vercel.com/{VERCEL_TEAM_SLUG}",
    "https://oidc.vercel.com",
}
ALLOWED_ENVIRONMENTS = {"production", "preview"}
_deep_health_cache: Optional[dict] = None


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
    samples: int = Field(default=48, ge=16, le=128)
    width: int = Field(default=1536, ge=640, le=2048)
    height: int = Field(default=1024, ge=480, le=1536)


def _bearer_token(authorization: Optional[str]) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return ""


@lru_cache(maxsize=4)
def _jwks_candidates(issuer: str) -> tuple[str, ...]:
    candidates: list[str] = []
    config_urls = [
        f"{issuer.rstrip('/')}/.well-known/openid-configuration",
        f"https://oidc.vercel.com/.well-known/openid-configuration/{VERCEL_TEAM_SLUG}",
        "https://oidc.vercel.com/.well-known/openid-configuration",
    ]
    for config_url in config_urls:
        try:
            response = requests.get(config_url, timeout=8)
            if not response.ok:
                continue
            jwks_uri = str(response.json().get("jwks_uri") or "").strip()
            if jwks_uri and jwks_uri.startswith("https://oidc.vercel.com"):
                candidates.append(jwks_uri)
        except Exception:
            continue

    candidates.extend(
        [
            f"{issuer.rstrip('/')}/.well-known/jwks",
            "https://oidc.vercel.com/.well-known/jwks",
        ]
    )
    return tuple(dict.fromkeys(candidates))


def _verify_vercel_oidc(token: str) -> None:
    try:
        unverified = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
                "verify_iss": False,
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid worker identity token") from exc

    issuer = str(unverified.get("iss") or "").rstrip("/")
    if issuer not in ALLOWED_ISSUERS:
        raise HTTPException(status_code=401, detail="Worker identity issuer is not allowed")

    payload = None
    last_error: Exception | None = None
    for jwks_uri in _jwks_candidates(issuer):
        try:
            signing_key = PyJWKClient(jwks_uri, cache_keys=True).get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=VERCEL_AUDIENCE,
                issuer=issuer,
                leeway=20,
            )
            break
        except Exception as exc:
            last_error = exc

    if payload is None:
        raise HTTPException(status_code=401, detail="Unable to verify Vercel worker identity") from last_error

    if payload.get("owner_id") != VERCEL_OWNER_ID:
        raise HTTPException(status_code=401, detail="Worker identity owner mismatch")
    if payload.get("project_id") != VERCEL_PROJECT_ID:
        raise HTTPException(status_code=401, detail="Worker identity project mismatch")
    if payload.get("environment") not in ALLOWED_ENVIRONMENTS:
        raise HTTPException(status_code=401, detail="Worker identity environment mismatch")


def require_token(authorization: Optional[str]) -> None:
    supplied = _bearer_token(authorization)
    if not supplied:
        raise HTTPException(status_code=401, detail="Missing render-worker authorization")

    expected = os.environ.get("BLENDER_RENDER_TOKEN", "").strip()
    if expected and secrets.compare_digest(supplied, expected):
        return

    _verify_vercel_oidc(supplied)


def _run_blender(payload: RenderRequest, timeout_seconds: int = 240) -> tuple[Path, str]:
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
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Blender render timed out") from exc

    output = completed.stdout or ""
    if completed.returncode != 0 or not output_path.exists():
        raise HTTPException(status_code=500, detail=f"Blender render failed: {output[-3000:]}")
    return output_path, output


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
            "auth": "vercel-oidc",
            "deepTest": _deep_health_cache,
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Blender unavailable: {exc}") from exc


@app.get("/health/deep")
def deep_health():
    global _deep_health_cache
    if _deep_health_cache is not None:
        return _deep_health_cache

    payload = RenderRequest(
        projectName="Chill Bros Blender Self Test",
        notes="mini split",
        rooms=[Room(id="self-test", name="Test Room", width=10, depth=10, height=8, verified=True)],
        brief=Brief(projectTitle="Worker Self Test", finishedProduct="mini split installation"),
        samples=16,
        width=640,
        height=480,
    )
    output_path, output = _run_blender(payload, timeout_seconds=120)
    _deep_health_cache = {
        "ok": True,
        "engine": "blender",
        "mode": "cycles",
        "rendered": output_path.exists(),
        "bytes": output_path.stat().st_size if output_path.exists() else 0,
        "cyclesSeen": "Cycles" in output or "cycles" in output.lower(),
        "cached": True,
    }
    return _deep_health_cache


@app.post("/render")
def render_scene(payload: RenderRequest, authorization: Optional[str] = Header(default=None)):
    require_token(authorization)
    if not payload.rooms:
        raise HTTPException(status_code=400, detail="At least one room is required")

    output_path, _ = _run_blender(payload, timeout_seconds=240)
    return FileResponse(
        path=str(output_path),
        media_type="image/png",
        filename="chill-bros-blender-render.png",
        background=None,
    )
