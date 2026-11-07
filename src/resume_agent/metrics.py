from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "resume_agent_http_requests_total", "HTTP requests", ["method", "path", "status"]
)
REQUEST_LATENCY = Histogram(
    "resume_agent_http_request_duration_seconds", "HTTP request latency", ["method", "path"]
)
PIPELINE_LATENCY = Histogram("resume_agent_pipeline_duration_seconds", "Resume pipeline latency")
AGENT_RUNS = Counter("resume_agent_runs_total", "Agent executions", ["agent", "status"])
