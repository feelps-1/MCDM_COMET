from pydantic import BaseModel, Field
from typing import List

class ScenarioInput(BaseModel):
    target_current: float = Field(gt=0)

class DecisionRequest(BaseModel):
    psu_voltage: float = Field(gt=0)
    led_current: float = Field(gt=0)
    max_current: float = Field(gt=0)

    alternatives: List[ScenarioInput]