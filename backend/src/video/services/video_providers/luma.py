"""Luma Dream Machine text-to-video provider.

API reference: https://docs.lumalabs.ai/docs/api
Auth header: ``Authorization: Bearer <LUMA_API_KEY>``

Notes:
- Job lifecycle: queued -> dreaming -> completed | failed.
- On completion the video URL is at ``assets.video``.
- ``aspect_ratio`` accepts a few preset strings; ``16:9`` is the default
  here. Other supported values: ``9:16``, ``1:1``, ``4:3``, ``3:4``,
  ``21:9``, ``9:21``.
"""
import httpx

from .http_provider import AsyncHttpProvider


class LumaProvider(AsyncHttpProvider):
    name = "luma"

    API_BASE = "https://api.lumalabs.ai/dream-machine/v1"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _submit_job(self, client: httpx.AsyncClient, prompt: str) -> str:
        resp = await client.post(
            f"{self.API_BASE}/generations",
            headers=self._headers(),
            json={"prompt": prompt, "aspect_ratio": "16:9"},
        )
        resp.raise_for_status()
        data = resp.json()
        job_id = data.get("id")
        if not job_id:
            raise RuntimeError(f"Luma submit returned no id: {data}")
        return job_id

    async def _poll_job(self, client: httpx.AsyncClient, job_id: str) -> str | None:
        resp = await client.get(
            f"{self.API_BASE}/generations/{job_id}",
            headers=self._headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        state = (data.get("state") or "").lower()

        if state in ("queued", "dreaming", "processing"):
            return None

        if state == "completed":
            url = (data.get("assets") or {}).get("video")
            if not url:
                raise RuntimeError(
                    f"Luma job {job_id} completed with no assets.video: {data}"
                )
            return url

        # failed / cancelled / etc.
        reason = data.get("failure_reason") or data
        raise RuntimeError(f"Luma job {job_id} ended in state={state!r}: {reason}")
