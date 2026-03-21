"""
Repository intelligence manager for Jarvis X
Searches inside repository files and extracts requested configuration details
"""

from pathlib import Path
from typing import Dict, List


class RepoIntelManager:
    """Finds and returns relevant lines from repository files"""

    def __init__(self, root: str = "."):
        self.root = Path(root).resolve()

    def search(self, query: str, limit: int = 20) -> Dict[str, object]:
        if not query or not query.strip():
            return {
                "success": False,
                "message": "No repository query provided"
            }

        query_l = query.lower().strip()
        hits: List[Dict[str, object]] = []

        try:
            for path in self.root.rglob("*"):
                if len(hits) >= limit:
                    break

                if not path.is_file():
                    continue

                if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".exe", ".dll", ".bin"}:
                    continue

                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                lines = text.splitlines()
                for idx, line in enumerate(lines, start=1):
                    if query_l in line.lower():
                        hits.append({
                            "path": str(path),
                            "line": idx,
                            "text": line.strip()
                        })
                        if len(hits) >= limit:
                            break

            return {
                "success": True,
                "query": query,
                "count": len(hits),
                "results": hits,
                "message": f"Found {len(hits)} matches in repository"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Repository search failed: {e}"
            }

