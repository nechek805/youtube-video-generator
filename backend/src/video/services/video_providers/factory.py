from src.core.config import config
from .base import VideoProvider
from .kling import KlingProvider
from .luma import LumaProvider
from .mock import MockVideoProvider
from .pika import PikaProvider
from .runway import RunwayProvider


def get_video_provider() -> VideoProvider:
    """Return the active video provider based on the VIDEO_PROVIDER env var.

    Defaults to ``mock``. Unknown names raise ValueError so misconfiguration
    is loud, not silent.
    """
    name = (config.get_video_provider() or "mock").lower()
    if name == "mock":
        return MockVideoProvider()
    if name == "runway":
        return RunwayProvider(api_key=config.get_runway_api_key())
    if name == "pika":
        return PikaProvider(api_key=config.get_pika_api_key())
    if name == "luma":
        return LumaProvider(api_key=config.get_luma_api_key())
    if name == "kling":
        return KlingProvider(api_key=config.get_kling_api_key())
    raise ValueError(f"Unknown VIDEO_PROVIDER={name!r}")
