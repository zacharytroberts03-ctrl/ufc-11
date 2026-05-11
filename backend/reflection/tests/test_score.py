"""Unit tests for backend.reflection.score — deterministic, no LLM."""

import pytest
from backend.reflection.score import score_fight, score_card


def _baseline_prediction():
    return {
        "winner": "Arnold Allen",
        "win_prob": 0.62,
        "method": {"ko_tko": 0.25, "submission": 0.05, "decision": 0.70},
        "rounds": {
            "ends_round_1": 0.05,
            "ends_round_2": 0.10,
            "ends_round_3": 0.10,
            "ends_round_4_or_later": 0.05,
            "goes_to_decision": 0.70,
        },
    }


def _baseline_actual(winner="Arnold Allen", method="Decision", round_=3):
    return {"winner": winner, "method": method, "round": round_, "time": "5:00"}


def _baseline_closing_line(f1_implied=0.677):
    return {"f1_moneyline": -210, "f1_implied_prob": f1_implied}


def test_pick_correct_when_winner_matches():
    s = score_fight(
        fighter1="Arnold Allen",
        fighter2="Melquizael Costa",
        predicted=_baseline_prediction(),
        actual=_baseline_actual(),
        closing_line=_baseline_closing_line(),
    )
    assert s["pick_correct"] is True


def test_pick_wrong_when_winner_loses():
    s = score_fight(
        fighter1="Arnold Allen",
        fighter2="Melquizael Costa",
        predicted=_baseline_prediction(),
        actual=_baseline_actual(winner="Melquizael Costa"),
        closing_line=_baseline_closing_line(),
    )
    assert s["pick_correct"] is False


def test_method_correct_decision_vs_decision():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted=_baseline_prediction(),  # decision is highest at 0.70
        actual=_baseline_actual(method="Decision"),
        closing_line=_baseline_closing_line(),
    )
    assert s["method_correct"] is True


def test_method_wrong_when_predicted_decision_actual_ko():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted=_baseline_prediction(),
        actual=_baseline_actual(method="KO/TKO"),
        closing_line=_baseline_closing_line(),
    )
    assert s["method_correct"] is False


def test_round_correct_when_predicted_decision_actual_decision():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted=_baseline_prediction(),  # goes_to_decision is 0.70
        actual=_baseline_actual(method="Decision"),
        closing_line=_baseline_closing_line(),
    )
    # Decision has no specific round; round_correct compares "decision predicted" vs "actual was decision"
    assert s["round_correct"] is True


def test_brier_score_for_correct_pick():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted=_baseline_prediction(),  # win_prob 0.62 for Allen
        actual=_baseline_actual(winner="Arnold Allen"),
        closing_line=_baseline_closing_line(),
    )
    # Brier = (0.62 - 1.0)^2 = 0.1444
    assert s["brier_score"] == pytest.approx(0.1444, abs=1e-4)


def test_brier_score_for_wrong_pick():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted=_baseline_prediction(),
        actual=_baseline_actual(winner="Melquizael Costa"),
        closing_line=_baseline_closing_line(),
    )
    # Brier = (0.62 - 0.0)^2 = 0.3844
    assert s["brier_score"] == pytest.approx(0.3844, abs=1e-4)


def test_bet_signal_pass_when_we_agree_with_market():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted={**_baseline_prediction(), "win_prob": 0.66},
        actual=_baseline_actual(),
        closing_line=_baseline_closing_line(f1_implied=0.68),  # |0.66-0.68|<=0.05
    )
    assert s["line_beat"]["bet_signal"] == "pass"


def test_bet_signal_back_f1_when_we_undervalue_market():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted={**_baseline_prediction(), "win_prob": 0.80},
        actual=_baseline_actual(),
        closing_line=_baseline_closing_line(f1_implied=0.60),  # edge +0.20 → back_f1
    )
    assert s["line_beat"]["bet_signal"] == "back_f1"


def test_bet_signal_back_f2_when_market_overvalues_f1():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted={**_baseline_prediction(), "winner": "Arnold Allen", "win_prob": 0.40},
        actual=_baseline_actual(),
        closing_line=_baseline_closing_line(f1_implied=0.70),  # edge -0.30 → back_f2
    )
    assert s["line_beat"]["bet_signal"] == "back_f2"


def test_line_beat_profitable_when_we_back_winner():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted={**_baseline_prediction(), "win_prob": 0.80},
        actual=_baseline_actual(winner="Arnold Allen"),
        closing_line=_baseline_closing_line(f1_implied=0.60),
    )
    assert s["line_beat"]["bet_signal"] == "back_f1"
    assert s["line_beat"]["would_have_been_profitable"] is True


def test_closing_line_null_yields_null_line_beat():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted=_baseline_prediction(),
        actual=_baseline_actual(),
        closing_line=None,
    )
    assert s["line_beat"] is None
    # Other metrics still compute
    assert s["pick_correct"] is True
    assert s["brier_score"] is not None


def test_score_card_aggregates():
    per_fight = [
        {"scoring": {"pick_correct": True, "brier_score": 0.10,
                     "line_beat": {"bet_signal": "back_f1",
                                   "would_have_been_profitable": True,
                                   "f1_implied_prob_at_close": 0.60}}},
        {"scoring": {"pick_correct": False, "brier_score": 0.40,
                     "line_beat": {"bet_signal": "back_f2",
                                   "would_have_been_profitable": False,
                                   "f1_implied_prob_at_close": 0.55}}},
        {"scoring": {"pick_correct": True, "brier_score": 0.15,
                     "line_beat": {"bet_signal": "pass",
                                   "would_have_been_profitable": None,
                                   "f1_implied_prob_at_close": 0.50}}},
    ]
    rollup = score_card(per_fight)
    assert rollup["fights_scored"] == 3
    assert rollup["pick_accuracy"] == pytest.approx(2 / 3)
    assert rollup["avg_brier"] == pytest.approx((0.10 + 0.40 + 0.15) / 3)
    assert rollup["betting_record"]["bets_taken"] == 2
    assert rollup["betting_record"]["bets_won"] == 1
