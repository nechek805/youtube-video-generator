"""YouTube account management and video upload service."""
import asyncio
import os
import tempfile
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.logger import logger
from src.youtube.exceptions import (
    YouTubeAccountNotFound,
    YouTubeOAuthError,
    YouTubeUploadError,
)
from src.youtube.models import YouTubeAccount
from src.youtube.oauth import (
    exchange_code,
    fetch_channel_info,
    refresh_access_token,
    token_expiry_from_response,
)
from src.youtube.repository import YouTubeAccountRepository
from src.youtube.schemas import YouTubePublishResult

_YOUTUBE_UPLOAD_URL = (
    "https://www.googleapis.com/upload/youtube/v3/videos"
    "?uploadType=resumable&part=snippet,status"
)


class YouTubeService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = YouTubeAccountRepository(db)

    # ------------------------------------------------------------------
    # OAuth connect / disconnect
    # ------------------------------------------------------------------

    async def connect(self, user_id: int, code: str) -> YouTubeAccount:
        """Exchange OAuth code, fetch channel info, persist tokens."""
        try:
            token_data = await exchange_code(code)
        except RuntimeError as exc:
            raise YouTubeOAuthError(str(exc)) from exc

        access_token = token_data.get("access_token", "")
        refresh_token = token_data.get("refresh_token", "")
        if not refresh_token:
            raise YouTubeOAuthError(
                "Google did not return a refresh_token. "
                "Revoke app access in your Google Account and try again."
            )

        expiry = token_expiry_from_response(token_data)
        channel = await fetch_channel_info(access_token)

        account = await self.repo.upsert(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expiry,
            **channel,
        )
        logger.info(
            "YouTube account connected (user=%d, channel=%s)",
            user_id,
            channel.get("channel_name"),
        )
        return account

    async def disconnect(self, user_id: int) -> None:
        deleted = await self.repo.delete(user_id)
        if not deleted:
            raise YouTubeAccountNotFound()

    async def get_account(self, user_id: int) -> YouTubeAccount:
        account = await self.repo.get_by_user_id(user_id)
        if account is None:
            raise YouTubeAccountNotFound()
        return account

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    async def _get_valid_token(self, user_id: int) -> str:
        """Return a fresh access_token, refreshing if expired."""
        account = await self.get_account(user_id)

        # Refresh 60 s before actual expiry to avoid races.
        needs_refresh = datetime.now(timezone.utc).timestamp() >= (
            account.token_expiry.timestamp() - 60
        )
        if not needs_refresh:
            return account.access_token

        logger.info("Refreshing YouTube access token for user %d", user_id)
        try:
            new_token, new_expiry = await refresh_access_token(account.refresh_token)
        except RuntimeError as exc:
            raise YouTubeOAuthError(str(exc)) from exc

        await self.repo.upsert(
            user_id=user_id,
            access_token=new_token,
            refresh_token=account.refresh_token,
            token_expiry=new_expiry,
            channel_id=account.channel_id,
            channel_name=account.channel_name,
            channel_thumbnail=account.channel_thumbnail,
        )
        return new_token

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    async def _fetch_and_concat(self, video_urls: list[str]) -> bytes:
        """Download one or more video URLs and return a single MP4 byte string.

        If only one URL is given the bytes are returned as-is.  For multiple
        URLs the clips are concatenated (in order) using ffmpeg's demuxer
        concat so the result is a valid MP4.
        """
        if len(video_urls) == 1:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.get(video_urls[0])
            if resp.is_error:
                raise YouTubeUploadError(
                    f"Failed to download video: {resp.status_code}"
                )
            return resp.content

        # Download all parts concurrently.
        async def _dl(url: str) -> bytes:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.get(url)
            if resp.is_error:
                raise YouTubeUploadError(
                    f"Failed to download video part ({url}): {resp.status_code}"
                )
            return resp.content

        parts_bytes = await asyncio.gather(*[_dl(u) for u in video_urls])

        # Write parts to temp files and concat with ffmpeg.
        with tempfile.TemporaryDirectory() as tmpdir:
            input_paths: list[str] = []
            for i, data in enumerate(parts_bytes):
                path = os.path.join(tmpdir, f"part_{i}.mp4")
                with open(path, "wb") as fh:
                    fh.write(data)
                input_paths.append(path)

            concat_list = os.path.join(tmpdir, "concat.txt")
            with open(concat_list, "w") as fh:
                for path in input_paths:
                    fh.write(f"file '{path}'\n")

            output_path = os.path.join(tmpdir, "output.mp4")
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list,
                "-c", "copy",
                output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise YouTubeUploadError(
                    f"ffmpeg concat failed: {stderr.decode(errors='replace')}"
                )

            with open(output_path, "rb") as fh:
                return fh.read()

    async def upload_video(
        self,
        *,
        user_id: int,
        video_urls: list[str],
        title: str,
        description: str,
        tags: list[str] | None = None,
        privacy: str = "public",
    ) -> YouTubePublishResult:
        """Download (and optionally concatenate) videos, then upload to YouTube.

        ``video_urls`` should contain one URL per approved video part in order.
        Multiple parts are concatenated via ffmpeg before uploading.
        Uses the resumable upload protocol so large files are handled correctly.
        Returns the published video id and URL.
        """
        access_token = await self._get_valid_token(user_id)

        # 1. Download / concat video bytes.
        logger.info(
            "Downloading %d video part(s) for upload (project user=%d)",
            len(video_urls),
            user_id,
        )
        video_bytes = await self._fetch_and_concat(video_urls)

        # 2. Initiate a resumable upload session.
        metadata = {
            "snippet": {
                "title": title[:100],          # YouTube max 100 chars
                "description": description[:5000],
                "tags": tags or [],
                "categoryId": "22",            # People & Blogs
            },
            "status": {
                "privacyStatus": privacy,
            },
        }

        async with httpx.AsyncClient(timeout=30) as client:
            init_resp = await client.post(
                _YOUTUBE_UPLOAD_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json; charset=UTF-8",
                    "X-Upload-Content-Type": "video/mp4",
                    "X-Upload-Content-Length": str(len(video_bytes)),
                },
                json=metadata,
            )

        if init_resp.is_error:
            raise YouTubeUploadError(
                f"Failed to initiate YouTube upload: {init_resp.text}"
            )

        upload_url = init_resp.headers.get("Location")
        if not upload_url:
            raise YouTubeUploadError("YouTube did not return an upload Location URL")

        # 3. Upload the video bytes.
        logger.info(
            "Uploading %d bytes to YouTube (user=%d)", len(video_bytes), user_id
        )
        async with httpx.AsyncClient(timeout=300) as client:
            upload_resp = await client.put(
                upload_url,
                content=video_bytes,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(len(video_bytes)),
                },
            )

        if upload_resp.is_error:
            raise YouTubeUploadError(
                f"YouTube video upload failed: {upload_resp.text}"
            )

        data = upload_resp.json()
        video_id = data.get("id")
        if not video_id:
            raise YouTubeUploadError(f"YouTube did not return a video id: {data}")

        yt_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info("YouTube upload complete: %s (user=%d)", yt_url, user_id)

        return YouTubePublishResult(
            youtube_video_id=video_id,
            youtube_url=yt_url,
            title=title,
        )
