import pandas as pd
from scipy import stats

CSV_PATH = #UPDATE TO YOUR PATHS


def main():
    df = pd.read_csv(CSV_PATH)

    # Collapse to one row per practice, averaging across months
    practice_avg = df.groupby(["GP_CODE", "GP_NAME", "imd_decile"]).agg(
        mean_appts_per_1000=("appts_per_1000_patients", "mean"),
        mean_dna_rate_pct=("dna_rate_pct", "mean"),
    ).reset_index()

    print(f"{len(practice_avg)} practices\n")
    print("=== Spearman rank correlation ===")
    print("(rho: -1 to +1 | p < 0.05 is conventionally 'statistically significant')\n")

    rho1, p1 = stats.spearmanr(practice_avg["imd_decile"], practice_avg["mean_appts_per_1000"])
    print(f"Appointments per 1,000 patients vs IMD decile:")
    print(f"  rho = {rho1:.3f}, p = {p1:.10f}")
    _interpret(rho1, p1, "appointments per 1,000 patients")

    rho2, p2 = stats.spearmanr(practice_avg["imd_decile"], practice_avg["mean_dna_rate_pct"])
    print(f"\nDNA rate vs IMD decile:")
    print(f"  rho = {rho2:.3f}, p = {p2:.10f}")
    _interpret(rho2, p2, "DNA rate")


def _interpret(rho, p, label):
    direction = "positive" if rho > 0 else "negative"
    strength = "weak" if abs(rho) < 0.3 else "moderate" if abs(rho) < 0.6 else "strong"
    sig = "statistically significant" if p < 0.05 else "not statistically significant"
    print(f"  -> {strength} {direction} correlation, {sig}")
    if rho < 0:
        print(f"     (decile 1 = MOST deprived, so this means {label} tends to be HIGHER "
              f"in more deprived areas)")
    else:
        print(f"     (decile 1 = MOST deprived, so this means {label} tends to be LOWER "
              f"in more deprived areas / higher in less deprived areas)")


if __name__ == "__main__":
    main()