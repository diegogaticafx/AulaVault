from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
from .models import SessionData


class MoodleSession:
    def __init__(self, data: SessionData):
        self.data = data
        self.client = httpx.Client(
            base_url=data.base_url,
            cookies={"MoodleSession": data.moodle_session},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/json",
                "Accept": "application/json, text/javascript, */*; q=0.01",
            },
            follow_redirects=True,
            timeout=30.0,
        )

    def verify(self) -> bool:
        try:
            r = self.client.get("/my/courses.php", follow_redirects=True)
            return r.status_code == 200 and "login" not in str(r.url).lower()
        except Exception:
            return False

    def ajax(self, method: str, args: dict | None = None) -> dict | None:
        if args is None:
            args = {}
        payload = [{"index": 0, "methodname": method, "args": args}]
        r = self.client.post(
            f"/lib/ajax/service.php?sesskey={self.data.sesskey}",
            json=payload,
        )
        r.raise_for_status()
        try:
            result = r.json()
        except Exception as e:
            raise Exception(f"JSON parse error: {e}, body={r.text[:500]}")
        if isinstance(result, list) and len(result) > 0:
            entry = result[0]
            if entry.get("error"):
                err_msg = entry.get("exception", {}).get("message", "Unknown API error")
                raise Exception(f"API error: {err_msg}")
            data = entry.get("data")
            if data is None:
                raise Exception(f"API returned null data, full response: {result}")
            if isinstance(data, str):
                import json
                data = json.loads(data)
            return data
        raise Exception(f"Unexpected API response format: {result}")

    def get_response(self, url: str) -> httpx.Response:
        r = self.client.get(url, follow_redirects=True)
        r.raise_for_status()
        return r

    def get_html(self, url: str) -> BeautifulSoup:
        r = self.get_response(url)
        return BeautifulSoup(r.text, "lxml")

    def get_raw(self, url: str) -> httpx.Response:
        return self.get_response(url)

    def abs_url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return urljoin(self.data.base_url, path)

    def close(self):
        self.client.close()
