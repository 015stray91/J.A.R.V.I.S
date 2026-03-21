"""Workflow memory manager for Jarvis X.

Persists command history and metadata so workflows can be reconstructed later.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

try:
    import psutil
except Exception:  # pragma: no cover - optional safety
    psutil = None

from utils.config_manager import get_config


class WorkflowMemoryManager:
    """Persist and export workflow history."""

    def __init__(self):
        self.config = get_config()
        self.memory_file = Path(self.config.get('workflow.memory_file', 'data/workflow_memory.json'))
        self.max_entries = int(self.config.get('workflow.max_entries', 800) or 800)
        self.data = {
            'version': 1,
            'created_at': datetime.now().isoformat(timespec='seconds'),
            'entries': [],
            'preferences': {
                'anti_repeat': True,
                'markdown_instructions': True,
                'instruction_style': 'numbered',
                'verbosity': 'concise'
            }
        }
        self._load()

    def record(self,
               command: str,
               intent: str,
               success: bool,
               response: str,
               parameters: Optional[Dict] = None,
               confidence: float = 0.0,
               latency_ms: Optional[float] = None) -> None:
        metrics = self._capture_system_metrics()
        entry = {
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'command': (command or '').strip(),
            'intent': intent,
            'success': bool(success),
            'confidence': round(float(confidence), 3),
            'parameters': parameters or {},
            'response': (response or '')[:280],
            'latency_ms': round(float(latency_ms), 1) if latency_ms is not None else None,
            'metrics': metrics
        }

        entries: List[Dict] = self.data.get('entries', [])
        entries.append(entry)
        if len(entries) > self.max_entries:
            entries = entries[-self.max_entries:]
        self.data['entries'] = entries
        self._save()

    def status(self) -> Dict[str, object]:
        entries: List[Dict] = self.data.get('entries', [])
        total = len(entries)
        success_count = len([e for e in entries if e.get('success')])
        latencies = [float(e.get('latency_ms')) for e in entries if isinstance(e.get('latency_ms'), (int, float))]
        intents: Dict[str, int] = {}
        for entry in entries:
            name = str(entry.get('intent', 'unknown'))
            intents[name] = intents.get(name, 0) + 1

        top_intents = sorted(intents.items(), key=lambda x: x[1], reverse=True)[:5]
        last_entry = entries[-1] if entries else None

        return {
            'success': True,
            'total_entries': total,
            'retention_limit': self.max_entries,
            'success_rate': round((success_count / total) * 100, 1) if total else 0.0,
            'avg_latency_ms': round(sum(latencies) / len(latencies), 1) if latencies else None,
            'top_intents': top_intents,
            'last_entry': last_entry,
            'memory_file': str(self.memory_file)
        }

    def learning_curve(self, days: int = 7) -> Dict[str, object]:
        cutoff = datetime.now() - timedelta(days=max(1, int(days)))
        entries = [e for e in self.data.get('entries', []) if self._parse_iso(e.get('timestamp')) and self._parse_iso(e.get('timestamp')) >= cutoff]
        if not entries:
            return {
                'success': True,
                'days': days,
                'message': 'Not enough history yet to compute a learning curve.',
                'daily': []
            }

        daily: Dict[str, Dict[str, object]] = defaultdict(lambda: {
            'count': 0,
            'success_count': 0,
            'confidence_sum': 0.0,
            'latency_total': 0.0,
            'latency_count': 0
        })

        for entry in entries:
            ts = self._parse_iso(entry.get('timestamp'))
            if not ts:
                continue
            key = ts.strftime('%Y-%m-%d')
            row = daily[key]
            row['count'] += 1
            row['success_count'] += 1 if entry.get('success') else 0
            row['confidence_sum'] += float(entry.get('confidence', 0.0) or 0.0)
            if isinstance(entry.get('latency_ms'), (int, float)):
                row['latency_total'] += float(entry.get('latency_ms'))
                row['latency_count'] += 1

        series = []
        for day in sorted(daily.keys()):
            row = daily[day]
            count = max(1, int(row['count']))
            series.append({
                'day': day,
                'count': row['count'],
                'success_rate': round((row['success_count'] / count) * 100, 1),
                'avg_confidence': round(row['confidence_sum'] / count, 3),
                'avg_latency_ms': round(row['latency_total'] / row['latency_count'], 1) if row['latency_count'] else None
            })

        midpoint = max(1, len(series) // 2)
        early = series[:midpoint]
        late = series[midpoint:]
        early_rate = sum(x['success_rate'] for x in early) / len(early)
        late_rate = sum(x['success_rate'] for x in late) / len(late)
        trend = 'improving' if late_rate > early_rate + 1 else 'stable' if abs(late_rate - early_rate) <= 1 else 'declining'

        return {
            'success': True,
            'days': days,
            'trend': trend,
            'early_success_rate': round(early_rate, 1),
            'late_success_rate': round(late_rate, 1),
            'daily': series
        }

    def performance_peaks(self, min_samples: int = 2) -> Dict[str, object]:
        buckets: Dict[int, Dict[str, float]] = defaultdict(lambda: {
            'count': 0,
            'success': 0,
            'cpu_sum': 0.0,
            'memory_sum': 0.0,
            'latency_sum': 0.0,
            'latency_count': 0
        })

        for entry in self.data.get('entries', []):
            ts = self._parse_iso(entry.get('timestamp'))
            if not ts:
                continue
            hour = ts.hour
            row = buckets[hour]
            row['count'] += 1
            row['success'] += 1 if entry.get('success') else 0

            metrics = entry.get('metrics', {}) or {}
            cpu = metrics.get('cpu_percent')
            mem = metrics.get('memory_percent')
            if isinstance(cpu, (int, float)):
                row['cpu_sum'] += float(cpu)
            if isinstance(mem, (int, float)):
                row['memory_sum'] += float(mem)

            if isinstance(entry.get('latency_ms'), (int, float)):
                row['latency_sum'] += float(entry.get('latency_ms'))
                row['latency_count'] += 1

        scored = []
        for hour, row in buckets.items():
            if row['count'] < min_samples:
                continue
            success_rate = (row['success'] / row['count']) * 100
            avg_cpu = row['cpu_sum'] / row['count'] if row['cpu_sum'] else None
            avg_mem = row['memory_sum'] / row['count'] if row['memory_sum'] else None
            avg_latency = row['latency_sum'] / row['latency_count'] if row['latency_count'] else None

            score = success_rate
            if isinstance(avg_cpu, (int, float)):
                score -= avg_cpu * 0.3
            if isinstance(avg_mem, (int, float)):
                score -= avg_mem * 0.2
            if isinstance(avg_latency, (int, float)):
                score -= min(avg_latency / 50.0, 20.0)

            scored.append({
                'hour': hour,
                'samples': int(row['count']),
                'success_rate': round(success_rate, 1),
                'avg_cpu': round(avg_cpu, 1) if isinstance(avg_cpu, (int, float)) else None,
                'avg_memory': round(avg_mem, 1) if isinstance(avg_mem, (int, float)) else None,
                'avg_latency_ms': round(avg_latency, 1) if isinstance(avg_latency, (int, float)) else None,
                'score': round(score, 2)
            })

        scored.sort(key=lambda x: x['score'], reverse=True)
        return {
            'success': True,
            'best_hours': scored[:3],
            'worst_hours': list(reversed(scored[-2:])) if scored else [],
            'analyzed_hours': len(scored)
        }

    def optimization_advice(self) -> Dict[str, object]:
        current = self._capture_system_metrics()
        peaks = self.performance_peaks(min_samples=2)

        entries = self.data.get('entries', [])
        failures = [e for e in entries if not e.get('success')]
        failed_intents: Dict[str, int] = {}
        for item in failures:
            intent = str(item.get('intent', 'unknown'))
            failed_intents[intent] = failed_intents.get(intent, 0) + 1
        top_failures = sorted(failed_intents.items(), key=lambda x: x[1], reverse=True)[:3]

        advice = []
        cpu = current.get('cpu_percent')
        memory = current.get('memory_percent')
        if isinstance(cpu, (int, float)) and cpu >= 85:
            advice.append('CPU is high right now. Close heavy apps before running intensive commands.')
        if isinstance(memory, (int, float)) and memory >= 85:
            advice.append('Memory pressure is high. Restart memory-heavy apps or increase page file.')

        best_hours = peaks.get('best_hours', [])
        if best_hours:
            labels = ', '.join([f"{int(x['hour']):02d}:00" for x in best_hours[:2]])
            advice.append(f"Best observed execution window: {labels} based on your workflow history.")

        if top_failures:
            fail_str = ', '.join([f"{name}({count})" for name, count in top_failures])
            advice.append(f"Most common failed intents: {fail_str}. Consider tightening phrasing or aliases.")

        if not advice:
            advice.append('No major bottlenecks detected. Current workflow performance looks healthy.')

        return {
            'success': True,
            'current_metrics': current,
            'best_hours': best_hours,
            'top_failures': top_failures,
            'advice': advice
        }

    def export_package(self, output_path: Optional[str] = None) -> Dict[str, object]:
        output = output_path.strip() if output_path else ''
        if not output:
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output = f'exports/workflow_package_{stamp}.json'

        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        package = {
            'schema': 'jarvis.workflow.package.v1',
            'exported_at': datetime.now().isoformat(timespec='seconds'),
            'status': self.status(),
            'entries': self.data.get('entries', []),
            'preferences': self.get_preferences(),
            'planner': self.config.get('planner', {}),
            'automations': self.config.get('automations', {}),
            'voice': {
                'wake_word': self.config.get('voice.wake_word', 'jarvis'),
                'wake_word_aliases': self.config.get('voice.wake_word_aliases', []),
                'wake_word_min_similarity': self.config.get('voice.wake_word_min_similarity', 0.86)
            }
        }

        with open(out_path, 'w', encoding='utf-8') as handle:
            json.dump(package, handle, indent=2)

        return {
            'success': True,
            'message': 'Workflow package exported',
            'path': str(out_path),
            'entries': len(self.data.get('entries', []))
        }

    def get_preferences(self) -> Dict[str, object]:
        prefs = self.data.get('preferences', {})
        if not isinstance(prefs, dict):
            prefs = {}
        return {
            'anti_repeat': bool(prefs.get('anti_repeat', True)),
            'markdown_instructions': bool(prefs.get('markdown_instructions', True)),
            'instruction_style': str(prefs.get('instruction_style', 'numbered')),
            'verbosity': str(prefs.get('verbosity', 'concise'))
        }

    def update_preferences(self, updates: Dict[str, object]) -> Dict[str, object]:
        prefs = self.get_preferences()
        for key, value in (updates or {}).items():
            prefs[key] = value

        self.data['preferences'] = prefs
        self._save()
        return {
            'success': True,
            'preferences': prefs,
            'message': 'Workflow preferences updated'
        }

    def _load(self) -> None:
        try:
            if not self.memory_file.exists():
                self.memory_file.parent.mkdir(parents=True, exist_ok=True)
                self._save()
                return

            with open(self.memory_file, 'r', encoding='utf-8') as handle:
                self.data = json.load(handle)
            if 'entries' not in self.data or not isinstance(self.data['entries'], list):
                self.data['entries'] = []
            if 'preferences' not in self.data or not isinstance(self.data['preferences'], dict):
                self.data['preferences'] = {
                    'anti_repeat': True,
                    'markdown_instructions': True,
                    'instruction_style': 'numbered',
                    'verbosity': 'concise'
                }
        except Exception:
            self.data = {
                'version': 1,
                'created_at': datetime.now().isoformat(timespec='seconds'),
                'entries': [],
                'preferences': {
                    'anti_repeat': True,
                    'markdown_instructions': True,
                    'instruction_style': 'numbered',
                    'verbosity': 'concise'
                }
            }
            self._save()

    def _save(self) -> None:
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, 'w', encoding='utf-8') as handle:
            json.dump(self.data, handle, indent=2)

    @staticmethod
    def _parse_iso(value: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None

    @staticmethod
    def _capture_system_metrics() -> Dict[str, object]:
        if psutil is None:
            return {}
        try:
            return {
                'cpu_percent': round(psutil.cpu_percent(interval=None), 1),
                'memory_percent': round(psutil.virtual_memory().percent, 1)
            }
        except Exception:
            return {}

