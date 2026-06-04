"""Video provider package.

Public surface re-exported here so callers don't need to know about
internal layout. To add a new provider:

  1. Create ``<name>.py`` with a class subclassing ``VideoProvider``.
  2. Wire it into ``factory.get_video_provider`` based on ``VIDEO_PROVIDER``.
  3. Add its API key getter to ``src/core/config.py``.
"""
from .base import VideoProvider, VideoResult
from .factory import get_video_provider
from .kling import KlingProvider
from .luma import LumaProvider
from .mock import MockVideoProvider
from .pika import PikaProvider
from .runway import RunwayProvider

# Legacy aliases so existing imports keep working during the package split.
VideoGeneratorService = VideoProvider
MockVideoGenerator = MockVideoProvider
get_video_generator = get_video_provider


__all__ = [
    "VideoProvider",
    "VideoResult",
    "MockVideoProvider",
    "RunwayProvider",
    "PikaProvider",
    "LumaProvider",
    "KlingProvider",
    "get_video_provider",
    # legacy aliases
    "VideoGeneratorService",
    "MockVideoGenerator",
    "get_video_generator",
]
