from __future__ import annotations
import os, json, urllib.parse, urllib.request

class DotTalkClient:
    """Stub for a future FastAPI-based DotTalk++ backend.

    Expected endpoints (can be adjusted later to match your service):

      GET  /status                                -> {"ok": true}
      GET  /xbase/header?table=students           -> {"version":3,"last_updated":"20250824","num_of_recs":123,"cpr":128}
      GET  /xbase/schema                          -> { "tables": {...} }
      GET  /xbase/fixtures                        -> { "teachers":[...], "students":[...], ... }

    """
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("DOT_TALK_URL", "").strip().rstrip("/")

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def _get_json(self, path: str, params: dict | None = None) -> dict | None:
        if not self.is_configured():
            return None
        try:
            url = self.base_url + path
            if params:
                url += "?" + urllib.parse.urlencode(params)
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status != 200:
                    return None
                data = r.read()
                return json.loads(data.decode("utf-8"))
        except Exception:
            return None

    def status(self) -> str:
        res = self._get_json("/status")
        if res is None:
            return "not-configured" if not self.is_configured() else "unreachable"
        return "ok" if res.get("ok") else "unknown"

    # ---------- XBase helpers ----------
    def get_header(self, table: str) -> dict | None:
        return self._get_json("/xbase/header", {"table": table})

    def get_schema(self) -> dict | None:
        return self._get_json("/xbase/schema")

    def get_fixtures(self) -> dict | None:
        return self._get_json("/xbase/fixtures")
