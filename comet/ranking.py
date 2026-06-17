from dataclasses import dataclass

@dataclass(frozen=True)
class RankedAlternative:
    rank: int
    alternative_index: int
    intpreference:float

@dataclass(frozen=True)
class Ranking:
    alternatives: tuple[RankedAlternative, ...]

    @property
    def size(self)-> int:
        return len(self.alternatives)

def build_ranking(
    preferences: tuple[float, ...]
) -> Ranking:
    
    if not preferences:
        raise ValueError("Preference list must not be empty.")
    
    sorted_preferences = sorted(
        enumerate(preferences, start=1),
        key=lambda item:item[1],
        reverse=True
    )

    ranked_alternatives = tuple(
        RankedAlternative(
            rank=rank,
            alternative_index=alternative_index,
            preference=preference
        )
        for rank, (alternative_index, preference)
        in enumerate(sorted_preferences, start=1)
    )

    return Ranking(alternatives=ranked_alternatives)