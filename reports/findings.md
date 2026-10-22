# Results: simulated checkout A/B experiment

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
| Control users | 14,975 |
| Treatment users | 15,025 |
| SRM chi-square p-value (expected 50/50) | 0.7728 |
| Duplicate user IDs / invalid values | 0 (validation passed) |

**Interpretation:** no SRM alarm at the conservative threshold p < 0.001; absence of an alarm is not proof of perfect randomization.

## Primary: conversion

| Metric | Control | Treatment |
|---|---:|---:|
| Conversions | 1,602 | 1,849 |
| Conversion rate | 10.70% | 12.31% |

- Absolute difference: **+1.61 percentage points**.
- Relative difference: **+15.03%**.
- Two-sided z-test p-value: **1.2686e-05**.
- 95% Newcombe confidence interval for conversion difference: **[+0.89, +2.33] pp**.

![Conversion comparison](../figures/conversion.png)

## Secondary: revenue and guardrail

| Metric | Control | Treatment |
|---|---:|---:|
| Net revenue / assigned user | 267.31 RUB | 310.57 RUB |
| Refunds / completed purchases | 5.06% | 4.11% |

- Revenue difference: **+43.26 RUB/user**, bootstrap 95% CI **[+22.65, +61.85] RUB/user**.
- Revenue is **exploratory**: its confidence interval is unadjusted for multiple metrics and cost of redesign is unknown.
- Refund-rate is conditional on purchasing and can be affected by who converts; it is not a formal non-inferiority safety test. A larger/longer test could be needed to assess small harms.

![Revenue comparison](../figures/revenue_per_user.png)

## Business recommendation

**Consider a staged rollout with refund and revenue monitoring**. In this simulation, primary conversion is statistically higher, but real deployment would require product QA, correct logging, a pre-agreed minimum worthwhile effect and monitoring of refunds, latency, net margin and seasonal patterns. **Never treat simulated uplift as the employer's actual achieved business improvement.**

## Limitations

1. Data are fully simulated; there is no observed customer behavior or company relationship.
2. Single synthetic 28-day window, and one modeled purchase per user.
3. Refunds assumed to cancel the entire order; no returns after observation window.
4. Statistical significance is not the same as economic value; implementation costs not provided.
5. A/A test, instrumentation audit, network effects and novelty effects not assessed.
