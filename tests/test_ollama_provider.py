import json

import httpx
import pytest

from resume_agent.models import (
    ATSAnalysis,
    CandidateProfile,
    ProfileAnalysis,
    ResumeRequest,
    Seniority,
)
from resume_agent.providers.ollama import OllamaProvider


def _context() -> tuple[ResumeRequest, ProfileAnalysis, ATSAnalysis]:
    request = ResumeRequest(
        profile=CandidateProfile(
            full_name="Jordan Lee",
            email="jordan@example.com",
            skills=["Python", "SQL"],
        ),
        target_role="Data Analyst",
        job_description="Seeking a data analyst with Python and SQL reporting experience.",
    )
    profile = ProfileAnalysis(
        candidate_level=Seniority.ENTRY,
        primary_domain="Data Analytics",
        years_experience=1,
        strengths=["Python", "SQL"],
    )
    ats = ATSAnalysis(
        matched_keywords=["python", "sql"],
        missing_keywords=[],
        ats_score=90,
        formatting_suggestions=[],
    )
    return request, profile, ats


@pytest.mark.asyncio
async def test_ollama_provider_uses_schema_and_validates_response():
    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert request.url.path == "/api/chat"
        assert payload["stream"] is False
        assert payload["format"]["title"] == "ResumeContent"
        assert "Never invent" in payload["messages"][1]["content"]
        content = {
            "professional_summary": "Data analyst with Python and SQL reporting experience.",
            "experience": [],
            "skills": ["Python", "SQL"],
            "projects": [],
            "education": [],
            "certifications": [],
        }
        return httpx.Response(200, json={"message": {"content": json.dumps(content)}})

    provider = OllamaProvider(
        "http://ollama.test", "llama3.2:3b", transport=httpx.MockTransport(handler)
    )
    result = await provider.generate(*_context())
    assert result.skills == ["Python", "SQL"]


@pytest.mark.asyncio
async def test_ollama_provider_rejects_invalid_model_output():
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": "not json"}})

    provider = OllamaProvider(
        "http://ollama.test", "llama3.2:3b", transport=httpx.MockTransport(handler)
    )
    with pytest.raises(ValueError):
        await provider.generate(*_context())
