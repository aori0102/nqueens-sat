import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ---- config ----
CSV_PATH = "benchmark_results.csv"
SAT_METHODS = ["Pairwise", "Binary", "Sequential", "Commander", "Product"]
EXACT_METHODS = ["CPLEX_MIP", "GUROBI_MIP", "CP_SAT", "CPLEX_CP"]
METHODS = SAT_METHODS + EXACT_METHODS
BEST_SAT = "Best SAT"
STRUCTURE_REPORT_EXCLUDED_METHODS = {"CPLEX_MIP", "CPLEX_CP", "CP_SAT", "GUROBI_MIP"}
METHOD_COL = "Method Name"
RESULT_COL = "Result"
X_COL = "Board Size"
SOLVE_COL = "Solve Time"
CLAUSES_COL = "Num Clauses"
VARIABLES_COL = "Num Variables"

OK_RESULTS = {"SAT", "SOLVED"}            # filled dot, connected by lines
UNFILLED_RESULTS = {"UNSAT", "UNSOLVED"}  # hollow dot, no line
TIMEOUT_LABEL = "TIMEOUT"                 # triangle, no line
# anything else (ERROR, NaN, ...)         -> x, no line

SOLVE_CAP = 100   # seconds, all solve times clipped to this
Y_PAD = 1.05      # headroom so markers at the cap aren't cut in half (set 1 for a hard ceiling)
LOG_Y_SOLVE = False
LOG_Y_SIZES = False

# stable colors across every plot (index 9 is free for "Best SAT")
_cmap = plt.get_cmap("tab10")
COLORS = {m: _cmap(i % 10) for i, m in enumerate(METHODS)}
COLORS[BEST_SAT] = _cmap(9)

STATUS_RANK = {"ok": 0, "unfilled": 1, "timeout": 2, "error": 3}


def classify(result):
    r = str(result).strip().upper()
    if r in OK_RESULTS:
        return "ok"
    if r in UNFILLED_RESULTS:
        return "unfilled"
    if r == TIMEOUT_LABEL:
        return "timeout"
    return "error"


def build_frame(df, y_col, is_solve):
    """One row per (method, n): y value + status."""
    df = df.copy()
    df["status"] = df[RESULT_COL].map(classify)
    if is_solve:
        df["y"] = df[y_col].clip(upper=SOLVE_CAP)
        df.loc[df["status"] == "timeout", "y"] = SOLVE_CAP  # timeouts sit at the cap
    else:
        # timeouts log 0 and CPLEX has no clauses/vars -> nothing real to place
        df["y"] = df[y_col].where(df[y_col] > 0)
    df = df.dropna(subset=["y"])
    return (df.groupby([METHOD_COL, X_COL])
              .agg(y=("y", "median"), status=("status", lambda s: s.mode().iat[0]))
              .reset_index())


def collapse_best_sat(frame):
    """Replace all SAT encoder rows with one 'Best SAT' row per board size.
    Best = best status class first (ok > unfilled > timeout > error), then lowest y."""
    is_sat = frame[METHOD_COL].isin(SAT_METHODS)
    sat = frame[is_sat].copy()
    sat["rank"] = sat["status"].map(STATUS_RANK)
    best = (sat.sort_values(["rank", "y"])
               .drop_duplicates(subset=X_COL, keep="first")
               .drop(columns="rank"))
    best[METHOD_COL] = BEST_SAT
    return pd.concat([frame[~is_sat], best], ignore_index=True)


