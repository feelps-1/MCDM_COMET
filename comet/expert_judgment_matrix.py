from collections.abc import Callable
from dataclasses import dataclass
from itertools import combinations

from comet.characteristic_objects import CharacteristicObject, CharacteristicObjectSet

DIAGONAL_PREFERENCE = 0.5


@dataclass(frozen=True)
class ExpertJudgmentMatrix:

    alpha: tuple[tuple[float, ...], ...]
    summed_judgments: tuple[float, ...]

    @property
    def size(self) -> int:
        return len(self.alpha)


def _validate_preference(value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Preference value must be in [0, 1], got {value}.")


def _required_pairs(count: int) -> set[tuple[int, int]]:
    return {(i, j) for i, j in combinations(range(1, count + 1), 2)}


def _index_to_position(
    objects: tuple[CharacteristicObject, ...],
) -> dict[int, int]:
    return {obj.index: position for position, obj in enumerate(objects)}


def _normalize_comparisons(
    objects: tuple[CharacteristicObject, ...],
    comparisons: dict[tuple[int, int], float],
) -> dict[tuple[int, int], float]:
    index_to_position = _index_to_position(objects)
    required = _required_pairs(len(objects))
    normalized: dict[tuple[int, int], float] = {}

    for (left, right), value in comparisons.items():
        if left not in index_to_position or right not in index_to_position:
            raise ValueError(
                f"Comparison ({left}, {right}) references unknown characteristic objects."
            )
        if left == right:
            raise ValueError("Pairwise comparison indices must be distinct.")

        i, j = sorted((left, right))
        preference = value if (left, right) == (i, j) else 1.0 - value
        _validate_preference(preference)
        normalized[(i, j)] = preference

    missing = required - set(normalized)
    if missing:
        pair = next(iter(missing))
        raise ValueError(
            f"Missing pairwise comparison for characteristic objects ({pair[0]}, {pair[1]})."
        )

    return normalized


def _comparisons_from_compare(
    objects: tuple[CharacteristicObject, ...],
    compare: Callable[[CharacteristicObject, CharacteristicObject], float],
) -> dict[tuple[int, int], float]:
    comparisons: dict[tuple[int, int], float] = {}
    for left, right in combinations(objects, 2):
        value = compare(left, right)
        _validate_preference(value)
        comparisons[(left.index, right.index)] = value
    return comparisons


def _build_alpha_matrix(
    size: int,
    comparisons: dict[tuple[int, int], float],
) -> tuple[tuple[float, ...], ...]:
    matrix = [[DIAGONAL_PREFERENCE] * size for _ in range(size)]

    for (left, right), preference in comparisons.items():
        i = left - 1
        j = right - 1
        matrix[i][j] = preference
        matrix[j][i] = 1.0 - preference

    return tuple(tuple(row) for row in matrix)


def _compute_summed_judgments(
    alpha: tuple[tuple[float, ...], ...],
) -> tuple[float, ...]:
    return tuple(sum(row) for row in alpha)


def build_expert_judgment_matrix(
    characteristic_objects: CharacteristicObjectSet,
    *,
    comparisons: dict[tuple[int, int], float] | None = None,
    compare: Callable[[CharacteristicObject, CharacteristicObject], float] | None = None,
) -> ExpertJudgmentMatrix:
    """Build MEJ matrix alpha and summed judgments vector SJ."""
    if comparisons is None and compare is None:
        raise ValueError("Either comparisons or compare must be provided.")
    if comparisons is not None and compare is not None:
        raise ValueError("Provide only one of comparisons or compare.")

    objects = characteristic_objects.objects
    count = len(objects)
    if count == 0:
        raise ValueError("Characteristic object set must not be empty.")

    if compare is not None:
        comparisons = _comparisons_from_compare(objects, compare)

    assert comparisons is not None
    normalized = _normalize_comparisons(objects, comparisons)
    alpha = _build_alpha_matrix(count, normalized)
    summed_judgments = _compute_summed_judgments(alpha)

    return ExpertJudgmentMatrix(alpha=alpha, summed_judgments=summed_judgments)
