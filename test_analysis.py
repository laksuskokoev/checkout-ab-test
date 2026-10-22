import pytest
from scripts.generate_data import generate
from src.analysis import bootstrap_difference, compute, validate


def test_generated_data_valid():
    df=generate(n_per_arm=100, seed=42)
    assert len(df)==200
    assert validate(df) is df


def test_duplicate_user_id_is_detected():
    df=generate(n_per_arm=100, seed=42)
    df.loc[1, "user_id"] = df.loc[0, "user_id"]
    with pytest.raises(AssertionError, match="Duplicates"):
        validate(df)


def test_no_revenue_on_nonpurchase():
    df=generate(n_per_arm=100, seed=42)
    index=df.index[df.converted.eq(0)][0]
    df.loc[index, "order_value_rub"]=900
    with pytest.raises(AssertionError, match="Non-buyer"):
        validate(df)


def test_mean_difference_ci_has_two_numeric_bounds():
    ci=bootstrap_difference([0, 1, 2], [5, 6, 7], n_boot=200)
    assert ci[0] < ci[1]


def test_summary_matches_counts():
    df=generate(n_per_arm=300, seed=123)
    r=compute(df)
    assert r["n_control"] + r["n_treatment"] == 600
    assert r["n_control"] > 200
    assert r["n_treatment"] > 200
    assert r["conversions_control"] == df.loc[df.variant.eq("control"),"converted"].sum()
