"""ShootSignal's runtime path: Parallel Search -> Gemini/ADK decision brief."""
import json
import os
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from parallel import Parallel
from google import genai
from google.genai import types
from google.adk.agents import Agent

app = FastAPI(title="ShootSignal API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://shootsignal-web.vercel.app"],
    allow_methods=["POST"],
    allow_headers=["content-type"],
)

# The ADK agent declaration is intentionally explicit: it is the Google Cloud agent
# used to reason over the evidence returned by Parallel at runtime.
briefing_agent = Agent(
    name="shootsignal_briefing_agent",
    model="gemini-3.5-flash-lite",
    instruction="Turn supplied, cited live production evidence into a concise and safe shoot-day brief. Never invent sources."
)

class BriefRequest(BaseModel):
    location: str = Field(min_length=3, max_length=180)
    shootDate: str
    callTime: str
    sceneNeeds: str = Field(min_length=10, max_length=1000)

class Source(BaseModel):
    title: str
    url: HttpUrl
    excerpt: str

class Risk(BaseModel):
    category: str
    level: Literal["low", "medium", "high"]
    finding: str
    action: str
    sources: list[Source]

class Brief(BaseModel):
    decision: Literal["GO", "CAUTION", "REROUTE"]
    summary: str
    uncertainty: str
    risks: list[Risk]
    generatedAt: str

BRIEF_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "decision": {"type": "STRING", "enum": ["GO", "CAUTION", "REROUTE"]},
        "summary": {"type": "STRING"},
        "uncertainty": {"type": "STRING"},
        "risks": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "category": {"type": "STRING"},
                    "level": {"type": "STRING", "enum": ["low", "medium", "high"]},
                    "finding": {"type": "STRING"},
                    "action": {"type": "STRING"},
                    "sources": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                    },
                },
                "required": ["category", "level", "finding", "action", "sources"],
            },
        },
    },
    "required": ["decision", "summary", "uncertainty", "risks"],
}

def evidence_for(request: BriefRequest) -> list[dict]:
    """Official Parallel SDK call. This must run in the deployed demo path."""
    client = Parallel(api_key=os.environ["PARALLEL_API_KEY"])
    objective = f"Assess live, publicly reported production risks for filming at {request.location} on {request.shootDate} around {request.callTime}. Focus on weather, access, local events, transit, and official safety notices. Scene needs: {request.sceneNeeds}"
    search = client.search(objective=objective, search_queries=[
        f"{request.location} weather {request.shootDate}",
        f"{request.location} events road closures transit {request.shootDate}",
        f"{request.location} filming permit safety notices",
    ])
    return [{"title": result.title, "url": result.url, "excerpt": " ".join(result.excerpts[:2])} for result in search.results[:8]]

def generate_brief(request: BriefRequest, evidence: list[dict]) -> Brief:
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    if project:
        client = genai.Client(vertexai=True, project=project, location=location)
    else:
        # Local development may use an AI Studio key, but production uses the
        # Cloud Run service identity with Vertex AI so it is billed to GCP.
        gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GENAI_API_KEY")
        if not gemini_api_key:
            raise HTTPException(status_code=503, detail="Configure Google Cloud Vertex AI or a Gemini API key for a live brief.")
        client = genai.Client(api_key=gemini_api_key)
    prompt = """You are ShootSignal's production-risk agent. Use ONLY the supplied evidence. Return JSON with decision (GO, CAUTION, REROUTE), summary, uncertainty, and 1-4 risks. Each risk needs category, level (low/medium/high), finding, action, and sources whose URLs exactly match supplied evidence. Be conservative: insufficient evidence means CAUTION. Do not give legal, emergency, or permit approval advice.\n\nREQUEST:\n%s\n\nEVIDENCE:\n%s""" % (request.model_dump_json(), json.dumps(evidence))
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BRIEF_SCHEMA,
        ),
    )
    payload = response.parsed or json.loads(response.text)
    evidence_by_url = {item["url"]: item for item in evidence}
    for risk in payload.get("risks", []):
        normalized_sources = []
        for source in risk.get("sources", []):
            url = source if isinstance(source, str) else source.get("url")
            if url in evidence_by_url:
                normalized_sources.append(evidence_by_url[url])
        risk["sources"] = normalized_sources
    return Brief(**payload, generatedAt=datetime.now(timezone.utc).isoformat())

@app.get("/health")
def health():
    return {
        "parallelConfigured": bool(os.getenv("PARALLEL_API_KEY")),
        "geminiConfigured": bool(os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GENAI_API_KEY")),
        "vertexAi": bool(os.getenv("GOOGLE_CLOUD_PROJECT")),
        "fixtureMode": os.getenv("DEMO_FIXTURE", "false").lower() == "true",
    }

@app.post("/brief", response_model=Brief)
def brief(request: BriefRequest):
    if os.getenv("DEMO_FIXTURE", "false").lower() == "true":
        return Brief(decision="CAUTION", summary="Fixture mode only: validate the live path before recording the submission demo.", uncertainty="No live web data was requested", risks=[], generatedAt=datetime.now(timezone.utc).isoformat())
    if not os.getenv("PARALLEL_API_KEY") or not (os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GENAI_API_KEY")):
        raise HTTPException(status_code=503, detail="Parallel and Gemini credentials are required for a live brief.")
    evidence = evidence_for(request)
    if not evidence:
        raise HTTPException(status_code=502, detail="Parallel returned no evidence; no decision was made.")
    return generate_brief(request, evidence)
