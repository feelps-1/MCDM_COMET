from dataclasses import dataclass
from itertools import product

from backend.app.comet.problem_space import ProblemSpace, TriangularFuzzyNumber


@dataclass(frozen=True)
class CharacteristicObject:

    index: int
    fuzzy_sets: tuple[TriangularFuzzyNumber, ...]

    @property
    def nucleus_values(self) -> tuple[float, ...]:
        return tuple(fs.nucleus for fs in self.fuzzy_sets)

    @property
    def fuzzy_set_names(self) -> tuple[str, ...]:
        return tuple(fs.name for fs in self.fuzzy_sets)


@dataclass(frozen=True)
class CharacteristicObjectSet:

    objects: tuple[CharacteristicObject, ...]

    @property
    def count(self) -> int:
        return len(self.objects)


def count_characteristic_objects(problem_space: ProblemSpace) -> int:
    return problem_space.num_characteristic_objects


def generate_characteristic_objects(
    problem_space: ProblemSpace,
) -> CharacteristicObjectSet:
    combinations = product(
        *(criterion.fuzzy_sets for criterion in problem_space.criteria)
    )

    objects = tuple(
        CharacteristicObject(
            index=index,
            fuzzy_sets=tuple(fuzzy_sets),
        )
        for index, fuzzy_sets in enumerate(combinations, start=1)
    )

    return CharacteristicObjectSet(objects)
