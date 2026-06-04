"""Kling video provider (via fal.ai queue).

Kling's official API is operated by Kuaishou and historically gated by
region. The portable public path is via fal.ai's queue endpoints. Set
``KLING_API_KEY`` to a fal.ai key (https://fal.ai/dashboard/keys).

fal.ai Kling models: https://fal.ai/models?keywords=kling
Queue API guide:    https://docs.fal.ai/queue

If you have direct access to the Kling API (via Kuaishou or a partner
like PiAPI), override ``QUEUE_URL`` and the auth header here.
"""
import httpx

from .http_provider import AsyncHttpProvider


class KlingProvider(AsyncHttpProvider):
    name = "kling"

    QUEUE_URL = "https://queue.fal.run/fal-ai/kling-video/v1/standard/text-to-video"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _submit_job(self, client: httpx.AsyncClient, prompt: str) -> str:
        resp = await client.post(
            self.QUEUE_URL,
            headers=self._headers(),
            json={"prompt": prompt, "duration": "5", "aspect_ratio": "16:9"},
        )
        resp.raise_for_status()
        data = resp.json()
        job_id = data.get("request_id")
        if not job_id:
            raise RuntimeError(f"Kling submit returned no request_id: {data}")
        return job_id

    async def _poll_job(self, client: httpx.AsyncClient, job_id: str) -> str | None:
        status_url = f"{self.QUEUE_URL}/requests/{job_id}/status"
        resp = await client.get(status_url, headers=self._headers())
        resp.raise_for_status()
        data = resp.json()
        status = (data.get("status") or "").upper()

        if status in ("IN_QUEUE", "IN_PROGRESS"):
            return None

        if status == "COMPLETED":
            result_url = f"{self.QUEUE_URL}/requests/{job_id}"
            r2 = await client.get(result_url, headers=self._headers())
            r2.raise_for_status()
            payload = r2.json()
            video = payload.get("video") or {}
            url = video.get("url") if isinstance(video, dict) else None
            if not url:
                raise RuntimeError(
                    f"Kling job {job_id} COMPLETED but no video.url in result: {payload}"
                )
            return url

        raise RuntimeError(f"Kling job {job_id} ended in status={status!r}: {data}")
