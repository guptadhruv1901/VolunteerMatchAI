from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session
from app.config import settings
from app.crud.profiles import create_profile, delete_profile, get_profile, list_profiles, update_profile
from app.db.session import Base, engine, get_db
from app.models import Completion, DailyContext, RecommendationHistory
from app.schemas.api import *
from app.services.catalogue import CONTEXTS, OPPORTUNITIES, get_context, get_opportunity
from app.services.recommendation import recommend

Base.metadata.create_all(bind=engine)
if engine.dialect.name == "sqlite":
    profile_columns = {column["name"] for column in inspect(engine).get_columns("profiles")}
    if "description" not in profile_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE profiles ADD COLUMN description TEXT NOT NULL DEFAULT ''"))
app = FastAPI(title="VolunteerMatchAI API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health(): return {"status": "ok", "ai_enabled": settings.ai_enabled, "ai_provider": settings.ai_provider}

@app.get("/api/profiles", response_model=list[ProfileOut])
def profiles(db: Session = Depends(get_db)): return list_profiles(db)
@app.post("/api/profiles", response_model=ProfileOut, status_code=201)
def add_profile(data: ProfileCreate, db: Session = Depends(get_db)):
    return create_profile(db, data)
@app.get("/api/profiles/{profile_id}", response_model=ProfileOut)
def profile(profile_id: int, db: Session = Depends(get_db)):
    item = get_profile(db, profile_id)
    if not item: raise HTTPException(404, "Profile not found")
    return item
@app.patch("/api/profiles/{profile_id}", response_model=ProfileOut)
def patch_profile(profile_id: int, data: ProfileUpdate, db: Session = Depends(get_db)):
    item = get_profile(db, profile_id)
    if not item: raise HTTPException(404, "Profile not found")
    return update_profile(db, item, data)
@app.put("/api/profiles/{profile_id}", response_model=ProfileOut)
def put_profile(profile_id: int, data: ProfileUpdate, db: Session = Depends(get_db)):
    item = get_profile(db, profile_id)
    if not item: raise HTTPException(404, "Profile not found")
    return update_profile(db, item, data)
@app.delete("/api/profiles/{profile_id}", status_code=204)
def remove_profile(profile_id: int, db: Session = Depends(get_db)):
    item = get_profile(db, profile_id)
    if not item: raise HTTPException(404, "Profile not found")
    delete_profile(db, item)

@app.get("/api/contexts", response_model=list[ContextOut])
def contexts(): return CONTEXTS
@app.post("/api/profiles/{profile_id}/contexts", response_model=DailyContextOut, status_code=201)
def save_context(profile_id: int, data: DailyContextCreate, db: Session = Depends(get_db)):
    if not get_profile(db, profile_id): raise HTTPException(404, "Profile not found")
    item = DailyContext(profile_id=profile_id, **data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item
@app.post("/api/recommendations", response_model=RecommendationResponse)
def recommendations(data: RecommendationRequest, db: Session = Depends(get_db)):
    profile = get_profile(db, data.profile_id)
    saved_context = None
    if data.context_id and data.context_id.isdigit():
        saved_context = db.get(DailyContext, int(data.context_id))
        if saved_context and saved_context.profile_id != data.profile_id:
            saved_context = None
    context = data.context or saved_context or get_context(data.context_id or "quick")
    if not profile or not context: raise HTTPException(404, "Profile or context not found")
    result = recommend(db, profile, data.context_id, context)
    if isinstance(context, ContextOut):
        response_context = context
    else:
        context_values = context.model_dump() if hasattr(context, "model_dump") else {
            "time": context.time,
            "energy": context.energy,
            "environment": context.environment,
            "mode": context.mode,
            "skills": context.skills,
            "equipment": context.equipment,
            "causes": context.causes,
        }
        response_context = ContextOut(
            id=f"daily-{getattr(context, 'id', 'context')}",
            label="Today's context",
            description="Saved daily context",
            tags=[],
            **{k: v for k, v in context_values.items() if k not in {"id", "label", "description", "tags"}},
        )
    return {**result, "context": response_context}
@app.get("/api/recommendations/{recommendation_id}", response_model=RecommendationResponse)
def recommendation(recommendation_id: int, db: Session = Depends(get_db)):
    item = db.get(RecommendationHistory, recommendation_id)
    if not item: raise HTTPException(404, "Recommendation not found")
    return {**item.result, "context": item.context, "history_id": item.id, "recommendation_id": item.id}
@app.get("/api/recommendations/{recommendation_id}/alternatives", response_model=list[Opportunity])
def alternatives(recommendation_id: int, db: Session = Depends(get_db)):
    item = db.get(RecommendationHistory, recommendation_id)
    if not item: raise HTTPException(404, "Recommendation not found")
    prior = {x.opportunity_id for x in db.scalars(select(RecommendationHistory).where(RecommendationHistory.profile_id == item.profile_id)) if x.opportunity_id}
    profile = get_profile(db, item.profile_id)
    context = ContextOut.model_validate(item.context)
    result = recommend(db, profile, context=context, excluded=prior)
    return result["alternatives"]

@app.post("/api/recommendations/{recommendation_id}/alternatives", response_model=list[Opportunity])
def request_alternative(recommendation_id: int, db: Session = Depends(get_db)):
    return alternatives(recommendation_id, db)
@app.post("/api/completions", response_model=CompletionOut, status_code=201)
def complete(data: CompletionCreate, db: Session = Depends(get_db)):
    if not get_profile(db, data.profile_id) or not get_opportunity(data.opportunity_id): raise HTTPException(404, "Profile or opportunity not found")
    existing = db.scalar(select(Completion).where(Completion.profile_id == data.profile_id, Completion.opportunity_id == data.opportunity_id))
    if existing: return existing
    item = Completion(profile_id=data.profile_id, opportunity_id=data.opportunity_id)
    db.add(item); db.commit(); db.refresh(item); return item
@app.post("/api/recommendations/{recommendation_id}/completion", response_model=CompletionOut, status_code=201)
def complete_recommendation(recommendation_id: int, db: Session = Depends(get_db)):
    item = db.get(RecommendationHistory, recommendation_id)
    if not item or not item.opportunity_id: raise HTTPException(404, "Recommendation not found")
    return complete(CompletionCreate(profile_id=item.profile_id, opportunity_id=item.opportunity_id), db)
@app.get("/api/history/{profile_id}")
def history(profile_id: int, db: Session = Depends(get_db)):
    if not get_profile(db, profile_id): raise HTTPException(404, "Profile not found")
    return list(db.scalars(select(RecommendationHistory).where(RecommendationHistory.profile_id == profile_id).order_by(RecommendationHistory.created_at.desc())))
@app.get("/api/profiles/{profile_id}/history", response_model=HistorySummary)
def profile_history(profile_id: int, db: Session = Depends(get_db)):
    if not get_profile(db, profile_id):
        raise HTTPException(404, "Profile not found")
    completions = list(db.scalars(select(Completion).where(Completion.profile_id == profile_id).order_by(Completion.completed_at.desc())))
    recommendations = list(db.scalars(select(RecommendationHistory).where(RecommendationHistory.profile_id == profile_id).order_by(RecommendationHistory.created_at.desc())))
    opportunities = {opportunity.id: opportunity for opportunity in OPPORTUNITIES}
    items = [
        HistoryItem(kind="completed", id=item.id, opportunity=opportunities.get(item.opportunity_id), completed_at=item.completed_at)
        for item in completions
    ]
    items.extend(
        HistoryItem(kind="recommended", id=item.id, opportunity=opportunities.get(item.opportunity_id), created_at=item.created_at)
        for item in recommendations
        if item.opportunity_id
    )
    return HistorySummary(
        total_completed=len(completions),
        total_minutes=sum(opportunities[item.opportunity_id].duration_minutes for item in completions if item.opportunity_id in opportunities),
        items=items,
    )
