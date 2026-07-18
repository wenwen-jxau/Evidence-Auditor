from fastapi import FastAPI
from pydantic import BaseModel,Field
from typing import Any
from agent_core import CFG,analyze
app=FastAPI(title=CFG["name"],version="1.0.0")
class Request(BaseModel):
    user_id:str="anonymous"; role:str="student"; course_unit:str=""; task_type:str=""; question:str=""; product_info:dict[str,Any]=Field(default_factory=dict); ingredient_list:Any=""; attachments:list[Any]=Field(default_factory=list); conversation_history:list[Any]=Field(default_factory=list); requested_output_level:str="learning_support"; additive:str=""; parameters:dict[str,Any]=Field(default_factory=dict); assignment_type:str=""
@app.get("/api/v1/agents/{agent_name}/health")
def health(agent_name:str): return {"status":"ok","agent":CFG["name"]}
@app.get("/api/v1/agents/{agent_name}/capabilities")
def capabilities(agent_name:str): return CFG
@app.post("/api/v1/agents/{agent_name}/chat")
def chat(agent_name:str,req:Request): return analyze(req.model_dump())
@app.post("/api/v1/agents/{agent_name}/analyze")
def analysis(agent_name:str,req:Request): return analyze(req.model_dump())
@app.post("/api/v1/feedback")
def feedback(payload:dict): return {"accepted":True,"feedback_id":"demo"}
@app.get("/api/v1/sessions/{session_id}")
def session(session_id:str): return {"session_id":session_id,"status":"learning_trace_available"}
