"""Generate demonstrative, entirely synthetic A/B experiment data.

Run from repository root: python scripts/generate_data.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "checkout_experiment_synthetic.csv"
SEED = 20261022


def generate(n_per_arm=15000, seed=SEED):
    rng = np.random.default_rng(seed)
    n = 2 * n_per_arm
    # Assign participants 1:1 *before* their outcomes are simulated.
    variants = rng.choice(["control", "treatment"], size=n, p=[0.5, 0.5])
    device = rng.choice(["desktop", "mobile"], size=n, p=[0.38, 0.62])
    traffic_source = rng.choice(["organic", "paid", "direct"], size=n, p=[0.49, 0.33, 0.18])
    day = rng.integers(0, 28, size=n)
    dates = (pd.Timestamp("2026-09-01") + pd.to_timedelta(day, unit="D")).strftime("%Y-%m-%d")

    # Both arms share the same segment adjustments; treatment raises the
    # underlying conversion probability by 1.8 percentage points.
    baseline = 0.105 + np.where(device == "desktop", 0.012, -0.007)
    baseline += np.select([traffic_source == "direct", traffic_source == "paid"], [0.008, -0.006], default=0.0)
    probabilities = baseline + np.where(variants == "treatment", 0.018, 0.0)
    converted = rng.binomial(1, probabilities)

    # Rounded integer rubles, single purchase per person in the 28-day test.
    price = rng.gamma(shape=6, scale=440, size=n).round().astype(int)
    order_value = np.where(converted == 1, price, 0)
    refunded = rng.binomial(1, 0.045, size=n) * converted

    return pd.DataFrame({
        "user_id": [f"u{i:06d}" for i in range(1, n + 1)],
        "assigned_at": dates,
        "variant": variants,
        "device": device,
        "traffic_source": traffic_source,
        "converted": converted,
        "order_value_rub": order_value,
        "refunded": refunded,
    })


if __name__ == "__main__":
    df = generate()
    OUTPUT.parent.mkdir(exist_ok=True, parents=True)
    df.to_csv(OUTPUT, index=False)
    print(f"Generated {len(df):,} synthetic participant records -> {OUTPUT}")
