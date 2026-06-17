from dataclasses import dataclass
from app.comet.characteristic_function import CharacteristicFunction
from app.comet.problem_space import ProblemSpace

@dataclass(frozen=True)
class ActivatedRule:
    rule_index: int
    activation_degree: float
    preference: float

@dataclass(frozen=True)
class InferenceResult:
    activated_rules: tuple[ActivatedRule, ...]
    preference: float

def infer(
    problem_space: ProblemSpace,
    characteristic_function: CharacteristicFunction,
    alternative: tuple[float, ...]
) -> InferenceResult:
    if len(alternative) != problem_space.num_criteria:
        raise ValueError(
            "Alternative dimension does not match the number of criteria."
        )
    activated_rules: list[ActivatedRule] = []

    for index, rule in enumerate(characteristic_function.rules, start=1):
        degree = 1.0 

        for value, criterion, fuzzy_set in zip(
            alternative,
            problem_space.criteria,
            rule.characteristic_object.fuzzy_sets
        ):
            degree *= criterion.membership(value, fuzzy_set)
        
        if degree > 0.0:
            activated_rules.append(
                ActivatedRule(
                    rule_index=index,
                    activation_degree=degree,
                    preference=rule.preference
                )
            )
        
    if not activated_rules:
        raise ValueError(
            "No rule was activated by the given alternative."
        )
    
    total_activation = sum(
        rule.activation_degree for rule in activated_rules
    )
    normalized_rules = tuple(
        ActivatedRule(
            rule_index=rule.rule_index,
            activation_degree=rule.activation_degree / total_activation,
            preference = rule.preference
        )
        for rule in activated_rules
    )

    preference = sum(
        rule.activation_degree * rule.preference
        for rule in normalized_rules
    )

    return InferenceResult(
        activated_rules=normalized_rules,
        preference=preference
    )