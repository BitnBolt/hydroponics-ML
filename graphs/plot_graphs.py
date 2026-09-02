"""Generate g1-g5 graphs: task_graphs ranges/windows + reference point markers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

DATA_DIR = Path(__file__).resolve().parent / "data"
OUT_DIR = Path(__file__).resolve().parent / "output_graphs"
OUT_DIR.mkdir(exist_ok=True)

REF_ORANGE = "#E67E22"
REF_BLUE = "#2471A3"
TASK_GREEN = "#70AD47"
TASK_BLUE = "#4472C4"
LUX_YELLOW = "#FFC000"
LUX_GREEN = "#548235"
REF_GRID = "#BFBFBF"

# Task graph axis ranges (from task_graphs/)
TASK_RANGES = {
    "g1_y": (0, 120, 20),
    "g2_y": (765, 815, 5),
    "g3_y": (0, 60, 10),
    "g4_y": (0, 30000, 5000),
    "g5_y": (0, 35, 5),
}


def _apply_reference_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "font.size": 10,
            "font.family": "sans-serif",
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "axes.grid": True,
            "grid.alpha": 0.35,
            "grid.linestyle": ":",
            "axes.edgecolor": "#333333",
            "axes.linewidth": 0.9,
        }
    )


def _save(fig: plt.Figure, name: str, caption: str) -> None:
    fig.text(0.5, 0.01, caption, ha="center", va="bottom", fontsize=11, fontfamily="serif")
    out = OUT_DIR / name
    fig.savefig(out, dpi=150, bbox_inches="tight", pad_inches=0.32)
    plt.close(fig)
    print(f"Saved: {out}")


def _style_reference_axes(ax: plt.Axes, *, ygrid: bool = True, xgrid: bool = False) -> None:
    ax.set_axisbelow(True)
    if ygrid:
        ax.grid(True, which="major", axis="y", color=REF_GRID, alpha=0.45, linestyle=":")
    if xgrid:
        ax.grid(True, which="major", axis="x", color=REF_GRID, alpha=0.45, linestyle=":")
    else:
        ax.grid(False, axis="x")


def _set_y_range(ax: plt.Axes, key: str) -> None:
    lo, hi, step = TASK_RANGES[key]
    ax.set_ylim(lo, hi)
    ax.set_yticks(range(lo, hi + 1, step))


def _markevery(n: int, target: int = 60) -> int:
    return max(1, n // target)


def _plot_with_markers(
    ax: plt.Axes,
    x,
    y,
    *,
    color: str,
    marker: str = "o",
    linewidth: float = 1.6,
    markersize: float = 4,
    markevery: int = 1,
    linestyle: str = "-",
    label: str | None = None,
    **kwargs,
) -> None:
    ax.plot(
        x,
        y,
        color=color,
        linewidth=linewidth,
        linestyle=linestyle,
        marker=marker,
        markersize=markersize,
        markerfacecolor=color,
        markeredgecolor=color,
        markevery=markevery,
        label=label,
        **kwargs,
    )


def _round_green_frame(fig: plt.Figure, ax: plt.Axes) -> None:
    fig.canvas.draw()
    bbox = ax.get_position()
    fancy = FancyBboxPatch(
        (bbox.x0 - 0.012, bbox.y0 - 0.07),
        bbox.width + 0.024,
        bbox.height + 0.12,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=1.5,
        edgecolor=TASK_GREEN,
        facecolor="white",
        transform=fig.transFigure,
        clip_on=False,
        zorder=-1,
    )
    fig.patches.append(fancy)


def plot_g1_humidity() -> None:
    """Task g1: full Aug-12 day, humidity 0–120 %, excel row order (14:10 → 00:01)."""
    df = pd.read_excel(DATA_DIR / "ems_data_time_humidity.xlsx")
    df = df[df["Day_time"].astype(str).str.startswith("12/08/2025")].reset_index(drop=True)

    x = range(len(df))
    tick_step = max(1, len(df) // 55)

    fig, ax = plt.subplots(figsize=(13.5, 5.8))
    _plot_with_markers(ax, x, df["Humidity"], color=TASK_GREEN, marker="o", markevery=1, linewidth=1.3)
    ax.set_title("DHT22 Sensor", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Humidity (%)", fontsize=10)
    ax.set_xlabel("Date & Time", fontsize=10)
    _set_y_range(ax, "g1_y")
    ax.set_xticks(list(x)[::tick_step])
    ax.set_xticklabels(df["Day_time"].iloc[::tick_step], rotation=90, ha="center", fontsize=7)
    ax.set_xlim(-0.5, len(df) - 0.5)
    _style_reference_axes(ax, ygrid=True, xgrid=False)
    for spine in ax.spines.values():
        spine.set_edgecolor(TASK_GREEN)
        spine.set_linewidth(1.2)
    _round_green_frame(fig, ax)
    fig.subplots_adjust(bottom=0.28, top=0.9)
    _save(fig, "g1_humidity.png", "Figure 24: Humidity Value by DHT22 Sensor")


def plot_g2_tds() -> None:
    """Task g2: Jun-20 dense window (~69 pts), TDS y-axis 765–815."""
    df = pd.read_excel(DATA_DIR / "TDS_.xlsx")
    df["datetime"] = pd.to_datetime(df["createdAt"], utc=True).dt.tz_convert(None)
    df = (
        df[df["datetime"].dt.date == pd.Timestamp("2025-06-20").date()]
        .dropna(subset=["tds"])
        .sort_values("datetime")
        .reset_index(drop=True)
    )

    # Evenly spaced index avoids datetime-axis label overlap; one-line timestamps read cleanly when rotated.
    x = range(len(df))
    labels = df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    tick_step = max(1, len(df) // 34)

    fig, ax = plt.subplots(figsize=(13.5, 5.8))
    _plot_with_markers(
        ax,
        x,
        df["tds"],
        color=TASK_BLUE,
        marker="o",
        markevery=1,
        markersize=4,
    )
    ax.set_title("TDS Sensor", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("TDS Data", fontsize=10)
    ax.set_xlabel("Date - Time", fontsize=10)
    _set_y_range(ax, "g2_y")
    ax.set_xlim(-0.5, len(df) - 0.5)
    ax.set_xticks(list(x)[::tick_step])
    ax.set_xticklabels(labels.iloc[::tick_step], rotation=90, ha="center", va="top", fontsize=6)
    _style_reference_axes(ax, ygrid=True, xgrid=False)
    fig.subplots_adjust(bottom=0.38, top=0.9)
    _save(fig, "g2_tds.png", "Figure 22: TDS Value from EC Sensor")


def plot_g3_temperature() -> None:
    """Task g3: Jun-20 → Aug-08, temp y-axis 0–60, line graph only."""
    df = pd.read_excel(DATA_DIR / "ems_data_time_temp.xlsx")
    df["datetime"] = pd.to_datetime(df["Date_Time"])
    df = df.dropna(subset=["datetime", "Temp"]).sort_values("datetime")

    fig, ax = plt.subplots(figsize=(13.5, 5.8))
    _plot_with_markers(
        ax,
        df["datetime"],
        df["Temp"],
        color=TASK_GREEN,
        marker="o",
        markevery=_markevery(len(df), 70),
        linewidth=1.6,
        markersize=3,
    )

    ax.set_title("DHT22 Sensor", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Temperature (Celcius)", fontsize=10)
    ax.set_xlabel("Date & Time", fontsize=10)
    _set_y_range(ax, "g3_y")
    ax.set_xlim(df["datetime"].min(), df["datetime"].max())
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%Y %H:%M:%S"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
    _style_reference_axes(ax, ygrid=True, xgrid=False)
    fig.subplots_adjust(bottom=0.22, top=0.9)
    _save(fig, "g3_temperature.png", "Figure 23: Temperature Value by DHT22 Sensor")


def plot_g4_lux() -> None:
    """Task g4: single day, LUX 0–30000, evening (left) → morning (right)."""
    df = pd.read_excel(DATA_DIR / "LMS.xlsx")
    df["Time"] = df["Time"].astype(str).str.strip()
    df["datetime"] = pd.to_datetime(
        df["Date"].dt.strftime("%Y-%m-%d") + " " + df["Time"],
        format="%Y-%m-%d %I:%M:%S %p",
        errors="coerce",
    )
    df = df.dropna(subset=["datetime"]).sort_values("datetime", ascending=False).reset_index(drop=True)

    x = range(len(df))
    tick_step = max(1, len(df) // 28)

    fig, ax = plt.subplots(figsize=(13.5, 5.8))
    _plot_with_markers(
        ax, x, df["BH1750"],
        color=LUX_YELLOW, marker="o", markevery=_markevery(len(df), 30),
        label="Bh1750 Sensor (lux)",
    )
    _plot_with_markers(
        ax, x, df["TSL2591"],
        color=LUX_GREEN, marker="o", markevery=_markevery(len(df), 30),
        label="TSL2591 Sensor (lux)",
    )

    ax.set_title("Comparitive LUX value", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("LUX", fontsize=10)
    ax.set_xlabel("TIME (HR:MIN:SEC)\n09-08-2025", fontsize=10)
    _set_y_range(ax, "g4_y")
    ax.set_xticks(list(x)[::tick_step])
    ax.set_xticklabels(
        df["datetime"].iloc[::tick_step].dt.strftime("%I:%M:%S %p"),
        rotation=90,
        ha="center",
        fontsize=8,
    )
    ax.set_xlim(-0.5, len(df) - 0.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.11), ncol=2, frameon=False, fontsize=9)
    _style_reference_axes(ax, ygrid=True, xgrid=False)
    fig.subplots_adjust(bottom=0.28, top=0.82)
    _save(fig, "g4_lux.png", "Figure 25: LUX readings from BH1750 and TSL2591 Sensors")


def plot_g5_water_temperature() -> None:
    """Task g5: datetime x-axis, y 0–35; tick labels at even time steps (not every Nth row)."""
    df = pd.read_excel(DATA_DIR / "Water Temperature.xlsx")
    df["datetime"] = pd.to_datetime(df["createdAt"], utc=True).dt.tz_convert(None)
    df = df.dropna(subset=["datetime", "waterTemp"]).sort_values("datetime").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(13.5, 5.8))
    _plot_with_markers(
        ax,
        df["datetime"],
        df["waterTemp"],
        color=TASK_BLUE,
        marker="o",
        markevery=1,
        markersize=2.5,
        linewidth=0.8,
        rasterized=True,
    )

    ax.set_title("DS18B20 Sensor", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Nutrient Temperature", fontsize=10)
    ax.set_xlabel("Date - Time", fontsize=10)
    _set_y_range(ax, "g5_y")
    ax.set_xlim(df["datetime"].min(), df["datetime"].max())

    def _iso_ms(_dt, _pos):
        dt = mdates.num2date(_dt).replace(tzinfo=None)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"

    ax.xaxis.set_major_locator(mdates.DayLocator(interval=4))
    ax.xaxis.set_major_formatter(_iso_ms)
    plt.setp(ax.get_xticklabels(), rotation=90, ha="center", va="top", fontsize=6)
    _style_reference_axes(ax, ygrid=True, xgrid=False)
    fig.subplots_adjust(bottom=0.38, top=0.9)
    _save(fig, "g5_water_temperature.png", "Figure 21: Nutrient Temperature from DS18B20 Sensor")


def main() -> None:
    _apply_reference_style()
    print("Output folder:", OUT_DIR.resolve())
    plot_g1_humidity()
    plot_g2_tds()
    plot_g3_temperature()
    plot_g4_lux()
    plot_g5_water_temperature()
    print("Done.")


if __name__ == "__main__":
    main()
