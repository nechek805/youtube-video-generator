from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.core.config import config


class LLMService:
    """Wraps all LLM calls used by the video workflow.

    All prompts and model parameters live here. Swap the underlying provider by
    replacing the constructor body (e.g. ChatAnthropic) without touching the
    workflow graph.
    """

    _PROMPT_SYSTEM = (
        "You are a YouTube video production consultant. "
        "Given a video topic, produce a detailed, vivid video generation prompt "
        "of 150–300 words that describes the visual content, tone, style, pacing, "
        "and narration. Return only the prompt text with no extra commentary."
    )

    _TITLE_SYSTEM = (
        "You are a YouTube SEO specialist. "
        "Given a video generation prompt, write one compelling YouTube video title "
        "that is under 70 characters, SEO-optimised, and attention-grabbing. "
        "Return only the title text with no extra commentary."
    )

    _DESCRIPTION_SYSTEM = (
        "You are a YouTube content strategist. "
        "Given a video prompt and its title, write a YouTube description of 150–300 words "
        "with relevant keywords and a clear call-to-action. "
        "Return only the description text with no extra commentary."
    )

    def __init__(self, *, temperature: float = 0.7) -> None:
        self._llm = ChatOpenAI(
            api_key=config.get_openai_api_key(),
            model=config.get_openai_model(),
            temperature=temperature,
        )

    async def generate_video_prompt(self, topic: str) -> str:
        messages = [
            SystemMessage(content=self._PROMPT_SYSTEM),
            HumanMessage(content=f"Video topic: {topic}"),
        ]
        response = await self._llm.ainvoke(messages)
        return response.content.strip()

    async def generate_youtube_title(self, prompt: str) -> str:
        messages = [
            SystemMessage(content=self._TITLE_SYSTEM),
            HumanMessage(content=f"Video prompt: {prompt}"),
        ]
        response = await self._llm.ainvoke(messages)
        return response.content.strip()

    async def generate_youtube_description(self, prompt: str, title: str) -> str:
        messages = [
            SystemMessage(content=self._DESCRIPTION_SYSTEM),
            HumanMessage(content=f"Video title: {title}\n\nVideo prompt: {prompt}"),
        ]
        response = await self._llm.ainvoke(messages)
        return response.content.strip()
