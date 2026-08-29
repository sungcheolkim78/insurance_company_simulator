from fastapi import FastAPI

app = FastAPI(title="Insurance Company Simulator")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
