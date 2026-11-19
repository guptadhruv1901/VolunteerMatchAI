from app.schemas.api import ContextOut, Opportunity

CONTEXTS = [
    ContextOut(id="quick", label="I have 30 minutes", description="A small action that fits into a busy day.", tags=["short", "remote"], time="30m"),
    ContextOut(id="weekend", label="I have a weekend window", description="Meaningful work you can plan ahead.", tags=["weekend", "local"], time="weekend"),
    ContextOut(id="outdoors", label="I want to be outside", description="Fresh air and practical community impact.", tags=["outdoors", "local"], environment="outdoors"),
    ContextOut(id="learn", label="I want to use my skills", description="A focused opportunity that matches your strengths.", tags=["skills", "remote"], mode="skills"),
]

OPPORTUNITIES = [
    Opportunity(id="food-001", title="Pack community pantry boxes", organization="Northside Food Bank", description="Prepare pantry staples for neighbors facing food insecurity.", cause="food", format="in-person", location="local", duration="2 hours", schedule="weekend", skills=["organizing", "teamwork"], accessibility=["step-free"], impact="Provides 25 family food boxes.", tags=["weekend", "local"]),
    Opportunity(id="food-002", title="Translate food access guides", organization="Open Table Network", description="Translate a short guide to local food resources.", cause="food", format="remote", location="remote", duration="30 minutes", schedule="flexible", skills=["languages", "writing"], accessibility=["screen-reader"], impact="Helps neighbors find meals and benefits.", tags=["short", "remote", "skills"]),
    Opportunity(id="climate-001", title="Restore a neighborhood garden", organization="Green Block", description="Plant native species and refresh a shared garden.", cause="climate", format="in-person", location="local", duration="3 hours", schedule="weekend", skills=["gardening", "teamwork"], accessibility=["step-free"], impact="Creates habitat and cooler public space.", tags=["outdoors", "local", "weekend"]),
    Opportunity(id="youth-001", title="Tutor a young learner online", organization="Bright Futures", description="Offer a friendly one-to-one learning session.", cause="youth", format="remote", location="remote", duration="1 hour", schedule="flexible", skills=["teaching", "communication"], accessibility=["screen-reader"], impact="Builds confidence and learning momentum.", tags=["remote", "skills"]),
]

def get_context(context_id: str):
    return next((c for c in CONTEXTS if c.id == context_id), None)
def get_opportunity(opportunity_id: str):
    return next((o for o in OPPORTUNITIES if o.id == opportunity_id), None)
