"""Pydantic v2 schemas for structured RAG responses."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Confidence(str, Enum):
    high = "high"
    partial = "partial"
    none = "none"


class SourceCitation(BaseModel):
    """A single verified citation shown to the user."""

    label: str = Field(description="Context block label, e.g. S1")
    source: str = Field(description="Source file name")
    location: str = Field(default="", description="Page, section, or row")
    snippet: str = Field(default="", description="Short verbatim excerpt")

    def display(self) -> str:
        loc = f" — {self.location}" if self.location else ""
        return f"{self.source}{loc}"


class GroundedResponse(BaseModel):
    """Schema-validated object returned by the RAG chain."""

    answer: str = Field(description="Customer-facing answer text")
    sources: list[str] = Field(
        default_factory=list,
        description="Labels of context blocks actually used, e.g. ['S1','S3']",
    )
    confidence: Confidence = Field(description="high | partial | none")
    answered: bool = Field(
        description="True if the knowledge base supported an answer"
    )
    flags: list[str] = Field(
        default_factory=list,
        description="Optional flags: refusal, partial, injection_attempt, out_of_scope",
    )

    @field_validator("sources", mode="before")
    @classmethod
    def _coerce_sources(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)


class DisplayResponse(BaseModel):
    """UI-facing response after citation resolution."""

    answer: str
    citations: list[SourceCitation] = Field(default_factory=list)
    confidence: Confidence
    answered: bool
    flags: list[str] = Field(default_factory=list)
    rewritten_query: str = ""
    original_query: str = ""
    refusal: bool = False

    def render(self) -> str:
        lines = [self.answer.strip(), ""]
        if self.citations:
            lines.append("Sources:")
            for i, cite in enumerate(self.citations, start=1):
                lines.append(f"  [{i}] {cite.display()}")
                if cite.snippet:
                    lines.append(f"      \"{cite.snippet[:140]}\"")
        elif self.refusal or not self.answered:
            lines.append("Sources: none (no supporting documentation found)")
        lines.append(f"Confidence: {self.confidence.value}")
        return "\n".join(lines)
