from dataclasses import dataclass

from comet.expert_judgment_matrix import ExpertJudgmentMatrix

INDIFFERENCE_PREFERENCE = 0.5

@dataclass(frozen=True)
class PreferenceVector:

    values: tuple[float, ...]
    distinct_summed_judgments: tuple[float, ...]
    preference_levels: tuple[float, ...]


def _distinct_preference_levels(
    distinct_summed_judgments: tuple[float, ...],
) -> tuple[float, ...]:
    count = len(distinct_summed_judgments)
    if count == 1:
        return (INDIFFERENCE_PREFERENCE,)

    return tuple(index / (count - 1) for index in range(count))


def compute_preference_vector(
    summed_judgments: tuple[float, ...],
) -> PreferenceVector:
    if not summed_judgments:
        raise ValueError("Summed judgments vector must not be empty.")

    distinct_summed_judgments = tuple(sorted(set(summed_judgments)))
    preference_levels = _distinct_preference_levels(distinct_summed_judgments)
    level_by_sj = dict(zip(distinct_summed_judgments, preference_levels, strict=True))

    values = tuple(level_by_sj[sj] for sj in summed_judgments)
    return PreferenceVector(
        values=values,
        distinct_summed_judgments=distinct_summed_judgments,
        preference_levels=preference_levels,
    )


def compute_preference_vector_from_mej(
    expert_judgment_matrix: ExpertJudgmentMatrix,
) -> PreferenceVector:
    return compute_preference_vector(expert_judgment_matrix.summed_judgments)
