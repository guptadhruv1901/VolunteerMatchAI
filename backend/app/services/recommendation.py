from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.adapter import AIAdapter
from app.models import Completion, RecommendationHistory
from app.services.catalogue import OPPORTUNITIES, get_context

ENERGY_LEVELS = {"low": 1, "medium": 2, "high": 3}
TIME_LIMITS = {"15m": 15, "30m": 30, "1h": 60, "90m": 90, "2h": 120}

def _time_limit(value: str) -> int | None:
    if value in TIME_LIMITS:
        return TIME_LIMITS[value]
    if value == "weekend":
        return 240
    return None

def recommend(db: Session, profile, context_id: str | None = None, context=None, excluded=None):
    context = context or get_context(context_id or "quick")
    if not context:
        return None

    completed = {
        row.opportunity_id
        for row in db.scalars(select(Completion).where(Completion.profile_id == profile.id))
    }
    excluded = set(excluded or ()) | completed
    context_causes = set(getattr(context, "causes", []) or [])
    context_skills = set(getattr(context, "skills", []) or [])
    context_equipment = {
        item for item in (getattr(context, "equipment", []) or [])
        if item not in {"none", "no-special-equipment"}
    }
    profile_causes = set(profile.causes or [])
    profile_skills = set(profile.skills or [])
    time_limit = _time_limit(getattr(context, "time", "flexible"))
    requested_energy = ENERGY_LEVELS.get(getattr(context, "energy", "medium"), 2)

    def hard_constraints(opportunity):
        if opportunity.id in excluded:
            return False
        if profile_causes and opportunity.cause not in profile_causes:
            return False
        if context_causes and opportunity.cause not in context_causes:
            return False
        if time_limit is not None and opportunity.duration_minutes > time_limit:
            return False
        if getattr(context, "environment", "any") not in ("any", opportunity.environment):
            return False
        requested_mode = getattr(context, "mode", "any")
        if requested_mode not in ("any", opportunity.mode, opportunity.format):
            return False
        if context_equipment and not context_equipment.issubset(set(opportunity.equipment)):
            return False
        if profile.accessibility_needs and not set(profile.accessibility_needs).issubset(set(opportunity.accessibility)):
            return False
        if ENERGY_LEVELS.get(opportunity.energy, 2) > requested_energy:
            return False
        return True

    eligible = [opportunity for opportunity in OPPORTUNITIES if hard_constraints(opportunity)]

    def score(opportunity):
        cause_match = 4 if opportunity.cause in context_causes else 0
        skill_match = 3 if profile_skills.intersection(opportunity.skills) else 0
        context_skill_match = 2 if context_skills.intersection(opportunity.skills) else 0
        equipment_match = 1 if not context_equipment or context_equipment.intersection(opportunity.equipment) else 0
        energy_match = 2 if ENERGY_LEVELS.get(opportunity.energy, 2) == requested_energy else 1
        return cause_match + skill_match + context_skill_match + equipment_match + energy_match

    ranked = sorted(eligible, key=lambda opportunity: (-score(opportunity), opportunity.duration_minutes, opportunity.id))
    matched = ranked[0] if ranked else None
    deterministic_reason = (
        "This match fits your selected cause, available time, energy, participation mode, "
        "skills, and equipment."
        if matched
        else "No opportunity satisfies all of your current constraints. Try more time, another mode, or another cause."
    )
    reason = deterministic_reason
    if matched:
        prompt = (
            "Write one concise, encouraging explanation (maximum 35 words) for this volunteer recommendation. "
            "Do not invent facts or add opportunities. Mention only the strongest fit between the person's context "
            "and the listed opportunity.\n"
            f"Profile causes: {sorted(profile_causes)}; profile skills: {sorted(profile_skills)}; "
            f"context causes: {sorted(context_causes)}; context skills: {sorted(context_skills)}; "
            f"time: {getattr(context, 'time', 'flexible')}; energy: {getattr(context, 'energy', 'medium')}; "
            f"mode: {getattr(context, 'mode', 'any')}; opportunity: {matched.title}; "
            f"cause: {matched.cause}; skills: {matched.skills}; duration: {matched.duration}."
        )
        try:
            generated_reason = AIAdapter().explain(prompt)
            if generated_reason:
                reason = generated_reason
        except RuntimeError:
            reason = deterministic_reason
    result = {
        "matched": bool(matched),
        "opportunity": matched.model_dump() if matched else None,
        "alternatives": [item.model_dump() for item in ranked[1:]],
        "reason": reason,
    }
    context_payload = context.model_dump() if hasattr(context, "model_dump") else {
        "id": str(getattr(context, "id", "daily")),
        "label": "Today's context",
        "description": "Saved daily context",
        "tags": [],
        "time": context.time,
        "energy": context.energy,
        "environment": context.environment,
        "mode": context.mode,
        "skills": context.skills,
        "equipment": context.equipment,
        "causes": context.causes,
    }
    history = RecommendationHistory(
        profile_id=profile.id,
        context=context_payload,
        opportunity_id=matched.id if matched else None,
        result=result,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    result["history_id"] = history.id
    result["recommendation_id"] = history.id
    return result
