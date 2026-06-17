from fastapi import APIRouter, HTTPException

from app.models.requests import DecisionRequest
from app.models.responses import DecisionResponse, ScenarioResult
from app.comet.problem_space import ProblemSpace, Criterion, TriangularFuzzyNumber
from app.comet.characteristic_objects import generate_characteristic_objects
from app.comet.expert_judgment_matrix import build_expert_judgment_matrix
from app.comet.preference_vector import build_preference_vector
from app.comet.characteristic_function import build_characteristic_function
from app.comet.fuzzy_inference import infer
from app.comet.ranking import build_ranking
from app.services.electrical.ohm_engine import OhmsLawCalculator, LEDCircuit

router = APIRouter()


@router.post("/decision", response_model=DecisionResponse)
def make_decision(payload: DecisionRequest):
    psu_v = payload.psu_voltage
    led_v = payload.led_voltage
    led_i = payload.led_current
    max_i = payload.max_current

    if led_v >= psu_v:
        raise HTTPException(
            status_code=422,
            detail="led_voltage must be less than psu_voltage.",
        )
    if led_i >= max_i:
        raise HTTPException(
            status_code=422,
            detail="led_current must be less than max_current.",
        )
    for scenario in payload.alternatives:
        if scenario.target_current > max_i:
            raise HTTPException(
                status_code=422,
                detail=f"Alternative '{scenario.name}' target_current exceeds max_current.",
            )
        eff_v = scenario.source_voltage if scenario.source_voltage is not None else psu_v
        if eff_v <= led_v:
            raise HTTPException(
                status_code=422,
                detail=f"Alternative '{scenario.name}' source_voltage must be greater than led_voltage.",
            )

    # --- Step 1: Define problem space ---
    max_eff_v = max(
        (s.source_voltage if s.source_voltage is not None else psu_v)
        for s in payload.alternatives
    )
    max_power = max_i * (max_eff_v - led_v)
    mid_power = max_power / 2.0

    c1 = Criterion(
        index=1,
        name="current",
        domain_min=0.0,
        domain_max=max_i,
        fuzzy_sets=(
            TriangularFuzzyNumber(0.0, 0.0, led_i, name="zero"),
            TriangularFuzzyNumber(0.0, led_i, max_i, name="nominal"),
            TriangularFuzzyNumber(led_i, max_i, max_i, name="max"),
        ),
    )
    c2 = Criterion(
        index=2,
        name="power",
        domain_min=0.0,
        domain_max=max_power,
        fuzzy_sets=(
            TriangularFuzzyNumber(0.0, 0.0, mid_power, name="low"),
            TriangularFuzzyNumber(0.0, mid_power, max_power, name="medium"),
            TriangularFuzzyNumber(mid_power, max_power, max_power, name="high"),
        ),
    )
    problem_space = ProblemSpace(criteria=(c1, c2))

    # --- Step 2: Generate characteristic objects ---
    co_set = generate_characteristic_objects(problem_space)

    # --- Step 3: Build expert judgment matrix ---
    def compare(co_a, co_b):
        curr_a, pow_a = co_a.nucleus_values
        curr_b, pow_b = co_b.nucleus_values

        c1_score_a = 1.0 - abs(curr_a - led_i) / max_i
        c1_score_b = 1.0 - abs(curr_b - led_i) / max_i

        c2_score_a = 1.0 - pow_a / max_power
        c2_score_b = 1.0 - pow_b / max_power

        score_a = (c1_score_a + c2_score_a) / 2.0
        score_b = (c1_score_b + c2_score_b) / 2.0

        total = score_a + score_b
        return 0.5 if total == 0.0 else score_a / total

    ejm = build_expert_judgment_matrix(co_set, compare=compare)

    # --- Step 4: Build preference vector ---
    pv = build_preference_vector(ejm)

    # --- Step 5: Build characteristic function ---
    cf = build_characteristic_function(co_set, pv)

    # --- Step 6: Compute electrical values and infer preference for each alternative ---
    preferences: list[float] = []
    electrical: list[dict] = []

    for scenario in payload.alternatives:
        eff_v = scenario.source_voltage if scenario.source_voltage is not None else psu_v
        circuit = LEDCircuit(
            source_voltage=eff_v,
            led_voltage=led_v,
            led_current=scenario.target_current,
        )
        resistor = OhmsLawCalculator.calculate_resistor(circuit)
        power_w = OhmsLawCalculator.calculate_resistor_power(resistor, scenario.target_current)
        alt_power = scenario.target_current * (eff_v - led_v)

        result = infer(
            problem_space=problem_space,
            characteristic_function=cf,
            alternative=(scenario.target_current, alt_power),
        )
        preferences.append(result.preference)
        electrical.append({"name": scenario.name, "resistor_ohm": resistor, "power_w": power_w})

    # --- Step 7: Build ranking ---
    ranking = build_ranking(tuple(preferences))

    results = [
        ScenarioResult(
            name=electrical[ra.alternative_index - 1]["name"],
            resistor_ohm=electrical[ra.alternative_index - 1]["resistor_ohm"],
            power_w=electrical[ra.alternative_index - 1]["power_w"],
            preference=ra.intpreference,
            rank=ra.rank,
        )
        for ra in ranking.alternatives
    ]

    return DecisionResponse(winner=results[0].name, ranking=results)