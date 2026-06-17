"""
Integration tests for the /decision endpoint using the 12 canonical alternatives.

Electrical setup
----------------
  LED forward voltage : 2.0 V
  Nominal LED current : 1.0 A  (A5-A8)
  Maximum current     : 4.0 A  (A9-A12)
  Global PSU voltage  : 32.0 V (> max scenario source voltage)

Each alternative has:
  source_voltage = led_voltage + DDP  →  R = DDP / I  (= U/I from the table)

Alternative table
-----------------
  A1  : DDP=5V,  I=0.125A → R=40Ω
  A2  : DDP=10V, I=0.125A → R=80Ω
  A3  : DDP=20V, I=0.125A → R=160Ω
  A4  : DDP=30V, I=0.125A → R=240Ω
  A5  : DDP=5V,  I=1A     → R=5Ω
  A6  : DDP=10V, I=1A     → R=10Ω
  A7  : DDP=20V, I=1A     → R=20Ω
  A8  : DDP=30V, I=1A     → R=30Ω
  A9  : DDP=5V,  I=4A     → R=1.25Ω
  A10 : DDP=10V, I=4A     → R=2.5Ω
  A11 : DDP=20V, I=4A     → R=5Ω
  A12 : DDP=30V, I=4A     → R=7.5Ω
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

LED_V = 2.0
PSU_V = 32.0
LED_I = 1.0
MAX_I = 4.0


def _source(ddp: float) -> float:
    """Convert resistor voltage drop to source voltage."""
    return LED_V + ddp


ALTERNATIVES = [
    {"name": "A1",  "ddp": 5,  "current": 0.125},
    {"name": "A2",  "ddp": 10, "current": 0.125},
    {"name": "A3",  "ddp": 20, "current": 0.125},
    {"name": "A4",  "ddp": 30, "current": 0.125},
    {"name": "A5",  "ddp": 5,  "current": 1.0},
    {"name": "A6",  "ddp": 10, "current": 1.0},
    {"name": "A7",  "ddp": 20, "current": 1.0},
    {"name": "A8",  "ddp": 30, "current": 1.0},
    {"name": "A9",  "ddp": 5,  "current": 4.0},
    {"name": "A10", "ddp": 10, "current": 4.0},
    {"name": "A11", "ddp": 20, "current": 4.0},
    {"name": "A12", "ddp": 30, "current": 4.0},
]

EXPECTED_RESISTANCES = {
    "A1": 40.0,
    "A2": 80.0,
    "A3": 160.0,
    "A4": 240.0,
    "A5": 5.0,
    "A6": 10.0,
    "A7": 20.0,
    "A8": 30.0,
    "A9": 1.25,
    "A10": 2.5,
    "A11": 5.0,
    "A12": 7.5,
}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def response(client):
    payload = {
        "psu_voltage": PSU_V,
        "led_voltage": LED_V,
        "led_current": LED_I,
        "max_current": MAX_I,
        "alternatives": [
            {
                "name": alt["name"],
                "target_current": alt["current"],
                "source_voltage": _source(alt["ddp"]),
            }
            for alt in ALTERNATIVES
        ],
    }
    return client.post("/api/v1/decision", json=payload)


class TestStatusAndStructure:
    def test_returns_200(self, response):
        assert response.status_code == 200

    def test_has_winner(self, response):
        body = response.json()
        assert "winner" in body
        assert isinstance(body["winner"], str)
        assert body["winner"] != ""

    def test_ranking_has_12_entries(self, response):
        body = response.json()
        assert len(body["ranking"]) == 12

    def test_all_alternative_names_present(self, response):
        body = response.json()
        names = {r["name"] for r in body["ranking"]}
        expected = {alt["name"] for alt in ALTERNATIVES}
        assert names == expected

    def test_ranks_are_unique_and_complete(self, response):
        body = response.json()
        ranks = sorted(r["rank"] for r in body["ranking"])
        assert ranks == list(range(1, 13))

    def test_winner_is_rank_1(self, response):
        body = response.json()
        rank1 = next(r for r in body["ranking"] if r["rank"] == 1)
        assert body["winner"] == rank1["name"]


class TestElectricalValues:
    def test_resistances_match_expected(self, response):
        body = response.json()
        result_by_name = {r["name"]: r for r in body["ranking"]}
        for name, expected_r in EXPECTED_RESISTANCES.items():
            actual_r = result_by_name[name]["resistor_ohm"]
            assert abs(actual_r - expected_r) < 1e-6, (
                f"{name}: expected R={expected_r}Ω, got {actual_r}Ω"
            )

    def test_power_values_are_positive(self, response):
        body = response.json()
        for r in body["ranking"]:
            assert r["power_w"] > 0, f"{r['name']} has non-positive power_w"

    def test_power_equals_i_squared_r(self, response):
        body = response.json()
        result_by_name = {r["name"]: r for r in body["ranking"]}
        for alt in ALTERNATIVES:
            name = alt["name"]
            i = alt["current"]
            r_expected = EXPECTED_RESISTANCES[name]
            expected_power = i ** 2 * r_expected
            actual_power = result_by_name[name]["power_w"]
            assert abs(actual_power - expected_power) < 1e-6, (
                f"{name}: expected P={expected_power}W, got {actual_power}W"
            )


class TestCOMETPreferences:
    def test_preferences_in_unit_interval(self, response):
        body = response.json()
        for r in body["ranking"]:
            assert 0.0 <= r["preference"] <= 1.0, (
                f"{r['name']} has preference {r['preference']} outside [0, 1]"
            )

    def test_higher_rank_has_higher_or_equal_preference(self, response):
        body = response.json()
        sorted_by_rank = sorted(body["ranking"], key=lambda r: r["rank"])
        for i in range(len(sorted_by_rank) - 1):
            a = sorted_by_rank[i]
            b = sorted_by_rank[i + 1]
            assert a["preference"] >= b["preference"], (
                f"rank {a['rank']} ({a['name']}, pref={a['preference']}) "
                f"has lower preference than rank {b['rank']} ({b['name']}, pref={b['preference']})"
            )

    def test_nominal_current_group_outranks_extreme_currents(self, response):
        """Nominal current alternatives (A5-A8, I=1A=led_current) should
        rank higher on average than the minimal-current group (A1-A4, I=0.125A)."""
        body = response.json()
        result_by_name = {r["name"]: r for r in body["ranking"]}

        nominal_ranks = [result_by_name[n]["rank"] for n in ("A5", "A6", "A7", "A8")]
        minimal_ranks = [result_by_name[n]["rank"] for n in ("A1", "A2", "A3", "A4")]

        avg_nominal = sum(nominal_ranks) / len(nominal_ranks)
        avg_minimal = sum(minimal_ranks) / len(minimal_ranks)

        assert avg_nominal < avg_minimal, (
            f"Expected nominal-current alternatives to rank higher on average "
            f"(got avg_rank={avg_nominal}) than minimal-current (avg_rank={avg_minimal})"
        )
