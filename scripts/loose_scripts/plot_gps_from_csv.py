# plot_gps_from_csv.py
#
# Static‑position scatter for a single /fix CSV, saving into the same run folder.
# -------------------------------------------------------------

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                        # head‑less backend
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle


def load_fix_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    needed = {"latitude", "longitude", "status.status"}
    if not needed.issubset(df.columns):
        missing = needed - set(df.columns)
        raise ValueError(f"{csv_path.name} is missing columns: {missing}")
    return df


def plot_static_scatter(df: pd.DataFrame, out_png: Path, max_distance: float):
    lat = df["latitude"].values
    lon = df["longitude"].values
    status = df["status.status"].values

    fig, ax = plt.subplots(figsize=(10, 8))

    # non‑RTK vs RTK
    rtk = status == 2
    ax.scatter(lon[~rtk], lat[~rtk], c="blue",  alpha=0.7, s=50, label="non‑RTK")
    ax.scatter(lon[rtk],  lat[rtk],  c="red",   alpha=0.9, s=70, marker="^", label="RTK fix")

    # mean position
    μlat, μlon = lat.mean(), lon.mean()

    # 95% error ellipse
    dx = (lon - μlon) * 111_320
    dy = (lat - μlat) * 110_540
    if len(dx) > 1:
        cov = np.cov(np.vstack([dx, dy]))
        vals, vecs = np.linalg.eig(cov)
        χ = np.sqrt(5.991)
        w_m, h_m = χ * np.sqrt(vals)
        angle = np.degrees(np.arctan2(vecs[1, 0], vecs[0, 0]))
        ax.add_patch(Ellipse(
            (μlon, μlat),
            width=w_m/111_320,
            height=h_m/110_540,
            angle=angle,
            fc="none", ec="black", lw=2,
            label="95 % error ellipse"
        ))

    # max‑distance circle
    ax.add_patch(Circle(
        (μlon, μlat),
        radius=max_distance/111_320,
        fc="none", ec="black", ls="--", lw=2,
        label=f"{max_distance} m radius"
    ))

    # axis limits
    lat_span = np.ptp(lat)
    lon_span = np.ptp(lon)
    ax.set_xlim(lon.min() - lon_span*0.2, lon.max() + lon_span*0.2)
    ax.set_ylim(lat.min() - lat_span*0.2, lat.max() + lat_span*0.2)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Static accuracy – position scatter")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True)
    ax.legend(fontsize=8, loc="best")

    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"Saved scatter plot to {out_png.resolve()}")


def main():
    p = argparse.ArgumentParser(
        description="Static GPS scatter plot from a /fix CSV, saved into the same run folder."
    )
    p.add_argument(
        "-i", "--csv", type=Path, required=True,
        help="Path to the ublox-fix CSV (e.g. ../run_0/ublox-fix.csv)"
    )
    p.add_argument(
        "--max-distance", type=float, default=1.0,
        help="Radius of dashed circle in metres (default: 1.0)"
    )
    args = p.parse_args()

    df = load_fix_csv(args.csv)
    run_dir = args.csv.parent
    out_png = run_dir / "static_scatter.png"

    plot_static_scatter(df, out_png, args.max_distance)


if __name__ == "__main__":
    main()
