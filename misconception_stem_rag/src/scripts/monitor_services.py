"""Continuous health monitor for docker compose stack."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

COMPOSE_DIR = Path(__file__).resolve().parents[2]
LOG_PATH = COMPOSE_DIR / "logs" / "health_report.json"
HEALTH_URL = "http://localhost:8000/health"
CHECK_INTERVAL_SECONDS = 600


def _run_compose_ps() -> list[dict[str, Any]]:
    result = subprocess.run(
        ["docker", "compose", "ps", "--format", "json"],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(COMPOSE_DIR),
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "docker compose ps failed")
    output = result.stdout.strip()
    return json.loads(output or "[]")


def _evaluate_services(raw: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    services: list[dict[str, Any]] = []
    failed: list[str] = []
    for item in raw:
        name = item.get("Service") or item.get("Name") or "unknown"
        state = str(item.get("State", ""))
        status = str(item.get("Status", ""))
        lower_state = state.lower()
        lower_status = status.lower()
        is_running = "running" in lower_state or lower_status.startswith("up")
        is_unhealthy = "unhealthy" in lower_status or "dead" in lower_state
        healthy = is_running and not is_unhealthy
        services.append(
            {
                "name": name,
                "state": state,
                "status": status,
                "healthy": healthy,
            }
        )
        if not healthy:
            failed.append(name)
    return services, failed


def _check_api_health(timeout: float = 5.0) -> tuple[bool, str | None]:
    try:
        response = httpx.get(HEALTH_URL, timeout=timeout)
        if response.status_code == 200:
            return True, None
        return False, f"Unexpected status: {response.status_code}"
    except Exception as exc:  # pragma: no cover - network use
        return False, str(exc)


def _restart_services(service_names: list[str]) -> list[str]:
    if not service_names:
        return []
    result = subprocess.run(
        ["docker", "compose", "restart", *service_names],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(COMPOSE_DIR),
    )
    if result.returncode != 0:
        return [f"Failed to restart {service_names}: {result.stderr.strip()}"]
    return [f"Restarted: {', '.join(service_names)}"]


def _append_report(entry: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        if not isinstance(existing, list):  # defensive
            existing = []
    except FileNotFoundError:
        existing = []
    except json.JSONDecodeError:
        existing = []
    existing.append(entry)
    LOG_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def monitor(interval: int = CHECK_INTERVAL_SECONDS) -> None:
    print("Starting continuous monitor. Press Ctrl+C to exit.")
    while True:
        timestamp = datetime.now(timezone.utc).isoformat()
        compose_info: list[dict[str, Any]] = []
        compose_errors: list[str] = []
        try:
            raw = _run_compose_ps()
            compose_info, failed_services = _evaluate_services(raw)
        except Exception as exc:  # pragma: no cover - command failure
            compose_errors.append(str(exc))
            failed_services = []

        api_ok, api_error = _check_api_health()
        if not api_ok:
            compose_errors.append(api_error or "Health check failed")
            if compose_info:
                api_services = [svc["name"] for svc in compose_info if "api" in svc["name"].lower()]
                if api_services:
                    for svc in api_services:
                        if svc not in failed_services:
                            failed_services.append(svc)
                else:
                    failed_services = list({svc["name"] for svc in compose_info})

        restart_actions = _restart_services(failed_services) if failed_services else []

        entry = {
            "timestamp": timestamp,
            "services": compose_info,
            "health_check": {
                "url": HEALTH_URL,
                "ok": api_ok,
                "error": api_error,
            },
            "errors": compose_errors,
            "restart_actions": restart_actions,
        }
        _append_report(entry)

        status_line = "OK" if not compose_errors and not restart_actions else "DEGRADED"
        print(f"[{timestamp}] Monitor status: {status_line}")
        if compose_errors:
            for err in compose_errors:
                print(f"  issue: {err}")
        if restart_actions:
            for note in restart_actions:
                print(f"  action: {note}")

        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitor stopped by user.")
            sys.exit(0)


if __name__ == "__main__":
    monitor()
