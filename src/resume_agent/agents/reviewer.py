from dataclasses import dataclass

from resume_agent.agents.base import Agent
from resume_agent.models import ATSAnalysis, ResumeContent, ReviewResult


@dataclass(frozen=True)
class ReviewerInput:
    resume: ResumeContent
    ats: ATSAnalysis


class ReviewerAgent(Agent[ReviewerInput, ReviewResult]):
    name = "reviewer"

    async def run(self, data: ReviewerInput) -> ReviewResult:
        bullets = [bullet for item in data.resume.experience for bullet in item.bullets]
        checks = {
            "summary_present": len(data.resume.professional_summary) >= 80,
            "consistent_punctuation": all(bullet.endswith(".") for bullet in bullets),
            "standard_sections_present": bool(data.resume.skills),
            "ats_alignment": data.ats.ats_score >= 50,
            "professional_length": len(data.resume.professional_summary) <= 500,
        }
        quality = round(sum(checks.values()) / len(checks) * 100)
        recommendations = []
        if not checks["ats_alignment"]:
            recommendations.append("Strengthen truthful alignment with the target job description.")
        if not bullets:
            recommendations.append("Add work experience with quantified achievement bullets.")
        elif not any(any(char.isdigit() for char in bullet) for bullet in bullets):
            recommendations.append("Add metrics to at least two experience bullets.")
        return ReviewResult(
            approved=quality >= 80,
            quality_score=quality,
            checks=checks,
            recommendations=recommendations,
        )
