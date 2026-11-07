from abc import ABC, abstractmethod

from resume_agent.models import ATSAnalysis, ProfileAnalysis, ResumeContent, ResumeRequest


class ResumeGenerationProvider(ABC):
    """Boundary for an external or local generative model."""

    name: str

    @abstractmethod
    async def generate(
        self,
        request: ResumeRequest,
        profile: ProfileAnalysis,
        ats: ATSAnalysis,
    ) -> ResumeContent:
        """Generate resume content conforming to the public response schema."""
