from pydantic import BaseModel

class ScenarioResult(BaseModel):
    target_current: float
    resistor: float
    power: float
    score_comet: float
    is_safe: bool

class DecisionResponse(BaseModel):
    ranking: list[ScenarioResult]