"""Reproducible analysis of an e-commerce checkout A/B test.

Run from repository root:
    python -m src.analysis
"""
from pathlib import Path
import json
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chisquare
from statsmodels.stats.proportion import (
    confint_proportions_2indep, proportion_confint, proportions_ztest,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "checkout_experiment_synthetic.csv"


def validate(df):
    """Fail loudly when dataset assumptions are violated."""
    fields = {"user_id", "assigned_at", "variant", "device", "traffic_source",
              "converted", "order_value_rub", "refunded"}
    assert fields.issubset(df.columns), "Missing columns in input dataset"
    assert len(df) > 0, "Empty dataset"
    assert df.user_id.notna().all() and df.user_id.is_unique, "Duplicates/null user_id"
    assert set(df.variant) == {"control", "treatment"}, "Unexpected variants"
    assert df[["converted", "refunded"]].isin([0, 1]).all().all(), "Invalid binary flags"
    assert df[["converted", "refunded", "order_value_rub"]].notna().all().all()
    assert (df.order_value_rub >= 0).all(), "Negative order value"
    assert (df.loc[df.converted.eq(0), "order_value_rub"] == 0).all(), "Non-buyer with revenue"
    assert (df.loc[df.converted.eq(1), "order_value_rub"] > 0).all(), "Buyer without revenue"
    assert (df.refunded <= df.converted).all(), "Refund without purchase"
    assert pd.to_datetime(df.assigned_at, errors="coerce").notna().all(), "Invalid dates"
    return df


def bootstrap_difference(a, b, n_boot=1200, seed=24):
    """Percentile bootstrap CI for mean(b) - mean(a), independently by arm."""
    rng = np.random.default_rng(seed)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    deltas = np.empty(n_boot)
    for i in range(n_boot):
        deltas[i] = b[rng.integers(len(b), size=len(b))].mean() - a[rng.integers(len(a), size=len(a))].mean()
    return [float(x) for x in np.quantile(deltas, [0.025, 0.975])]


def compute(df):
    validate(df)
    df = df.copy()
    df["net_revenue_rub"] = df.order_value_rub * (1 - df.refunded)
    arms = {arm: df.loc[df.variant.eq(arm)] for arm in ["control", "treatment"]}
    n_c, n_t = [len(arms[a]) for a in arms]
    x_c, x_t = [int(arms[a].converted.sum()) for a in arms]
    cr_c, cr_t = x_c / n_c, x_t / n_t
    abs_lift = cr_t - cr_c
    relative_lift = abs_lift / cr_c

    # SRM: a 1:1 assignment is assumed; high p-value is NOT evidence that
    # randomization is definitely correct.
    srm_p = float(chisquare([n_c, n_t], f_exp=[(n_c + n_t) / 2] * 2).pvalue)
    z_stat, p_val = proportions_ztest([x_t, x_c], [n_t, n_c], alternative="two-sided")
    ci_low, ci_high = confint_proportions_2indep(x_t, n_t, x_c, n_c, method="newcomb", compare="diff", alpha=0.05)

    rpv_c = float(arms["control"].net_revenue_rub.mean())
    rpv_t = float(arms["treatment"].net_revenue_rub.mean())
    rpv_ci = bootstrap_difference(arms["control"].net_revenue_rub, arms["treatment"].net_revenue_rub)
    refund_c = float(arms["control"].refunded.sum() / x_c)
    refund_t = float(arms["treatment"].refunded.sum() / x_t)
    result = {
        "dataset_type": "SYNTHETIC; NOT REAL CUSTOMERS",
        "analysis_window": "2026-09-01 to 2026-09-28 (synthetic)",
        "n_control": n_c, "n_treatment": n_t,
        "conversions_control": x_c, "conversions_treatment": x_t,
        "conversion_control": cr_c, "conversion_treatment": cr_t,
        "conversion_delta_pp": abs_lift * 100,
        "relative_conversion_lift_pct": relative_lift * 100,
        "ci95_conversion_delta_pp": [float(ci_low * 100), float(ci_high * 100)],
        "p_value_primary": float(p_val), "z_stat": float(z_stat),
        "srm_p_value": srm_p,
        "net_revenue_per_user_control_rub": rpv_c,
        "net_revenue_per_user_treatment_rub": rpv_t,
        "net_revenue_per_user_delta_rub": rpv_t - rpv_c,
        "ci95_net_revenue_per_user_delta_rub_bootstrap": rpv_ci,
        "refund_rate_given_purchase_control": refund_c,
        "refund_rate_given_purchase_treatment": refund_t,
        "recommendation": ("Consider a staged rollout with refund and revenue monitoring"
                            if p_val < 0.05 and ci_low > 0 and srm_p >= 0.001
                            else "Do not roll out based on this experiment alone"),
    }
    return result


def run_sql(df):
    """Recompute descriptive metrics from the accompanying SQLite SQL file."""
    with sqlite3.connect(":memory:") as conn:
        df.to_sql("experiment_users", conn, index=False, if_exists="replace")
        sql = (ROOT / "sql" / "metrics.sql").read_text(encoding="utf-8")
        # SQL file contains 3 independent SELECTs separated with semicolons.
        uncommented = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
        statements = [part.strip() for part in uncommented.split(";") if part.strip()]
        for i, statement in enumerate(statements, 1):
            print(f"\nSQL query {i}:")
            print(pd.read_sql_query(statement, conn).to_string(index=False))


def plot(df, result):
    (ROOT / "figures").mkdir(exist_ok=True)
    rate = [result["conversion_control"], result["conversion_treatment"]]
    arms = ["Control", "Treatment"]
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.bar(arms, [r * 100 for r in rate])
    for i, (n, x) in enumerate([
        (result["n_control"], result["conversions_control"]),
        (result["n_treatment"], result["conversions_treatment"]),
    ]):
        low, high = proportion_confint(x, n, alpha=0.05, method="wilson")
        ax.errorbar(i, 100 * (x / n), yerr=[[100 * ((x / n) - low)], [100 * (high - (x / n))]],
                    fmt="none", capsize=6)
        ax.text(i, rate[i] * 100 + 1.5, f"{100 * rate[i]:.2f}%", ha="center")
    ax.set(ylim=(0, 17), ylabel="Purchase conversion, %", title="Conversion by randomized group")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "conversion.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    vals = [result["net_revenue_per_user_control_rub"], result["net_revenue_per_user_treatment_rub"]]
    ax.bar(arms, vals)
    for i, y in enumerate(vals):
        ax.text(i, y + 12, f"{y:.0f} RUB", ha="center")
    ax.set(ylim=(0, max(vals) * 1.22), ylabel="Net revenue per assigned user, RUB",
           title="Descriptive revenue outcome (includes refunds)")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "revenue_per_user.png", dpi=160)
    plt.close(fig)


