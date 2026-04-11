from __future__ import annotations

import time
from logging import Logger

from ..config import Settings
from .run_once import RunOnceService


class MonitorService:
    def __init__(self, settings: Settings, run_once_service: RunOnceService, logger: Logger) -> None:
        self.settings = settings
        self.run_once_service = run_once_service
        self.logger = logger

    def run_forever(self) -> int:
        last_exit_code = 0

        while True:
            last_exit_code = self.run_once_service.run()
            self.logger.info(
                "Aguardando %s segundo(s) para o proximo ciclo.",
                self.settings.monitor_interval_seconds,
            )
            time.sleep(self.settings.monitor_interval_seconds)

        return last_exit_code
