"""Pika Labs video provider (via fal.ai queue).

Pika Labs doesn't publish a fully open direct API; the most reliable
public path is via fal.ai's queue endpoints. Set ``PIKA_API_KEY`` to
a fal.ai key (https://fal.ai/dashboard/keys).

fal.ai Pika models: https://fal.ai/models?keywords=pika
Queue API guide:   https://docs.fal.ai/queue

If you have direct Pika API access through a partnership, override
``QUEUE_URL`` and ``STATUS_URL`` in a subclass (or just edit this file).
"""
import httpx

from .http_provider import AsyncHttpProvider


class PikaProvider(AsyncHttpProvider):
    name = "pika"

    QUEUE_URL = "https://queue.fal.run/fal-ai/pika/v2/text-to-video"

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
            json={"prompt": prompt},
        )
        resp.raise_for_status()
        data = resp.json()
        # fal.ai queue: returns {"request_id": "...", "status": "IN_QUEUE", ...}
        job_id = data.get("request_id")
        if not job_id:
            raise RuntimeError(f"Pika submit returned no request_id: {data}")
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
            # Fetch the full result payload to get the video URL
            result_url = f"{self.QUEUE_URL}/requests/{job_id}"
            r2 = await client.get(result_url, headers=self._headers())
            r2.raise_for_status()
            payload = r2.json()
            video = payload.get("video") or {}
            url = video.get("url") if isinstance(video, dict) else None
            if not url:
                raise RuntimeError(
                    f"Pika job {job_id} COMPLETED but no video.url in result: {payload}"
                )
            return url

        raise RuntimeError(f"Pika job {job_id} ended in status={status!r}: {data}")
