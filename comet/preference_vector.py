from dataclasses import dataclass
from comet.expert_judgment_matrix import ExpertJudgmentMatrix

@dataclass(frozen=True)
class PreferenceVector:
    values: tuple [float, ...]

    @property
    def size(self) -> int:
        return len(self.values)
    
def build_preference_vector(expert_judgement_matrix: ExpertJudgmentMatrix) -> PreferenceVector:
    sj = list(expert_judgement_matrix.summed_judgments)
    size = len(sj)
    
    if size == 0:
        raise ValueError("Summed judgements vector must not be empty.")
    
    unique_values = sorted(set(sj), reverse = True)
    k = len(unique_values)

    if k == 1:
        return PreferenceVector(values=tuple(1.0 for _ in range(size)))

    preferences = [0.0] * size

    for rank, value in enumerate(unique_values):
        preference = (k - rank - 1) / (k - 1)

        for index, sj_value in enumerate(sj):
            if sj_value == value:
                preferences[index] = preference
    
    return PreferenceVector(values=tuple(preferences))
