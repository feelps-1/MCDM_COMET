from pydantic import BaseModel


class CharacteristicObject(BaseModel):
    current: float
    power: float

class Rule(BaseModel):
    co: CharacteristicObject
    preference: float

class AlternativeEvaluation(BaseModel):
    current: float
    power: float