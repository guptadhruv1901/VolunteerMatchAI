from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Completion, RecommendationHistory
from app.services.catalogue import OPPORTUNITIES, get_context

def recommend(db: Session, profile, context_id: str | None = None, context=None, excluded=None):
    context = context or get_context(context_id or "quick")
    if not context:
        return None
    completed = {x.opportunity_id for x in db.scalars(select(Completion).where(Completion.profile_id == profile.id))}
    excluded = set(excluded or ()) | completed
    def hard(o):
        if o.id in excluded or o.cause not in profile.causes:
            return False
        if profile.location != "remote" and o.location not in (profile.location, "remote"):
            return False
        if profile.accessibility_needs and not set(profile.accessibility_needs).issubset(set(o.accessibility)):
            return False
        if getattr(context, "causes", []) and o.cause not in context.causes:
            return False
        if getattr(context, "environment", "any") not in ("any", o.environment):
            return False
        if getattr(context, "mode", "any") not in ("any", o.mode, o.format):
            return False
        if getattr(context, "equipment", []) and not set(context.equipment).issubset(set(o.equipment)):
            return False
        if getattr(context, "time", "flexible") == "30m" and o.time not in ("30m", "flexible"):
            return False
        return True
    eligible = [o for o in OPPORTUNITIES if hard(o)]
    def score(o):
        tags = getattr(context, "tags", [])
        return (3 if any(s in profile.skills for s in o.skills) else 0) + (2 if any(s in getattr(context, "skills", []) for s in o.skills) else 0) + (2 if any(t in o.tags for t in tags) else 0) + (1 if profile.availability in (o.schedule, "flexible") else 0)
    ranked = sorted(eligible, key=lambda o: (-score(o), o.id))
    matched = ranked[0] if ranked else None
    result = {"matched": bool(matched), "opportunity": matched.model_dump() if matched else None, "alternatives": [x.model_dump() for x in ranked[1:]], "reason": "Matched to your causes, context, and constraints." if matched else "No exact match is available right now. Try another context or update your preferences."}
    if hasattr(context, "model_dump"):
        context_payload = context.model_dump()
    else:
        context_payload = {
            "id": str(getattr(context, "id", "daily")),
            "time": context.time,
            "energy": context.energy,
            "environment": context.environment,
            "mode": context.mode,
            "skills": context.skills,
            "equipment": context.equipment,
            "causes": context.causes,
            "label": "Today's context",
            "description": "Saved daily context",
            "tags": [],
        }
    history = RecommendationHistory(profile_id=profile.id, context=context_payload, opportunity_id=matched.id if matched else None, result=result)
    db.add(history); db.commit(); db.refresh(history)
    result["history_id"] = history.id
    result["recommendation_id"] = history.id
    return result
