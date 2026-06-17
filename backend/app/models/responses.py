from pydantic import BaseModel

class ScenarioResult(BaseModel):
    name: str
    resistor_ohm: float
    power_w: float
    preference: float
    rank: int

class DecisionResponse(BaseModel):
    winner: str
    ranking: list[ScenarioResult]