from dataclasses import dataclass
from comet.characteristic_objects import (
    CharacteristicObject,
    CharacteristicObjectSet
)
from comet.preference_vector import PreferenceVector

@dataclass(frozen=True)
class CharacteristicRule:

    characteristic_object: CharacteristicObject
    preference: float

@dataclass(frozen=True)
class CharacteristicFunction:

    rules: tuple[CharacteristicRule, ...]

    @property
    def size(self) -> int:
        return len(self.rules)
    
def build_characteristic_function(
    characteristic_objects: CharacteristicObjectSet,
    preference_vector: PreferenceVector
) -> CharacteristicFunction:
    
    objects = characteristic_objects.objects
    preferences = preference_vector.values

    if len(objects) != len(preferences):
        raise ValueError(
            "Number of characteristic objects must match "
            "number of preference values."
        )
    
    rules = tuple(
        CharacteristicRule(
            characteristic_object = co,
            preference = preference
        )
        for co, prefrence in zip(objects, preferences)
    )

    return CharacteristicFunction(rules=rules)
