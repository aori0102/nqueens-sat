import pandas as pd
import matplotlib.pyplot as plt

# ---- config ----
CSV_PATH = "benchmark_results.csv"
METHODS = ["CPLEX_CP", "Binary", "Sequential", "Commander"]  # values in the method column to plot as series
METHOD_COL = "Method Name"
RESULT_COL = "Result"
TIMEOUT_LABEL = "TIMEOUT"
X_COL = "Board Size"
Y_COL = "Solve Time"
LOG_Y = False  # flip to True if the times span orders of magnitude
HEADROOM = 1.15  # y axis top = slowest non-timeout time * this


def main():
    df = pd.read_csv(CSV_PATH)

    missing = [m for m in METHODS if m not in df[METHOD_COL].unique()]
    if missing:
        print(f"Warning: not found in '{METHOD_COL}': {missing}")

    df = df[df[METHOD_COL].isin(METHODS)].copy()

    # y axis is capped at the slowest *real* time, timeouts get pushed way past it
    is_timeout = df[RESULT_COL] == TIMEOUT_LABEL
    y_top = df.loc[~is_timeout, Y_COL].max() * HEADROOM
    df.loc[is_timeout, Y_COL] = y_top * 10  # off the chart, the line shoots out the top

    # one column per method, indexed by board size
    # aggfunc="median" so repeated runs of the same (method, size) collapse cleanly
    pivot = df.pivot_table(index=X_COL, columns=METHOD_COL, values=Y_COL, aggfunc="median")
    pivot = pivot[[m for m in METHODS if m in pivot.columns]]  # keep the order of METHODS

    ax = pivot.plot(marker="o", figsize=(10, 6), logy=LOG_Y)
    ax.set_ylim(top=y_top)  # clip so timeouts exit through the roof
    if not LOG_Y:
        ax.set_ylim(bottom=0)
    ax.set_xlabel(X_COL)
    ax.set_ylabel(f"{Y_COL} (s)")
    ax.set_title(f"{Y_COL} by {X_COL} (line leaves the chart = timeout)")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("report.png", dpi=150)
    plt.show()


if __name__ == "__main__":
    main()