"""LLM service for prompt and YouTube metadata generation.

Provider selection:
  - ``LLM_PROVIDER=openai`` (default) uses ``langchain_openai.ChatOpenAI``
    with model and key from ``OPENAI_MODEL`` / ``OPENAI_API_KEY``.
  - ``LLM_PROVIDER=mock`` (or any value when ``OPENAI_API_KEY`` is empty)
    falls back to deterministic mock responses so the workflow can be
    exercised end-to-end without paying for or configuring a real key.

The mock responses are intentionally simple but professional-sounding so
they don't trip the workflow's "prompt too short" guard.
"""
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.core.config import config
from src.logger import logger


class LLMService:
    """Wraps all LLM calls used by the video workflow."""

    _PROMPT_SYSTEM = (
        "You are a YouTube video production consultant. "
        "Given a video topic, produce a detailed, vivid video generation prompt "
        "of 150–300 words that describes the visual content, tone, style, pacing, "
        "and narration. Keep the content professional and suitable for general "
        "audiences. Return only the prompt text with no extra commentary."
    )

    _IMPROVE_SYSTEM = (
        "You are a YouTube video production consultant. "
        "You will be given the original video topic and the user's feedback on a "
        "previously-generated prompt. Produce an improved 150–300 word video "
        "generation prompt that incorporates the feedback while preserving the "
        "original topic's intent. Keep the content professional and suitable for "
        "general audiences. Return only the prompt text with no extra commentary."
    )

    _TITLE_SYSTEM = (
        "You are a YouTube SEO specialist. "
        "Given a video generation prompt, write one compelling YouTube video title "
        "that is under 70 characters, SEO-optimised, and attention-grabbing. "
        "Keep titles family-friendly and avoid clickbait. "
        "Return only the title text with no extra commentary."
    )

    _DESCRIPTION_SYSTEM = (
        "You are a YouTube content strategist. "
        "Given a video prompt and its title, write a YouTube description of 150–300 words "
        "with relevant keywords and a clear call-to-action. "
        "Keep the tone professional and brand-safe. "
        "Return only the description text with no extra commentary."
    )

    def __init__(self, *, temperature: float = 0.7) -> None:
        provider = (config.get_llm_provider() or "openai").lower()
        api_key = config.get_openai_api_key()
        self._provider = provider

        # Auto-fallback to mock if no API key, even if provider="openai" --
        # this keeps `docker compose up` working for new contributors.
        if provider == "mock" or not api_key:
            if provider == "openai" and not api_key:
                logger.warning(
                    "OPENAI_API_KEY is empty -- LLMService falling back to mock responses",
                )
            self._llm = None
        else:
            self._llm = ChatOpenAI(
                api_key=api_key,
                model=config.get_openai_model(),
                temperature=temperature,
            )

    @property
    def is_mock(self) -> bool:
        return self._llm is None

    # ------------------------------------------------------------------
    # Real LLM call helper
    # ------------------------------------------------------------------

    async def _chat(self, system: str, user: str) -> str:
        assert self._llm is not None  # callers guard with is_mock
        response = await self._llm.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=user)]
        )
        return response.content.strip()

    # ------------------------------------------------------------------
    # Mock fallback responses
    # ------------------------------------------------------------------

    def _mock_video_prompt(self, topic: str) -> str:
        return (
            f"Cinematic exploration of {topic}. Open with a wide establishing shot, "
            f"warm golden-hour lighting, slow drone push-in over textured detail. "
            f"Tone: contemplative, inviting. Narration is calm and measured, layered "
            f"over ambient pads with a subtle low-end pulse. Cut between intimate "
            f"close-ups and sweeping landscapes, holding each beat just long enough "
            f"to let the visuals breathe. Mid-section introduces archival or context "
            f"clips, color-graded toward muted teal and amber to match the opening. "
            f"Pacing slows in the final third for a reflective close — single slow "
            f"track-out shot, narration trails into score. Aspect 16:9, 4K, 24 fps. "
            f"Avoid: rapid jump cuts, harsh transitions, on-screen text overlays."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_video_prompt(self, topic: str) -> str:
        if self.is_mock:
            return self._mock_video_prompt(topic)
        return await self._chat(
            self._PROMPT_SYSTEM, f"Video topic: {topic}",
        )

    async def improve_video_prompt(self, topic: str, user_feedback: str) -> str:
        """Revise a previously-generated prompt using the user's feedback.

        ``user_feedback`` is free-form text describing what should change
        (tone, pacing, content, length, etc.).
        """
        if self.is_mock:
            return (
                f"{self._mock_video_prompt(topic)}\n\n"
                f"[Revised per user feedback: {user_feedback.strip()[:200]}]"
            )
        user_message = (
            f"Original topic: {topic}\n\n"
            f"User feedback on the previous prompt:\n{user_feedback}"
        )
        return await self._chat(self._IMPROVE_SYSTEM, user_message)

    async def generate_youtube_title(self, prompt: str) -> str:
        if self.is_mock:
            return f"A Visual Journey Through {prompt[:40].strip()}…"
        return await self._chat(
            self._TITLE_SYSTEM, f"Video prompt: {prompt}",
        )

    async def generate_youtube_description(self, prompt: str, title: str) -> str:
        if self.is_mock:
            return (
                f"{title}\n\nIn this short, cinematic piece we explore the subject "
                f"with measured pacing and warm visuals. The video aims to give "
                f"viewers a quiet moment to take in the material without distraction. "
                f"If you enjoyed it, please like and subscribe for more — it helps "
                f"the channel reach more people who appreciate this kind of work."
            )
        return await self._chat(
            self._DESCRIPTION_SYSTEM,
            f"Video title: {title}\n\nVideo prompt: {prompt}",
        )
