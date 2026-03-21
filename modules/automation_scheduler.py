"""
Automation scheduler for Jarvis X
Runs configured smart-home and Fire TV actions on schedule
"""

from datetime import datetime
from threading import Thread, Event
from typing import Dict, Optional
from utils.logger import get_logger
from utils.config_manager import get_config


logger = get_logger()
config = get_config()


class AutomationScheduler:
    """Background scheduler for recurring automations."""

    def __init__(self, smart_home_manager, android_tools_manager):
        self.smart_home_manager = smart_home_manager
        self.android_tools_manager = android_tools_manager
        self.stop_event = Event()
        self.thread: Optional[Thread] = None
        self.is_running = False
        self.last_run = {}

    def start(self):
        if self.is_running:
            return

        self.is_running = True
        self.stop_event.clear()
        self.thread = Thread(target=self._loop, daemon=True)
        self.thread.start()
        logger.info('Automation scheduler started')

    def stop(self):
        if not self.is_running:
            return

        self.is_running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2)
        logger.info('Automation scheduler stopped')

    def _loop(self):
        while not self.stop_event.is_set():
            try:
                self.tick()
            except Exception as e:
                logger.error(f'Automation scheduler error: {e}')

            self.stop_event.wait(20)

    def tick(self):
        automation_cfg = config.get('automations', {})
        if not automation_cfg.get('enabled', False):
            return

        schedules = automation_cfg.get('schedules', [])
        now = datetime.now()

        for schedule in schedules:
            should_run, run_key = self._should_run(schedule, now)
            if not should_run or not run_key:
                continue

            schedule_id = str(schedule.get('id', 'unnamed'))
            dedupe_key = f"{schedule_id}:{run_key}"
            if self.last_run.get(dedupe_key):
                continue

            result = self._execute(schedule)
            if result.get('success'):
                logger.info(f"Automation '{schedule_id}' executed")
                self.last_run[dedupe_key] = True
            else:
                logger.warning(f"Automation '{schedule_id}' failed: {result.get('message', 'unknown error')}")

    @staticmethod
    def _day_allowed(days, now: datetime) -> bool:
        if not days:
            return True
        day = now.strftime('%a').lower()
        normalized = [str(d).strip().lower()[:3] for d in days]
        return day in normalized

    def _should_run(self, schedule: Dict, now: datetime):
        if not schedule.get('enabled', True):
            return False, None

        if not self._day_allowed(schedule.get('days', []), now):
            return False, None

        every = int(schedule.get('every_minutes', 0) or 0)
        if every > 0:
            if now.minute % every != 0:
                return False, None

            window_start = str(schedule.get('window_start', '')).strip()
            window_end = str(schedule.get('window_end', '')).strip()
            if window_start and window_end:
                current = now.strftime('%H:%M')
                if not (window_start <= current <= window_end):
                    return False, None

            return True, now.strftime('%Y%m%d%H%M')

        at_time = str(schedule.get('time', '')).strip()
        if not at_time:
            return False, None

        if now.strftime('%H:%M') != at_time:
            return False, None

        return True, now.strftime('%Y%m%d%H%M')

    def _execute(self, schedule: Dict) -> Dict[str, object]:
        action = schedule.get('action', {})
        action_type = str(action.get('type', '')).strip().lower()

        if action_type == 'smart_switch':
            device = str(action.get('device', '')).strip()
            state = str(action.get('state', '')).strip().lower()
            return self.smart_home_manager.set_switch(device, state)

        if action_type == 'firetv_key':
            key_name = str(action.get('key', '')).strip()
            return self.android_tools_manager.firetv_key(key_name)

        if action_type == 'firetv_connect':
            ip = str(action.get('ip', '')).strip()
            return self.android_tools_manager.firetv_connect(ip)

        if action_type == 'adb':
            args = str(action.get('args', '')).strip()
            return self.android_tools_manager.run_adb(args)

        return {
            'success': False,
            'message': f'Unsupported automation action: {action_type}'
        }

