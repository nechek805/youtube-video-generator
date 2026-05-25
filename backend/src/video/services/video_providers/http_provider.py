"""Shared HTTP-polling skeleton for real video providers.

Real providers (Runway, Luma, Pika, Kling) all follow the same pattern:

  1. POST a job; receive a job id.
  2. Poll a status endpoint until the job is done or failed.
  3. Read the resulting video URL out of the success response.

This base class encapsulates that loop so each concrete provider only
implements two small async hooks: ``_submit_job`` and ``_poll_job``. The
loop runs **inside** the FastAPI request that triggered video generation
-- the workflow node already does ``await video_gen.generate(...)``, and
because everything is async, only this single request blocks; the rest
of the API stays responsive.

For very long jobs, you can keep the request short by returning
``VideoResult(is_complete=False, provider_job_id=...)`` from
``generate`` and adding a Celery task that polls and updates the DB.
That pattern is supported by the workflow but not used in these
in-request implementations.
"""
import asyncio

import httpx

from src.logger import logger
from .base import VideoProvider, VideoResult


class AsyncHttpProvider(VideoProvider):
    """Generic poll-until-done HTTP provider.

    Subclasses set ``name`` and (optionally) override the timing
    constants, then implement ``_submit_job`` and ``_poll_job``.
    """

    #: Seconds between polls.
    poll_interval_s: float = 5.0
    #: Hard ceiling. After this, ``generate`` raises TimeoutError.
    poll_timeout_s: float = 600.0  # 10 minutes
    #: Per-HTTP-call timeout.
    request_timeout_s: float = 60.0

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    # ------------------------------------------------------------------
    # Hooks for subclasses
    # ------------------------------------------------------------------

    async def _submit_job(
        self, client: httpx.AsyncClient, prompt: str
    ) -> str:
        """POST the job. Return the provider's job id."""
        raise NotImplementedError

    async def _poll_job(
        self, client: httpx.AsyncClient, job_id: str
    ) -> str | None:
        """Check the job's status.

        Returns:
          - the video URL (str) if the job has completed successfully,
          - ``None`` if the job is still queued / running,
          - raises an exception to abort polling on terminal failure.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def generate(
        self,
        *,
        prompt: str,
        project_id: int,
        step_id: int,
    ) -> VideoResult:
        if not self.api_key:
            raise RuntimeError(
                f"{self.name} provider requires an API key "
                f"({self.name.upper()}_API_KEY env var)."
            )

        async with httpx.AsyncClient(timeout=self.request_timeout_s) as client:
            job_id = await self._submit_job(client, prompt)
            logger.info(
                "Video job submitted (provider=%s, project=%d, step=%d, job=%s)",
                self.name, project_id, step_id, job_id,
            )
            max_polls = max(1, int(self.poll_timeout_s / self.poll_interval_s))
            for attempt in range(max_polls):
                await asyncio.sleep(self.poll_interval_s)
                try:
                    url = await self._poll_job(client, job_id)
                except Exception:
                    # Re-raise so the workflow node can mark FAILED and
                    # log the traceback; don't swallow.
                    raise
                if url:
                    logger.info(
                        "Video job complete (provider=%s, job=%s, polls=%d)",
                        self.name, job_id, attempt + 1,
                    )
                    return VideoResult(
                        video_url=url,
                        provider=self.name,
                        provider_job_id=job_id,
                        is_complete=True,
                    )
            raise TimeoutError(
                f"{self.name} job {job_id} did not complete within "
                f"{self.poll_timeout_s:.0f}s"
            )

    async def check_status(self, provider_job_id: str) -> VideoResult:
        """One-shot status check (no polling). Useful for background workers."""
        async with httpx.AsyncClient(timeout=self.request_timeout_s) as client:
            url = await self._poll_job(client, provider_job_id)
        return VideoResult(
            video_url=url,
            provider=self.name,
            provider_job_id=provider_job_id,
            is_complete=url is not None,
        )
