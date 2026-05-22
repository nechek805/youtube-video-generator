"""Backwards-compat shim.

The implementation moved to ``src.video.services.video_providers``.
This module re-exports the same public names so existing imports
(``from src.video.services.video_generator import ...``) keep working
during the migration. Remove once all callers are updated.
"""
from .video_providers import (  # noqa: F401
    MockVideoGenerator,
    MockVideoProvider,
    VideoGeneratorService,
    VideoProvider,
    VideoResult,
    get_video_generator,
)
