from typing import Literal

from pydantic import BaseModel, Field


class CopilotMessage(BaseModel):
    """A short, previous turn supplied by the browser for conversational context."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4_000)


class CopilotRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    conversation: list[CopilotMessage] = Field(default_factory=list, max_length=8)


class CopilotResponse(BaseModel):
    answer: str
    model: str
    sources: list[str] = Field(default_factory=list)


class CopilotStatus(BaseModel):
    enabled: bool
    ready: bool
    model: str
    detail: str
