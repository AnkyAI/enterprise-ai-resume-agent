from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Seniority(StrEnum):
    ENTRY = "Entry-Level"
    MID = "Mid-Level"
    SENIOR = "Senior"
    LEAD = "Lead/Principal"


class Education(StrictModel):
    institution: str = Field(min_length=2, max_length=120)
    degree: str = Field(min_length=2, max_length=120)
    field_of_study: str | None = Field(default=None, max_length=120)
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)


class Experience(StrictModel):
    company: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=120)
    start_date: date
    end_date: date | None = None
    responsibilities: list[str] = Field(min_length=1, max_length=20)
    achievements: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_dates(self) -> "Experience":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class Project(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=5, max_length=1_000)
    technologies: list[str] = Field(default_factory=list, max_length=30)
    url: HttpUrl | None = None


class CandidateProfile(StrictModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$", max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    location: str | None = Field(default=None, max_length=120)
    headline: str | None = Field(default=None, max_length=160)
    skills: list[str] = Field(min_length=1, max_length=100)
    experience: list[Experience] = Field(default_factory=list, max_length=30)
    projects: list[Project] = Field(default_factory=list, max_length=30)
    education: list[Education] = Field(default_factory=list, max_length=20)
    certifications: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("skills")
    @classmethod
    def unique_skills(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))


class ResumeRequest(StrictModel):
    profile: CandidateProfile
    target_role: str = Field(min_length=2, max_length=120)
    job_description: str = Field(min_length=20, max_length=20_000)
    tone: str = Field(default="professional", pattern="^(professional|executive|technical)$")


class ProfileAnalysis(StrictModel):
    candidate_level: Seniority
    primary_domain: str
    years_experience: float = Field(ge=0)
    strengths: list[str]


class ATSAnalysis(StrictModel):
    matched_keywords: list[str]
    missing_keywords: list[str]
    ats_score: int = Field(ge=0, le=100)
    formatting_suggestions: list[str]


class ResumeExperience(StrictModel):
    company: str
    title: str
    period: str
    bullets: list[str]


class ResumeProject(StrictModel):
    name: str
    description: str
    technologies: list[str]


class ResumeContent(StrictModel):
    professional_summary: str
    experience: list[ResumeExperience]
    skills: list[str]
    projects: list[ResumeProject]
    education: list[Education]
    certifications: list[str]


class ReviewResult(StrictModel):
    approved: bool
    quality_score: int = Field(ge=0, le=100)
    checks: dict[str, bool]
    recommendations: list[str]


class PipelineMetadata(StrictModel):
    request_id: str
    pipeline_version: str
    agents_executed: list[str]
    processing_time_ms: float


class ResumeResponse(StrictModel):
    profile_analysis: ProfileAnalysis
    ats_analysis: ATSAnalysis
    resume: ResumeContent
    review: ReviewResult
    metadata: PipelineMetadata


class HealthResponse(StrictModel):
    status: str
    version: str


class ErrorDetail(StrictModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(StrictModel):
    error: ErrorDetail
