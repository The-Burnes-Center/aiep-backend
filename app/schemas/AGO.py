from pydantic import BaseModel

class AGOCreateSchema(BaseModel):
    AGO_id: int
    goal: str
    areasOfNeed: str
    baseline: str
    shortTermObjective: str
    role: str

class AGOListCreateSchema(BaseModel):
    AGOs: list[AGOCreateSchema]