from datetime import date

import pytest

from resume_agent.agents.ats_optimizer import ATSOptimizerAgent
from resume_agent.agents.profile_analyzer import ProfileAnalyzerAgent
from resume_agent.models import CandidateProfile, Experience, ResumeRequest, Seniority


@pytest.mark.asyncio
async def test_profile_analyzer_calculates_level():
    profile = CandidateProfile(
        full_name="Taylor Smith",
        email="taylor@example.com",
        skills=["Python"],
        experience=[
            Experience(
                company="Example",
                title="Engineer",
                start_date=date(2020, 1, 1),
                end_date=date(2024, 1, 1),
                responsibilities=["Built systems"],
            )
        ],
    )
    result = await ProfileAnalyzerAgent().run(profile)
    assert result.candidate_level == Seniority.MID
    assert 3.9 <= result.years_experience <= 4.1


@pytest.mark.asyncio
async def test_ats_agent_reports_keyword_gap():
    profile = CandidateProfile(
        full_name="Taylor Smith", email="taylor@example.com", skills=["Python"]
    )
    request = ResumeRequest(
        profile=profile,
        target_role="Data Engineer",
        job_description=(
            "Build reliable data pipelines using Python, SQL, Airflow, and cloud platforms."
        ),
    )
    result = await ATSOptimizerAgent().run(request)
    assert "python" in result.matched_keywords
    assert "sql" in result.missing_keywords
    assert 0 <= result.ats_score <= 100
