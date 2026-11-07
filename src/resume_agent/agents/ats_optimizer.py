import re
from collections import Counter

from resume_agent.agents.base import Agent
from resume_agent.models import ATSAnalysis, ResumeRequest

STOP_WORDS = {
    "and",
    "the",
    "with",
    "for",
    "that",
    "this",
    "from",
    "your",
    "you",
    "our",
    "are",
    "will",
    "have",
    "has",
    "into",
    "using",
    "work",
    "role",
    "team",
    "years",
    "about",
}


class ATSOptimizerAgent(Agent[ResumeRequest, ATSAnalysis]):
    name = "ats_optimizer"

    async def run(self, request: ResumeRequest) -> ATSAnalysis:
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{1,}", request.job_description.lower())
        keywords = [word for word, _ in Counter(tokens).most_common() if word not in STOP_WORDS][
            :20
        ]
        profile_text = " ".join(
            request.profile.skills
            + [exp.title for exp in request.profile.experience]
            + [project.description for project in request.profile.projects]
        ).lower()
        matched = [word for word in keywords if word in profile_text]
        missing = [word for word in keywords if word not in profile_text][:10]
        score = round((len(matched) / max(1, len(keywords))) * 100)
        score = min(100, score + (10 if request.profile.experience else 0))
        suggestions = [
            "Use standard section headings and reverse-chronological experience.",
            "Quantify outcomes with scope, speed, revenue, cost, or quality metrics.",
        ]
        if missing:
            suggestions.append(
                "Add relevant missing keywords only where supported by genuine experience."
            )
        return ATSAnalysis(
            matched_keywords=matched,
            missing_keywords=missing,
            ats_score=score,
            formatting_suggestions=suggestions,
        )
