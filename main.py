from fastapi import FastAPI, Request
from helper import ai

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Talem AI server"}

@app.post("/")
async def root(request: Request):
    body = await request.json()
    aiResponse = ai.fetch_and_query(body.query) 

    return { "content": aiResponse}