from datetime import date

from resume_agent.agents.base import Agent
from resume_agent.models import CandidateProfile, ProfileAnalysis, Seniority


class ProfileAnalyzerAgent(Agent[CandidateProfile, ProfileAnalysis]):
    name = "profile_analyzer"

    async def run(self, profile: CandidateProfile) -> ProfileAnalysis:
        today = date.today()
        total_days = sum(
            ((item.end_date or today) - item.start_date).days for item in profile.experience
        )
        years = round(max(0, total_days) / 365.25, 1)
        if years < 2:
            level = Seniority.ENTRY
        elif years < 5:
            level = Seniority.MID
        elif years < 9:
            level = Seniority.SENIOR
        else:
            level = Seniority.LEAD

        domain = profile.headline or (
            profile.experience[0].title if profile.experience else "General"
        )
        strengths = profile.skills[:5]
        if profile.certifications:
            strengths.append(f"{len(profile.certifications)} professional certification(s)")
        if profile.projects:
            strengths.append(f"{len(profile.projects)} portfolio project(s)")
        return ProfileAnalysis(
            candidate_level=level,
            primary_domain=domain,
            years_experience=years,
            strengths=strengths,
        )
