from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class ProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    causes: list[str] = []
    skills: list[str] = []
    availability: str = "flexible"
    location: str = "remote"
    accessibility_needs: list[str] = []

class ProfileCreate(ProfileBase): pass
class ProfileUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    causes: list[str] | None = None
    skills: list[str] | None = None
    availability: str | None = None
    location: str | None = None
    accessibility_needs: list[str] | None = None

class ProfileOut(ProfileBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ContextOut(BaseModel):
    id: str = "daily"
    label: str = "Today's context"
    description: str = ""
    tags: list[str] = []
    time: str = "flexible"
    energy: str = "medium"
    environment: str = "any"
    mode: str = "any"
    skills: list[str] = []
    equipment: list[str] = []
    causes: list[str] = []

class DailyContextCreate(BaseModel):
    time: str = "flexible"
    energy: str = "medium"
    environment: str = "any"
    mode: str = "any"
    skills: list[str] = []
    equipment: list[str] = []
    causes: list[str] = []

class DailyContextOut(DailyContextCreate):
    id: int
    profile_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RecommendationRequest(BaseModel):
    profile_id: int
    context_id: str | None = None
    context: DailyContextCreate | None = None

class Opportunity(BaseModel):
    id: str
    title: str
    organization: str
    description: str
    cause: str
    format: str
    location: str
    duration: str
    schedule: str
    skills: list[str]
    accessibility: list[str]
    impact: str
    tags: list[str]
    time: str = "flexible"
    energy: str = "any"
    environment: str = "any"
    mode: str = "any"
    equipment: list[str] = []

class RecommendationResponse(BaseModel):
    matched: bool
    opportunity: Opportunity | None = None
    alternatives: list[Opportunity] = []
    reason: str
    context: ContextOut
    history_id: int | None = None
    recommendation_id: int | None = None

class CompletionCreate(BaseModel):
    profile_id: int
    opportunity_id: str
    reflection: str = ""

class CompletionOut(BaseModel):
    id: int
    profile_id: int
    opportunity_id: str
    completed_at: datetime
    model_config = ConfigDict(from_attributes=True)
