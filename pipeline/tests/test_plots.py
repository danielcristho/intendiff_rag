from pipeline.results.figure_style import bounds, configs_of, short_model, wrap_label
from pipeline.results.pareto import dominates, pareto_front


def test_a_trade_off_keeps_both_points_on_the_front():
    senses = (-1, 1)
    assert dominates((0.1, 0.9), (0.2, 0.8), senses) and not dominates((0.1, 0.9), (0.1, 0.9), senses)
    assert pareto_front([(0.1, 0.9), (0.2, 0.8)], senses) == [0]
    assert pareto_front([(0.1, 0.5), (0.3, 0.9)], senses) == [0, 1]
    assert pareto_front([(0.1, 0.9), (0.1, 0.9)], senses) == [0, 1]
    assert pareto_front([(0.1, 0.9, 0.0), (0.2, 0.8, 1.0)], (-1, 1, 1)) == [0, 1]


def test_intervals_are_in_points_and_narrow_with_more_pairs():
    assert bounds(None, 0) == (0.0, 0.0)
    low, high = bounds(0.5, 4)
    assert low > 0 and high > 0 and bounds(0.5, 400)[0] < low and bounds(1.0, 4)[0] > 20


def test_labels_fit_the_ticks():
    assert short_model("Qwen/Qwen3-4B-Instruct-2507") == "Qwen3-4B"
    assert wrap_label("E4-noint") == "E4-\nnoint" and wrap_label("E0") == "E0"
    assert configs_of([{"descriptive": {"E0": {}}}, {"descriptive": {"E4": {}}}]) == ["E0", "E4"]