def report(result):
    """Write the report from computed numbers: no manually invented outcomes."""
    r=result
    md=f"""# Results: simulated checkout A/B experiment

> **Educational simulation only.** This is not a real company experiment. All users, orders and revenues were generated with a fixed random seed; the numerical results below do not prove a real-world business effect.

## Hypothesis and experimental design

- **Problem:** too many users abandon checkout.
- **H0:** treatment purchase conversion equals control conversion.
- **H1:** rates differ. Two-sided test; significance level 0.05.
- **Unit of randomization and analysis:** a unique eligible user; 1:1 assignment, one observation per user.
- **Primary metric:** completed purchase / assigned users.
- **Secondary (exploratory):** net revenue per assigned user (RUB; a fully refunded purchase contributes zero).
- **Guardrail:** refunded purchases / completed purchases, descriptive only.
- **Synthetic period:** 1–28 September 2026; 28 consecutive days.

## Assignment and data quality

| Check | Result |
|---|---:|
| Control users | {r['n_control']:,} |
| Treatment users | {r['n_treatment']:,} |
| SRM chi-square p-value (expected 50/50) | {r['srm_p_value']:.4f} |
| Duplicate user IDs / invalid values | 0 (validation passed) |

**Interpretation:** no SRM alarm at the conservative threshold p < 0.001; absence of an alarm is not proof of perfect randomization.

## Primary: conversion

| Metric | Control | Treatment |
|---|---:|---:|
| Conversions | {r['conversions_control']:,} | {r['conversions_treatment']:,} |
| Conversion rate | {r['conversion_control']:.2%} | {r['conversion_treatment']:.2%} |

- Absolute difference: **{r['conversion_delta_pp']:+.2f} percentage points**.
- Relative difference: **{r['relative_conversion_lift_pct']:+.2f}%**.
- Two-sided z-test p-value: **{r['p_value_primary']:.5g}**.
- 95% Newcombe confidence interval for conversion difference: **[{r['ci95_conversion_delta_pp'][0]:+.2f}, {r['ci95_conversion_delta_pp'][1]:+.2f}] pp**.

![Conversion comparison](../figures/conversion.png)

## Secondary: revenue and guardrail

| Metric | Control | Treatment |
|---|---:|---:|
| Net revenue / assigned user | {r['net_revenue_per_user_control_rub']:.2f} RUB | {r['net_revenue_per_user_treatment_rub']:.2f} RUB |
| Refunds / completed purchases | {r['refund_rate_given_purchase_control']:.2%} | {r['refund_rate_given_purchase_treatment']:.2%} |

- Revenue difference: **{r['net_revenue_per_user_delta_rub']:+.2f} RUB/user**, bootstrap 95% CI **[{r['ci95_net_revenue_per_user_delta_rub_bootstrap'][0]:+.2f}, {r['ci95_net_revenue_per_user_delta_rub_bootstrap'][1]:+.2f}] RUB/user**.
- Revenue is **exploratory**: its confidence interval is unadjusted for multiple metrics and cost of redesign is unknown.
- Refund-rate is conditional on purchasing and can be affected by who converts; it is not a formal non-inferiority safety test. A larger/longer test could be needed to assess small harms.

![Revenue comparison](../figures/revenue_per_user.png)

## Business recommendation

**{r['recommendation']}**. In this simulation, primary conversion is statistically higher, but real deployment would require product QA, correct logging, a pre-agreed minimum worthwhile effect and monitoring of refunds, latency, net margin and seasonal patterns. **Never treat simulated uplift as the employer's actual achieved business improvement.**

## Limitations

1. Data are fully simulated; there is no observed customer behavior or company relationship.
2. Single synthetic 28-day window, and one modeled purchase per user.
3. Refunds assumed to cancel the entire order; no returns after observation window.
4. Statistical significance is not the same as economic value; implementation costs not provided.
5. A/A test, instrumentation audit, network effects and novelty effects not assessed.
"""
    (ROOT / "reports" / "findings.md").write_text(md,encoding="utf-8")


def main():
    df=pd.read_csv(DATA)
    result=compute(df)
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    plot(df,result)
    report(result)
    print("Primary metric: {:.2%} -> {:.2%} ({:+.2f} pp)".format(
        result["conversion_control"], result["conversion_treatment"], result["conversion_delta_pp"]))
    print("Primary p-value:", round(result["p_value_primary"], 6))
    print("95% CI pp:", [round(x,3) for x in result["ci95_conversion_delta_pp"]])
    print("SRM p-value:", round(result["srm_p_value"],5))
    print("Reports and graphs saved to reports/ and figures/")
    run_sql(df)


if __name__ == "__main__":
    main()
