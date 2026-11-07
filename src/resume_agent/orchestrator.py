import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

import structlog

from resume_agent.agents import (
    ATSOptimizerAgent,
    ProfileAnalyzerAgent,
    ResumeWriterAgent,
    ReviewerAgent,
)
from resume_agent.agents.resume_writer import WriterInput
from resume_agent.agents.reviewer import ReviewerInput
from resume_agent.metrics import AGENT_RUNS, PIPELINE_LATENCY
from resume_agent.models import PipelineMetadata, ResumeRequest, ResumeResponse
from resume_agent.providers.base import ResumeGenerationProvider

logger = structlog.get_logger()


class ResumeOrchestrator:
    """Runs the typed agent workflow and owns cross-agent error handling."""

    pipeline_version = "1.0.0"

    def __init__(
        self,
        provider: ResumeGenerationProvider | None = None,
        allow_fallback: bool = True,
    ) -> None:
        self.profile_agent = ProfileAnalyzerAgent()
        self.ats_agent = ATSOptimizerAgent()
        self.writer_agent = ResumeWriterAgent()
        self.reviewer_agent = ReviewerAgent()
        self.provider = provider
        self.allow_fallback = allow_fallback

    async def _run_agent(self, name: str, operation: Callable[[], Awaitable[object]]) -> object:
        started = time.perf_counter()
        try:
            result = await operation()
            AGENT_RUNS.labels(agent=name, status="success").inc()
            await logger.ainfo(
                "agent_completed", agent=name, duration_ms=(time.perf_counter() - started) * 1000
            )
            return result
        except Exception:
            AGENT_RUNS.labels(agent=name, status="error").inc()
            await logger.aexception("agent_failed", agent=name)
            raise

    async def generate(
        self, request: ResumeRequest, request_id: str | None = None
    ) -> ResumeResponse:
        started = time.perf_counter()
        request_id = request_id or str(uuid4())
        profile = await self._run_agent(
            self.profile_agent.name, lambda: self.profile_agent.run(request.profile)
        )
        ats = await self._run_agent(self.ats_agent.name, lambda: self.ats_agent.run(request))
        fallback_used = False
        provider_name = self.provider.name if self.provider else "deterministic"
        if self.provider:
            active_provider = self.provider
            try:
                resume = await self._run_agent(
                    self.writer_agent.name,
                    lambda: active_provider.generate(request, profile, ats),  # type: ignore[arg-type]
                )
            except Exception:
                if not self.allow_fallback:
                    raise
                fallback_used = True
                provider_name = "deterministic"
                await logger.awarning(
                    "provider_fallback",
                    requested_provider=active_provider.name,
                    request_id=request_id,
                )
                resume = await self._run_agent(
                    self.writer_agent.name,
                    lambda: self.writer_agent.run(WriterInput(request, profile, ats)),  # type: ignore[arg-type]
                )
        else:
            resume = await self._run_agent(
                self.writer_agent.name,
                lambda: self.writer_agent.run(WriterInput(request, profile, ats)),  # type: ignore[arg-type]
            )
        review = await self._run_agent(
            self.reviewer_agent.name,
            lambda: self.reviewer_agent.run(ReviewerInput(resume, ats)),  # type: ignore[arg-type]
        )
        elapsed = time.perf_counter() - started
        PIPELINE_LATENCY.observe(elapsed)
        return ResumeResponse(
            profile_analysis=profile,  # type: ignore[arg-type]
            ats_analysis=ats,  # type: ignore[arg-type]
            resume=resume,  # type: ignore[arg-type]
            review=review,  # type: ignore[arg-type]
            metadata=PipelineMetadata(
                request_id=request_id,
                pipeline_version=self.pipeline_version,
                agents_executed=["profile_analyzer", "ats_optimizer", "resume_writer", "reviewer"],
                processing_time_ms=round(elapsed * 1000, 2),
                ai_provider=provider_name,
                fallback_used=fallback_used,
            ),
        )
