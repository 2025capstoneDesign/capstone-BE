import uvicorn

from app.database.initialize import init_db


if __name__ == "__main__":
    init_db()
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)
