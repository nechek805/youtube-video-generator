# Backend static files

Files in this directory are served at `/static/*` by the FastAPI app.

## Mock video sample

To use the mock video provider in static-file mode, drop a small MP4 here
named `sample.mp4` and set `MOCK_VIDEO_MODE=static` in your `.env`.

```bash
# Any small MP4 works; ~1 MB is plenty for development.
cp /path/to/some/clip.mp4 backend/static/sample.mp4
```

With `MOCK_VIDEO_MODE=static` the mock provider will return
`{BASE_URL}/static/sample.mp4` as the project's `video_url`, and the
frontend video player will play that file directly.

The default mode is `placeholder`, which returns a fake CDN URL without
requiring any file on disk.

## Production note

This directory is mounted unauthenticated. Do not place real
user-generated content here — use signed object storage (S3, R2, etc.)
once the project ships beyond MVP.