def plot_report(df, y_col, title, ylabel, out_name, is_solve, logy,
                methods=None, collapse_sat=False):
    sizes = sorted(df[X_COL].unique())          # actual n values, evenly spaced on the axis
    pos = {n: i for i, n in enumerate(sizes)}
    frame = build_frame(df, y_col, is_solve)
    if collapse_sat:
        frame = collapse_best_sat(frame)
    if frame.empty:
        print(f"Nothing to plot for '{y_col}'")
        return

    if methods is None:
        methods = METHODS
    present = set(frame[METHOD_COL])
    methods = [m for m in methods if m in present]
    if not methods:
        print(f"Nothing to plot for '{out_name}'")
        return

    lookup = {(m, n): (y, s) for m, n, y, s in
              zip(frame[METHOD_COL], frame[X_COL], frame["y"], frame["status"])}

    fig, ax = plt.subplots(figsize=(11, 6))
    for m in methods:
        color = COLORS[m]
        run = []  # consecutive "ok" points get connected, anything else breaks the line
        for n in sizes:
            pt = lookup.get((m, n))
            status = pt[1] if pt else None
            if status == "ok":
                run.append((pos[n], pt[0]))
            else:
                if len(run) > 1:
                    ax.plot(*zip(*run), color=color, linewidth=1.5, zorder=2)
                run = []
            if pt is None:
                continue
            marker, mfc = {"ok": ("o", color), "unfilled": ("o", "none"),
                           "timeout": ("^", color), "error": ("x", color)}[status]
            ax.plot([pos[n]], [pt[0]], linestyle="none", marker=marker, color=color,
                    markerfacecolor=mfc, markersize=8, markeredgewidth=1.5,
                    clip_on=False, zorder=3)
        if len(run) > 1:
            ax.plot(*zip(*run), color=color, linewidth=1.5, zorder=2)

    ax.set_xticks(range(len(sizes)))
    ax.set_xticklabels([str(n) for n in sizes])
    ax.set_xlim(-0.4, len(sizes) - 0.6)
    if logy:
        ax.set_yscale("log")
    if is_solve:
        ax.set_ylim(top=SOLVE_CAP * Y_PAD, **({} if logy else {"bottom": 0}))
    ax.set_xlabel(X_COL)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    method_handles = [Line2D([], [], color=COLORS[m], marker="o", label=m) for m in methods]
    status_labels = ("SAT", "UNSAT") if not is_solve else ("SAT / solved", "UNSAT / unsolved")
    status_handles = [
        Line2D([], [], color="gray", marker="o", linestyle="none", label=status_labels[0]),
        Line2D([], [], color="gray", marker="o", markerfacecolor="none", linestyle="none", label=status_labels[1]),
        Line2D([], [], color="gray", marker="^", linestyle="none", label="Timeout"),
        Line2D([], [], color="gray", marker="x", linestyle="none", label="Error"),
    ]
    first = ax.legend(handles=method_handles, title="Method", loc="upper left", bbox_to_anchor=(1.01, 1))
    ax.add_artist(first)
    ax.legend(handles=status_handles, title="Result", loc="lower left", bbox_to_anchor=(1.01, 0))

    plt.tight_layout()
    plt.savefig(out_name, dpi=150, bbox_inches="tight")
    plt.show()


def main():
    df = pd.read_csv(CSV_PATH)

    missing = [m for m in METHODS if m not in df[METHOD_COL].unique()]
    if missing:
        print(f"Warning: not found in '{METHOD_COL}': {missing}")

    df = df[df[METHOD_COL].isin(METHODS)]

    # 1) solve time: SAT encoders only
    plot_report(df, SOLVE_COL, f"{SOLVE_COL} by {X_COL}: SAT encoders (capped at {SOLVE_CAP}s)",
                f"{SOLVE_COL} (s)", "solve_time_sat_encoders.png",
                is_solve=True, logy=LOG_Y_SOLVE, methods=SAT_METHODS)

    # 2) solve time: best SAT encoder vs exact solvers
    plot_report(df, SOLVE_COL, f"{SOLVE_COL} by {X_COL}: best SAT vs exact solvers (capped at {SOLVE_CAP}s)",
                f"{SOLVE_COL} (s)", "solve_time_best_sat_vs_exact.png",
                is_solve=True, logy=LOG_Y_SOLVE,
                methods=[BEST_SAT] + EXACT_METHODS, collapse_sat=True)

    # 3) + 4) clauses / variables: unchanged (CPLEX/CP-SAT/Gurobi excluded)
    structure_methods = [m for m in METHODS if m not in STRUCTURE_REPORT_EXCLUDED_METHODS]
    plot_report(df, CLAUSES_COL, f"{CLAUSES_COL} by {X_COL}", CLAUSES_COL,
                "clauses_report.png", is_solve=False, logy=LOG_Y_SIZES, methods=structure_methods)
    plot_report(df, VARIABLES_COL, f"{VARIABLES_COL} by {X_COL}", VARIABLES_COL,
                "variables_report.png", is_solve=False, logy=LOG_Y_SIZES, methods=structure_methods)


if __name__ == "__main__":
    main()