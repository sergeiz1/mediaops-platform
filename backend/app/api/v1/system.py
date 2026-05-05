from __future__ import annotations

from collections import deque
from pathlib import Path
import subprocess
import time

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/system")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _read_tail(path: Path, lines: int) -> str:
    if not path.exists():
        return ""
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return "".join(deque(fh, maxlen=lines))


def _normalize_backend_logs(content: str) -> str:
    if not content:
        return content

    lines = content.splitlines()
    # If PowerShell wrote an error record block (NativeCommandError), drop it
    # and keep the actual server logs from first Uvicorn line onward.
    uvicorn_start_idx = next((i for i, line in enumerate(lines) if line.startswith("INFO:     Uvicorn running")), -1)
    if uvicorn_start_idx > 0:
        lines = lines[uvicorn_start_idx:]

    return "\n".join(lines).strip() + ("\n" if lines else "")


def _docker_compose_logs(service: str, lines: int) -> str:
    cmd = ["docker", "compose", "logs", "--no-color", f"--tail={lines}", service]
    proc = subprocess.run(
        cmd,
        cwd=_project_root(),
        capture_output=True,
        text=True,
        timeout=8,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "docker compose logs failed").strip())
    return proc.stdout


def _logs_dir() -> Path:
    path = _project_root() / "backend" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _pid_file(service: str) -> Path:
    return _logs_dir() / f"{service}.pid"


def _read_pid(service: str) -> int | None:
    path = _pid_file(service)
    if not path.exists():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def _write_pid(service: str, pid: int) -> None:
    _pid_file(service).write_text(str(pid), encoding="utf-8")


def _clear_pid(service: str) -> None:
    path = _pid_file(service)
    if path.exists():
        path.unlink(missing_ok=True)


def _is_pid_running(pid: int) -> bool:
    proc = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}"],
        capture_output=True,
        text=True,
        timeout=4,
    )
    return proc.returncode == 0 and str(pid) in (proc.stdout or "")


def _service_status(service: str) -> dict[str, str | int | bool | None]:
    pid = _read_pid(service)
    running = bool(pid and _is_pid_running(pid))
    if pid and not running:
        _clear_pid(service)
        pid = None
    return {"service": service, "running": running, "pid": pid}


def _start_managed_service(service: str) -> dict[str, str | int | bool | None]:
    state = _service_status(service)
    if state["running"]:
        return state

    backend_dir = _project_root() / "backend"
    if service == "worker":
        command = "Set-Location .; .\\run_worker.ps1"
    elif service == "api":
        command = "Set-Location .; .\\run_api.ps1"
    else:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service}'")

    creationflags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen(  # noqa: S603
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        cwd=backend_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    _write_pid(service, proc.pid)
    time.sleep(0.4)
    return _service_status(service)


def _stop_managed_service(service: str) -> dict[str, str | int | bool | None]:
    pid = _read_pid(service)
    if not pid:
        return {"service": service, "running": False, "pid": None}

    if _is_pid_running(pid):
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True,
            timeout=8,
        )

    time.sleep(0.3)
    state = _service_status(service)
    if not state["running"]:
        _clear_pid(service)
        state["pid"] = None
    return state


@router.get("/logs/{service}")
def get_service_logs(
    service: str,
    lines: int = Query(default=120, ge=20, le=1000),
) -> dict[str, str | int]:
    service_name = service.strip().lower()
    logs_dir = _project_root() / "backend" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    if service_name == "worker":
        content = _read_tail(logs_dir / "worker.log", lines)
        if not content:
            content = (
                "No worker.log found yet.\n"
                "Start worker via: cd backend && .\\run_worker.ps1\n"
                "Then reload this logs page."
            )
        return {"service": "worker", "lines": lines, "content": content}

    if service_name == "backend":
        content = _read_tail(logs_dir / "backend.log", lines)
        if not content:
            content = (
                "No backend.log found yet.\n"
                "Recommended start command:\n"
                "cd backend && .\\run_api.ps1"
            )
        else:
            content = _normalize_backend_logs(content)
        return {"service": "backend", "lines": lines, "content": content}

    if service_name == "opensearch":
        try:
            content = _docker_compose_logs("opensearch", lines)
            if not content.strip():
                content = "No OpenSearch log lines returned."
            return {"service": "opensearch", "lines": lines, "content": content}
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Could not fetch OpenSearch logs: {exc}") from exc

    raise HTTPException(status_code=404, detail=f"Unknown service '{service_name}'")


@router.get("/control/status")
def get_control_status() -> dict[str, dict[str, str | int | bool | None]]:
    return {
        "worker": _service_status("worker"),
        "api": _service_status("api"),
    }


@router.post("/control/{service}/{action}")
def control_service(service: str, action: str) -> dict[str, str | int | bool | None]:
    svc = service.strip().lower()
    act = action.strip().lower()
    if svc not in {"worker", "api"}:
        raise HTTPException(status_code=404, detail=f"Unknown service '{svc}'")
    if act not in {"start", "stop", "restart"}:
        raise HTTPException(status_code=400, detail=f"Unknown action '{act}'")

    if act == "start":
        state = _start_managed_service(svc)
    elif act == "stop":
        state = _stop_managed_service(svc)
    else:
        _stop_managed_service(svc)
        state = _start_managed_service(svc)

    return {"service": svc, "action": act, **state}
