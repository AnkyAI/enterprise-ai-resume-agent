import re
from dataclasses import dataclass

from resume_agent.agents.base import Agent
from resume_agent.models import (
    ATSAnalysis,
    ProfileAnalysis,
    ResumeContent,
    ResumeExperience,
    ResumeProject,
    ResumeRequest,
)


@dataclass(frozen=True)
class WriterInput:
    request: ResumeRequest
    profile: ProfileAnalysis
    ats: ATSAnalysis


def _polish_bullet(text: str) -> str:
    clean = re.sub(r"\s+", " ", text).strip().rstrip(".")
    if not clean:
        return clean
    weak = ("responsible for ", "worked on ", "helped ")
    for prefix in weak:
        if clean.lower().startswith(prefix):
            clean = clean[len(prefix) :]
            break
    return clean[0].upper() + clean[1:] + "."


class ResumeWriterAgent(Agent[WriterInput, ResumeContent]):
    name = "resume_writer"

    async def run(self, data: WriterInput) -> ResumeContent:
        request, profile, ats = data.request, data.profile, data.ats
        core_skills = profile.strengths[:3]
        summary = (
            f"{profile.candidate_level} {profile.primary_domain} professional with "
            f"{profile.years_experience:g} years of experience, targeting "
            f"{request.target_role} roles. Brings strengths in "
            f"{', '.join(core_skills) if core_skills else 'cross-functional delivery'} "
            "and a record of translating business needs into measurable outcomes."
        )
        experience = []
        for item in request.profile.experience:
            bullets = [_polish_bullet(x) for x in item.achievements + item.responsibilities]
            experience.append(
                ResumeExperience(
                    company=item.company,
                    title=item.title,
                    period=f"{item.start_date:%b %Y} - "
                    f"{item.end_date.strftime('%b %Y') if item.end_date else 'Present'}",
                    bullets=[bullet for bullet in bullets if bullet][:6],
                )
            )
        projects = [
            ResumeProject(
                name=item.name,
                description=_polish_bullet(item.description),
                technologies=item.technologies,
            )
            for item in request.profile.projects
        ]
        skills = list(dict.fromkeys(request.profile.skills + ats.matched_keywords))
        return ResumeContent(
            professional_summary=summary,
            experience=experience,
            skills=skills,
            projects=projects,
            education=request.profile.education,
            certifications=request.profile.certifications,
        )
