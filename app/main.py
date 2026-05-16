from fastapi import FastAPI

app = FastAPI(title="Japan Advisory Backend")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Japan Advisory Backend is running"}
