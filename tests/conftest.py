import os

os.environ["RESUME_API_KEYS"] = "test-key"
os.environ["RESUME_RATE_LIMIT_REQUESTS"] = "100"

import pytest
from fastapi.testclient import TestClient

from resume_agent.api import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def payload() -> dict:
    return {
        "profile": {
            "full_name": "Jordan Lee",
            "email": "jordan@example.com",
            "location": "Seattle, WA",
            "headline": "Data Analytics Engineer",
            "skills": ["Python", "SQL", "Power BI", "FastAPI"],
            "experience": [
                {
                    "company": "Acme Analytics",
                    "title": "Data Analyst",
                    "start_date": "2021-01-01",
                    "end_date": "2024-01-01",
                    "responsibilities": ["Built executive dashboards for operations leaders"],
                    "achievements": [
                        "Reduced weekly reporting time by 40% using Python automation"
                    ],
                }
            ],
            "projects": [
                {
                    "name": "Forecasting Platform",
                    "description": "Built a demand forecasting service used by planning teams",
                    "technologies": ["Python", "FastAPI", "SQL"],
                }
            ],
            "education": [
                {
                    "institution": "State University",
                    "degree": "BSc",
                    "field_of_study": "Information Systems",
                    "graduation_year": 2020,
                }
            ],
            "certifications": ["Microsoft Power BI Data Analyst"],
        },
        "target_role": "Senior Data Analyst",
        "job_description": (
            "Seeking a data analyst with Python, SQL, Power BI, dashboard, stakeholder, "
            "forecasting, and analytics experience."
        ),
    }
