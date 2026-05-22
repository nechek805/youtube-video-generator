"""Video provider package.

Public surface re-exported here so callers don't need to know about
internal layout. To add a new provider:

  1. Create ``<name>.py`` with a class subclassing ``VideoProvider``.
  2. Wire it into ``factory.get_video_provider`` based on ``VIDEO_PROVIDER``.
  3. Add its API key getter to ``src/core/config.py``.
"""
from .base import VideoProvider, VideoResult
from .mock import MockVideoProvider

# Legacy aliases so existing imports keep working during the package split.
VideoGeneratorService = VideoProvider
MockVideoGenerator = MockVideoProvider


def get_video_generator() -> VideoProvider:
    """Legacy factory name; returns the mock provider directly.

    The env-var-driven factory lands in commit 3 and replaces this with
    ``get_video_provider``. Keeping this here so workflow.py and service.py
    can be updated in a later commit.
    """
    return MockVideoProvider()


__all__ = [
    "VideoProvider",
    "VideoResult",
    "MockVideoProvider",
    # legacy aliases
    "VideoGeneratorService",
    "MockVideoGenerator",
    "get_video_generator",
]
