from fastapi import FastAPI, Request
from helper import ai
from pydantic import BaseModel

app = FastAPI()

class QueryModal(BaseModel):
    query: str

@app.get("/")
async def root():
    return {"message": "Talem AI server"}

@app.post("/")
async def root(request: QueryModal):
    aiResponse = ai.fetch_and_query(request.query) 

    return { "content": aiResponse}