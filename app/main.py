from __future__ import annotations
from fastapi import FastAPI
from pydantic import BaseModel
from agent import root_handle

app = FastAPI(title="Zero-Touch CX API")

class ChatIn(BaseModel):
    text: str

@app.post("/chat")
def chat(inp: ChatIn):
    return root_handle(inp.text)
