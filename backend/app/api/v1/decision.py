import logging
import traceback
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

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()


@router.post("/decision", response_model=DecisionResponse)
def make_decision(payload: DecisionRequest):
    logger.info("=== /decision called ===")
    logger.info(
        "psu_voltage=%.4f led_voltage=%.4f led_current=%.4f max_current=%.4f",
        payload.psu_voltage, payload.led_voltage, payload.led_current, payload.max_current,
    )
    logger.info("alternatives count: %d", len(payload.alternatives))
    for alt in payload.alternatives:
        logger.info(
            "  alt name=%s target_current=%.4f source_voltage=%s",
            alt.name, alt.target_current, alt.source_voltage,
        )

    try:
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
        logger.info("[step 1] Building problem space")
        max_eff_v = max(
            (s.source_voltage if s.source_voltage is not None else psu_v)
            for s in payload.alternatives
        )
        max_power = max_i * (max_eff_v - led_v)
        mid_power = max_power / 2.0
        logger.info("[step 1] max_eff_v=%.4f max_power=%.4f", max_eff_v, max_power)

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
        logger.info("[step 2] Generating characteristic objects")
        co_set = generate_characteristic_objects(problem_space)
        logger.info("[step 2] co_set count: %d", co_set.count)

        # --- Step 3: Build expert judgment matrix ---
        logger.info("[step 3] Building expert judgment matrix")

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
        logger.info("[step 3] MEJ size: %d", ejm.size)

        # --- Step 4: Build preference vector ---
        logger.info("[step 4] Building preference vector")
        pv = build_preference_vector(ejm)
        logger.info("[step 4] pv values: %s", pv.values)

        # --- Step 5: Build characteristic function ---
        logger.info("[step 5] Building characteristic function")
        cf = build_characteristic_function(co_set, pv)
        logger.info("[step 5] cf rules: %d", cf.size)

        # --- Step 6: Infer preference for each alternative ---
        logger.info("[step 6] Running inference for %d alternatives", len(payload.alternatives))
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
            logger.info(
                "  [step 6] %s: eff_v=%.4f R=%.4f P=%.4f alt_power=%.4f",
                scenario.name, eff_v, resistor, power_w, alt_power,
            )

            result = infer(
                problem_space=problem_space,
                characteristic_function=cf,
                alternative=(scenario.target_current, alt_power),
            )
            logger.info("  [step 6] %s preference=%.4f", scenario.name, result.preference)
            preferences.append(result.preference)
            electrical.append({"name": scenario.name, "resistor_ohm": resistor, "power_w": power_w})

        # --- Step 7: Build ranking ---
        logger.info("[step 7] Building ranking")
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

        logger.info("[step 7] Winner: %s", results[0].name)
        return DecisionResponse(winner=results[0].name, ranking=results)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[/decision] Unhandled exception: %s", exc)
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc
