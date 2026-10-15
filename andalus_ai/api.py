from __future__ import annotations
import os
from typing import Any
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from .engine import AndalusAI

app=FastAPI(title="Andalus AI Engine",version="0.2.0")
_agent: AndalusAI|None=None
class ChatRequest(BaseModel):
    message: str=Field(min_length=1,max_length=5000)
    history: list[dict[str,str]]=Field(default_factory=list,max_length=20)
    confirmed: bool=False
class ChatResponse(BaseModel):
    ok: bool
    message: str
    type: str="answer"
    tool: str|None=None
    data: Any=None
    confirmation_required: bool=False
    arguments: dict[str,Any]=Field(default_factory=dict)
def get_agent()->AndalusAI:
    global _agent
    if _agent is None: _agent=AndalusAI()
    return _agent
def authorize(token: str|None)->None:
    expected=os.getenv("ANDALUS_AI_ADMIN_TOKEN")
    if not expected: raise HTTPException(status_code=503,detail="ANDALUS_AI_ADMIN_TOKEN must be configured before exposing the API.")
    if token!=expected: raise HTTPException(status_code=401,detail="Unauthorized")
@app.get("/health")
async def health()->dict[str,str]:
    return {"status":"ok","service":"andalus-ai-engine"}
@app.get("/tools")
async def tools(x_andalus_admin_token: str|None=Header(default=None))->dict[str,Any]:
    authorize(x_andalus_admin_token)
    return {"tools":get_agent().registry.definitions()}
@app.post("/chat",response_model=ChatResponse)
async def chat(body: ChatRequest,x_andalus_admin_token: str|None=Header(default=None))->ChatResponse:
    authorize(x_andalus_admin_token)
    agent=get_agent()
    try:
        result=await agent.understand(body.message,body.history)
        if result.type!="tool_call" or not result.tool:
            return ChatResponse(ok=True,message=result.message,type=result.type)
        if result.confirmation_required and not body.confirmed:
            return ChatResponse(ok=True,message="قبل التنفيذ، راجع العملية وأكدها. لم يتم تنفيذ أي تغيير أو إرسال.",type="confirmation",tool=result.tool,confirmation_required=True,arguments=result.arguments)
        if result.confirmation_required and result.tool not in {"create_task","schedule_task","send_whatsapp"}:
            raise HTTPException(status_code=403,detail="This action is not enabled for confirmation yet.")
        value=await agent.execute(result)
        ok=not(isinstance(value,dict) and value.get("ok") is False)
        return ChatResponse(ok=ok,message=result.message if ok else str(value.get("error") or value.get("message") or "تعذر إكمال الطلب."),type="tool_result",tool=result.tool,data=value)
    except HTTPException: raise
    except Exception as exc:
        raise HTTPException(status_code=502,detail=f"تعذر تنفيذ الطلب. راجع سجل الخادم. ({type(exc).__name__})")
@app.get("/")
async def root()->dict[str,str]:
    return {"name":"Andalus AI Engine","docs":"/docs","health":"/health"}
