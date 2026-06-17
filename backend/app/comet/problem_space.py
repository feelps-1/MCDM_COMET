from dataclasses import dataclass
from math import prod

from backend.app.comet.membership_function import triangular_membership, validate_triangular_params


@dataclass(frozen=True)
class TriangularFuzzyNumber:

    a: float
    b: float
    c: float
    name: str = ""

    def __post_init__(self) -> None:
        validate_triangular_params(self.a, self.b, self.c)

    @property
    def nucleus(self) -> float:
        return self.b

    def membership(self, x: float) -> float:
        return triangular_membership(x, self.a, self.b, self.c)


@dataclass(frozen=True)
class Criterion:

    index: int
    name: str
    domain_min: float
    domain_max: float
    fuzzy_sets: tuple[TriangularFuzzyNumber, ...]

    def __post_init__(self) -> None:
        if self.index < 1:
            raise ValueError("Criterion index must be >= 1.")
        if self.domain_min >= self.domain_max:
            raise ValueError("domain_min must be less than domain_max.")
        if not self.fuzzy_sets:
            raise ValueError("Criterion must have at least one fuzzy set.")

        for fuzzy_set in self.fuzzy_sets:
            if fuzzy_set.a < self.domain_min or fuzzy_set.c > self.domain_max:
                raise ValueError(
                    f"TFN '{fuzzy_set.name}' is outside domain "
                    f"[{self.domain_min}, {self.domain_max}]."
                )

    @property
    def nuclei(self) -> tuple[float, ...]:
        return tuple(fuzzy_set.nucleus for fuzzy_set in self.fuzzy_sets)

    def membership(self, x: float, fuzzy_set: TriangularFuzzyNumber | str) -> float:
        self._validate_domain_value(x)
        return self._resolve_fuzzy_set(fuzzy_set).membership(x)

    def memberships(self, x: float) -> dict[str, float]:
        self._validate_domain_value(x)
        return {fuzzy_set.name: fuzzy_set.membership(x) for fuzzy_set in self.fuzzy_sets}

    def _validate_domain_value(self, x: float) -> None:
        if not self.domain_min <= x <= self.domain_max:
            raise ValueError(
                f"Value {x} is outside domain "
                f"[{self.domain_min}, {self.domain_max}] of criterion C_{self.index}."
            )

    def _resolve_fuzzy_set(
        self, fuzzy_set: TriangularFuzzyNumber | str
    ) -> TriangularFuzzyNumber:
        if isinstance(fuzzy_set, TriangularFuzzyNumber):
            if fuzzy_set not in self.fuzzy_sets:
                raise ValueError(
                    f"The given TFN does not belong to criterion C_{self.index}."
                )
            return fuzzy_set

        matches = [fs for fs in self.fuzzy_sets if fs.name == fuzzy_set]
        if not matches:
            raise ValueError(
                f"Fuzzy set '{fuzzy_set}' not found in C_{self.index}."
            )
        if len(matches) > 1:
            raise ValueError(
                f"Fuzzy set '{fuzzy_set}' is ambiguous in C_{self.index}."
            )
        return matches[0]


@dataclass(frozen=True)
class ProblemSpace:

    criteria: tuple[Criterion, ...]

    def __post_init__(self) -> None:
        if not self.criteria:
            raise ValueError("Problem must have at least one criterion.")

        indices = [criterion.index for criterion in self.criteria]
        expected = list(range(1, len(indices) + 1))
        if sorted(indices) != expected:
            raise ValueError(
                "Criterion indices must be sequential from 1 to r."
            )

    @property
    def num_criteria(self) -> int:
        return len(self.criteria)

    @property
    def num_characteristic_objects(self) -> int:
        return prod(len(criterion.fuzzy_sets) for criterion in self.criteria)

    def get_criterion(self, index: int) -> Criterion:
        try:
            return next(
                criterion for criterion in self.criteria if criterion.index == index
            )
        except StopIteration:
            raise KeyError(f"Criterion C_{index} not found.") from None
