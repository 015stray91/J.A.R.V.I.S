"""
Research manager for Jarvis X
Provides lightweight internet search and result summarization
"""

from typing import Dict, List
from pathlib import Path
from urllib.parse import quote_plus
import requests
from utils.config_manager import get_config
from utils.logger import get_logger

logger = get_logger()
config = get_config()


class ResearchManager:
    """Handles internet search tasks"""

    def __init__(self):
        self.timeout_seconds = 10
        self.offline_only = config.get('advanced.offline_mode', False)
        self.workspace_root = Path(config.get('development.workspace_root', '') or Path.cwd())

    def search_web(self, query: str, limit: int = 5) -> Dict[str, object]:
        """Search DuckDuckGo instant answer endpoint"""
        if self.offline_only:
            return {
                "success": False,
                "message": "Web search is disabled in offline mode"
            }

        if not query or not query.strip():
            return {
                "success": False,
                "message": "No search query provided"
            }

        clean_query = query.strip()
        url = (
            "https://api.duckduckgo.com/?q="
            f"{quote_plus(clean_query)}&format=json&no_html=1&skip_disambig=1"
        )

        try:
            response = requests.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()

            summary = payload.get("AbstractText", "").strip()
            heading = payload.get("Heading", "").strip()
            related = self._flatten_related(payload.get("RelatedTopics", []))

            results: List[Dict[str, str]] = []
            for item in related[:limit]:
                text = item.get("Text", "").strip()
                first_url = item.get("FirstURL", "").strip()
                if text:
                    results.append({
                        "title": text.split(" - ")[0][:120],
                        "snippet": text[:220],
                        "url": first_url
                    })

            if not summary and not results:
                return {
                    "success": True,
                    "query": clean_query,
                    "summary": "No instant answer found.",
                    "results": []
                }

            return {
                "success": True,
                "query": clean_query,
                "heading": heading,
                "summary": summary,
                "results": results
            }

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {
                "success": False,
                "message": f"Search failed: {e}"
            }

    def search_workspace(self, query: str, limit: int = 10) -> Dict[str, object]:
        """Search local workspace files for query matches"""
        if not query or not query.strip():
            return {
                "success": False,
                "message": "No local search query provided"
            }

        if not self.workspace_root.exists():
            return {
                "success": False,
                "message": f"Workspace root does not exist: {self.workspace_root}"
            }

        query_lower = query.strip().lower()
        hits: List[Dict[str, str]] = []

        try:
            for path in self.workspace_root.rglob('*'):
                if len(hits) >= limit:
                    break

                if not path.is_file():
                    continue

                name = path.name.lower()
                if query_lower in name:
                    hits.append({
                        "path": str(path),
                        "match": "filename"
                    })
                    continue

                # Avoid loading very large files for quick local search.
                if path.stat().st_size > 2 * 1024 * 1024:
                    continue

                try:
                    text = path.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    continue

                if query_lower in text.lower():
                    hits.append({
                        "path": str(path),
                        "match": "content"
                    })

            return {
                "success": True,
                "query": query,
                "results": hits,
                "summary": f"Found {len(hits)} local workspace matches"
            }

        except Exception as e:
            logger.error(f"Workspace search failed: {e}")
            return {
                "success": False,
                "message": f"Workspace search failed: {e}"
            }

    def _flatten_related(self, related_topics: List[dict]) -> List[dict]:
        """Flatten nested related topic payload"""
        flat: List[dict] = []

        for item in related_topics:
            if "Topics" in item and isinstance(item["Topics"], list):
                flat.extend(item["Topics"])
            else:
                flat.append(item)

        return flat

