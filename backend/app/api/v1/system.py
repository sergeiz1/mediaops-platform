from __future__ import annotations

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
    if lines <= 0:
        return ""

    # Efficient tail implementation for very large files:
    # read only from the end in chunks until enough line breaks are found.
    chunk_size = 4096
    data = bytearray()
    newline_count = 0

    with path.open("rb") as fh:
        fh.seek(0, 2)
        file_size = fh.tell()
        pos = file_size

        while pos > 0 and newline_count <= lines:
            read_size = chunk_size if pos >= chunk_size else pos
            pos -= read_size
            fh.seek(pos)
            chunk = fh.read(read_size)
            data[:0] = chunk
            newline_count += chunk.count(b"\n")

    text = data.decode("utf-8", errors="replace")
    tail_lines = text.splitlines()[-lines:]
    return ("\n".join(tail_lines) + "\n") if tail_lines else ""


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


def _rotate_log_file(path: Path, max_bytes: int = 2 * 1024 * 1024 * 1024, keep: int = 5) -> None:
    if not path.exists():
        return
    if path.stat().st_size <= max_bytes:
        return

    # Rotate: file.log.(keep-1) -> file.log.keep ... file.log -> file.log.1
    for idx in range(keep, 0, -1):
        src = path.with_name(f"{path.name}.{idx}")
        dst = path.with_name(f"{path.name}.{idx + 1}")
        if src.exists():
            if idx == keep:
                src.unlink(missing_ok=True)
            else:
                src.replace(dst)
    path.replace(path.with_name(f"{path.name}.1"))


def _clear_log_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
        return
    try:
        with path.open("w", encoding="utf-8"):
            pass
    except PermissionError as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Log file is in use: {path.name}. "
                "Stop the related service first (API log runner/Worker), then clear logs."
            ),
        ) from exc


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
    logs_dir = _logs_dir()
    creationflags = 0x00000200 | 0x08000000  # CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0  # SW_HIDE
    pythonw = backend_dir / ".venv" / "Scripts" / "pythonw.exe"
    python = backend_dir / ".venv" / "Scripts" / "python.exe"
    python_bin = pythonw if pythonw.exists() else python

    if service == "worker":
        worker_log_path = logs_dir / "worker.log"
        _rotate_log_file(worker_log_path)
        worker_log = worker_log_path.open("a", encoding="utf-8", buffering=1)
        proc = subprocess.Popen(  # noqa: S603
            [
                str(python_bin),
                "-X",
                "utf8",
                "-m",
                "celery",
                "-A",
                "app.workers.celery_app:celery_app",
                "worker",
                "--loglevel=info",
                "--pool=solo",
            ],
            cwd=backend_dir,
            stdout=worker_log,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            startupinfo=startupinfo,
            close_fds=True,
        )
        worker_log.close()
    elif service == "api":
        api_log_path = logs_dir / "backend.log"
        _rotate_log_file(api_log_path)
        api_log = api_log_path.open("a", encoding="utf-8", buffering=1)
        proc = subprocess.Popen(  # noqa: S603
            [
                str(python_bin),
                "-X",
                "utf8",
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ],
            cwd=backend_dir,
            stdout=api_log,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            startupinfo=startupinfo,
            close_fds=True,
        )
        api_log.close()
    else:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service}'")

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
) -> dict[str, str | int | None]:
    service_name = service.strip().lower()
    logs_dir = _project_root() / "backend" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    if service_name == "worker":
        log_path = logs_dir / "worker.log"
        content = _read_tail(logs_dir / "worker.log", lines)
        if not content:
            content = (
                "No worker.log found yet.\n"
                "Start worker via: cd backend && .\\run_worker.ps1\n"
                "Then reload this logs page."
            )
        return {
            "service": "worker",
            "lines": lines,
            "content": content,
            "log_size_bytes": log_path.stat().st_size if log_path.exists() else 0,
        }

    if service_name == "backend":
        log_path = logs_dir / "backend.log"
        content = _read_tail(logs_dir / "backend.log", lines)
        if not content or not content.strip():
            content = (
                "Backend log is empty.\n"
                "Start API via System Status (API log runner -> Start) or with:\n"
                "cd backend && .\\run_api.ps1\n"
                "Then call an endpoint (e.g. /health) and reload this page."
            )
        else:
            content = _normalize_backend_logs(content)
        return {
            "service": "backend",
            "lines": lines,
            "content": content,
            "log_size_bytes": log_path.stat().st_size if log_path.exists() else 0,
        }

    if service_name == "opensearch":
        try:
            content = _docker_compose_logs("opensearch", lines)
            if not content.strip():
                content = "No OpenSearch log lines returned."
            return {
                "service": "opensearch",
                "lines": lines,
                "content": content,
                "log_size_bytes": len(content.encode("utf-8", errors="replace")),
            }
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


@router.post("/logs/{service}/clear")
def clear_service_logs(service: str) -> dict[str, str]:
    service_name = service.strip().lower()
    logs_dir = _logs_dir()

    if service_name == "backend":
        _clear_log_file(logs_dir / "backend.log")
        return {"service": "backend", "status": "cleared"}
    if service_name == "worker":
        _clear_log_file(logs_dir / "worker.log")
        return {"service": "worker", "status": "cleared"}
    if service_name == "opensearch":
        raise HTTPException(
            status_code=400,
            detail="OpenSearch logs are provided by Docker. Clearing from app is not supported.",
        )

    raise HTTPException(status_code=404, detail=f"Unknown service '{service_name}'")
