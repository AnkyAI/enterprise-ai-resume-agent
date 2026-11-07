import uvicorn


def run() -> None:
    uvicorn.run("resume_agent.api:app", host="0.0.0.0", port=8000, reload=False)  # noqa: S104


if __name__ == "__main__":
    run()
