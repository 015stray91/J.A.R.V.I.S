"""
Alerts and events manager for Jarvis X.
Stores reminders in configuration and returns due/upcoming items.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from utils.config_manager import get_config


class AlertsManager:
    """Manage user alerts and events stored in configuration."""

    def __init__(self):
        self.config = get_config()

    def add_alert(self, phrase: str) -> Dict[str, object]:
        return self._add_item('alerts', phrase)

    def add_event(self, phrase: str) -> Dict[str, object]:
        return self._add_item('events', phrase)

    def list_items(self, kind: str = 'all', due_only: bool = False) -> Dict[str, object]:
        data = self._ensure_store()
        now = datetime.now()

        def _filter(items: List[Dict[str, object]]) -> List[Dict[str, object]]:
            active = [item for item in items if not item.get('done', False)]
            if due_only:
                active = [
                    item for item in active
                    if self._parse_iso(item.get('due_at', '')) and self._parse_iso(item.get('due_at', '')) <= now
                ]
            active.sort(key=lambda x: x.get('due_at', ''))
            return active

        alerts = _filter(data.get('alerts', []))
        events = _filter(data.get('events', []))

        if kind == 'alerts':
            return {'success': True, 'kind': kind, 'items': alerts}
        if kind == 'events':
            return {'success': True, 'kind': kind, 'items': events}

        return {
            'success': True,
            'kind': 'all',
            'alerts': alerts,
            'events': events,
            'items': alerts + events
        }

    def _add_item(self, kind: str, phrase: str) -> Dict[str, object]:
        title, due_dt = self._parse_phrase(phrase)
        if not title:
            return {'success': False, 'message': 'Please provide what to remember for this item.'}
        if not due_dt:
            return {
                'success': False,
                'message': 'Please include a time, such as "at 7:30 pm" or "in 30 minutes".'
            }

        data = self._ensure_store()
        items = data.get(kind, [])

        item_id = f"{kind[:-1]}_{int(datetime.now().timestamp())}"
        item = {
            'id': item_id,
            'title': title,
            'due_at': due_dt.isoformat(timespec='minutes'),
            'created_at': datetime.now().isoformat(timespec='seconds'),
            'done': False
        }
        items.append(item)
        data[kind] = items
        self.config.set('planner', data, save=True)

        return {'success': True, 'item': item, 'kind': kind}

    def _ensure_store(self) -> Dict[str, List[Dict[str, object]]]:
        planner = self.config.get('planner', {})
        if not isinstance(planner, dict):
            planner = {}

        if 'alerts' not in planner or not isinstance(planner['alerts'], list):
            planner['alerts'] = []
        if 'events' not in planner or not isinstance(planner['events'], list):
            planner['events'] = []

        return planner

    def _parse_phrase(self, phrase: str) -> Tuple[str, Optional[datetime]]:
        text = (phrase or '').strip()
        if not text:
            return '', None

        due_dt = self._extract_due_datetime(text)
        cleaned = self._strip_time_phrase(text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip(' .')
        return cleaned, due_dt

    def _extract_due_datetime(self, text: str) -> Optional[datetime]:
        lowered = text.lower()
        now = datetime.now()

        in_match = re.search(r'\bin\s+(\d{1,4})\s*(minute|minutes|hour|hours)\b', lowered)
        if in_match:
            amount = int(in_match.group(1))
            unit = in_match.group(2)
            if 'hour' in unit:
                return now + timedelta(hours=amount)
            return now + timedelta(minutes=amount)

        full_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})(?:\s*(am|pm))?\b', lowered)
        if full_match:
            day = full_match.group(1)
            time_part = full_match.group(2)
            ampm = full_match.group(3)
            return self._parse_date_time(day, time_part, ampm)

        day_token = None
        if 'tomorrow' in lowered:
            day_token = (now + timedelta(days=1)).date()
        elif 'today' in lowered:
            day_token = now.date()

        time_match = re.search(r'\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b', lowered)
        if not time_match:
            time_match = re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b', lowered)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            hour = self._normalize_hour(hour, ampm)

            base_date = day_token or now.date()
            candidate = datetime.combine(base_date, datetime.min.time()).replace(hour=hour, minute=minute)
            if day_token is None and candidate <= now:
                candidate = candidate + timedelta(days=1)
            return candidate

        return None

    def _parse_date_time(self, day: str, time_part: str, ampm: Optional[str]) -> Optional[datetime]:
        try:
            hour_s, minute_s = time_part.split(':', 1)
            hour = self._normalize_hour(int(hour_s), ampm)
            minute = int(minute_s)
            dt = datetime.strptime(day, '%Y-%m-%d')
            return dt.replace(hour=hour, minute=minute)
        except (ValueError, TypeError):
            return None

    def _normalize_hour(self, hour: int, ampm: Optional[str]) -> int:
        if ampm == 'pm' and hour < 12:
            return hour + 12
        if ampm == 'am' and hour == 12:
            return 0
        return hour

    def _strip_time_phrase(self, text: str) -> str:
        patterns = [
            r'\bin\s+\d{1,4}\s*(?:minute|minutes|hour|hours)\b',
            r'\b(?:today|tomorrow)\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b',
            r'\bat\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b',
            r'\b\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}\s*(?:am|pm)?\b',
        ]
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.I)
        return cleaned

    def _parse_iso(self, value: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None

