from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _to_int(value: str | None, default: int) -> int:
    if value is None or not value.strip():
        return default
    return int(value)


@dataclass(slots=True)
class Settings:
    project_root: Path
    target_url: str
    source_view_name: str
    consultant_name: str
    monitor_interval_seconds: int
    only_open: bool
    only_assigned_to_me: bool
    first_page_only: bool
    browser_headless: bool
    playwright_channel: str | None
    playwright_timeout_ms: int
    browser_profile_dir: Path
    database_path: Path
    log_file_path: Path
    teams_webhook_url: str
    teams_request_timeout_seconds: int

    @classmethod
    def load(cls) -> "Settings":
        project_root = Path(__file__).resolve().parents[2]
        load_dotenv(project_root / ".env", override=False)

        def resolve_path(raw_value: str, default_relative: str) -> Path:
            chosen = raw_value.strip() if raw_value and raw_value.strip() else default_relative
            path = Path(chosen)
            if not path.is_absolute():
                path = project_root / path
            return path

        channel = os.getenv("PLAYWRIGHT_CHANNEL", "msedge").strip()
        settings = cls(
            project_root=project_root,
            target_url=os.getenv("TARGET_URL", "https://megahub.megawork.com/Chamado/MinhaFila").strip(),
            source_view_name=os.getenv("SOURCE_VIEW_NAME", "Minha Fila").strip(),
            consultant_name=os.getenv("CONSULTANT_NAME", "Marcus Vinicius Maciel Vieira").strip(),
            monitor_interval_seconds=_to_int(os.getenv("MONITOR_INTERVAL_SECONDS"), 120),
            only_open=_to_bool(os.getenv("ONLY_OPEN"), True),
            only_assigned_to_me=_to_bool(os.getenv("ONLY_ASSIGNED_TO_ME"), True),
            first_page_only=_to_bool(os.getenv("FIRST_PAGE_ONLY"), True),
            browser_headless=_to_bool(os.getenv("BROWSER_HEADLESS"), True),
            playwright_channel=channel or None,
            playwright_timeout_ms=_to_int(os.getenv("PLAYWRIGHT_TIMEOUT_MS"), 30000),
            browser_profile_dir=resolve_path(os.getenv("BROWSER_PROFILE_DIR", ""), "data/browser-profile"),
            database_path=resolve_path(os.getenv("DATABASE_PATH", ""), "data/megahub-monitor.db"),
            log_file_path=resolve_path(os.getenv("LOG_FILE_PATH", ""), "data/logs/monitor.log"),
            teams_webhook_url=os.getenv("TEAMS_WEBHOOK_URL", "").strip(),
            teams_request_timeout_seconds=_to_int(os.getenv("TEAMS_REQUEST_TIMEOUT_SECONDS"), 15),
        )
        settings.ensure_directories()
        return settings

    def ensure_directories(self) -> None:
        self.browser_profile_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

