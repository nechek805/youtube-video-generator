"""Runway Gen-3 text-to-video provider.

API reference: https://docs.dev.runwayml.com/
Auth header: ``Authorization: Bearer <RUNWAY_API_KEY>``
Required version header: ``X-Runway-Version: 2024-11-06``

Notes:
- The text-to-video endpoint and model id change occasionally as Runway
  ships new models. If you see HTTP 4xx errors, check
  https://docs.dev.runwayml.com/api-reference for the current endpoint.
- ``ratio`` and ``duration`` are model-dependent. The values below are
  safe defaults for ``gen3a_turbo`` at the time of writing.
"""
import httpx

from .http_provider import AsyncHttpProvider


class RunwayProvider(AsyncHttpProvider):
    name = "runway"

    API_BASE = "https://api.dev.runwayml.com/v1"
    API_VERSION = "2024-11-06"
    MODEL = "gen4.5"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Runway-Version": self.API_VERSION,
            "Content-Type": "application/json",
        }

    async def _submit_job(self, client: httpx.AsyncClient, prompt: str) -> str:
        resp = await client.post(
            f"{self.API_BASE}/text_to_video",
            headers=self._headers(),
            json={
                "promptText": prompt[:1000],
                "model": self.MODEL,
                "duration": 5,
                "ratio": "1280:720",
            },
        )
        if resp.is_error:
            raise RuntimeError(f"Runway 400 body: {resp.text}")
        resp.raise_for_status()
        data = resp.json()
        job_id = data.get("id")
        if not job_id:
            raise RuntimeError(f"Runway submit returned no id: {data}")
        return job_id

    async def _poll_job(self, client: httpx.AsyncClient, job_id: str) -> str | None:
        resp = await client.get(
            f"{self.API_BASE}/tasks/{job_id}",
            headers=self._headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        status = (data.get("status") or "").upper()

        if status in ("PENDING", "RUNNING", "THROTTLED"):
            return None

        if status == "SUCCEEDED":
            outputs = data.get("output") or []
            if not outputs:
                raise RuntimeError(f"Runway job {job_id} SUCCEEDED with no output")
            # output is a list of URLs (usually one video).
            return outputs[0]

        # FAILED, CANCELLED, anything else terminal.
        raise RuntimeError(f"Runway job {job_id} ended in status={status!r}: {data}")
