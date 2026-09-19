from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from shapely import contains_xy
from shapely.geometry import Polygon
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "plan1_geometry.json"
FIG_DIR = ROOT / "output" / "figures"
RESULT_DIR = ROOT / "output" / "results"
INTERMEDIATE_DIR = ROOT / "output" / "intermediate"


def load_geometry():
    with CONFIG.open(encoding="utf-8") as f:
        cfg = json.load(f)
    slab = Polygon(cfg["outline"])
    slab = unary_union([slab, *(Polygon(p) for p in cfg["additions"])])
    openings = unary_union([Polygon(p) for p in cfg["openings"]])
    net = slab.difference(openings)
    return cfg, slab, openings, net


def segment_distance(x, y, start, end):
    ax, ay = start
    bx, by = end
    vx, vy = bx - ax, by - ay
    denom = vx * vx + vy * vy
    t = np.clip(((x - ax) * vx + (y - ay) * vy) / denom, 0.0, 1.0)
    return np.hypot(x - (ax + t * vx), y - (ay + t * vy))


def label_point(element):
    if "point" in element:
        return element["point"]
    a, b = element["start"], element["end"]
    return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]


def main():
    cfg, gross, openings, net = load_geometry()
    for folder in (FIG_DIR, RESULT_DIR, INTERMEDIATE_DIR):
        folder.mkdir(parents=True, exist_ok=True)

    grid = cfg["analysis"]["grid_m"]
    xmin, ymin, xmax, ymax = net.bounds
    xs = np.arange(xmin + grid / 2, xmax, grid)
    ys = np.arange(ymin + grid / 2, ymax, grid)
    xx, yy = np.meshgrid(xs, ys)
    inside = contains_xy(net, xx, yy)
    px, py = xx[inside], yy[inside]

    elements = []
    for col in cfg["columns"]:
        item = {**col, "type": "Column"}
        elements.append(item)
    for wall in cfg["walls"]:
        item = {**wall, "type": "Wall"}
        elements.append(item)

    distances = []
    for e in elements:
        if e["type"] == "Column":
            distances.append(np.hypot(px - e["point"][0], py - e["point"][1]))
        else:
            distances.append(segment_distance(px, py, e["start"], e["end"]))
    owner = np.argmin(np.vstack(distances), axis=0)
    raster_areas = np.bincount(owner, minlength=len(elements)) * grid * grid
    # Normalize the minute boundary-cell discrepancy so that global equilibrium is exact.
    areas = raster_areas * (net.area / raster_areas.sum())

    loads = cfg["loads"]
    qd = loads["slab_thickness_m"] * loads["concrete_unit_weight_kN_m3"]
    ql = loads["live_load_kN_m2"]
    nstoreys = loads["storeys"]
    rows = []
    for e, area in zip(elements, areas):
        x, y = label_point(e)
        dead = area * qd
        live = area * ql
        total = dead + live
        rows.append({
            "id": e["id"], "type": e["type"], "size_mm": e["size_mm"],
            "x_m": x, "y_m": y, "tributary_area_m2": area,
            "dead_load_1floor_kN": dead, "live_load_1floor_kN": live,
            "total_load_1floor_kN": total, "base_load_5storey_kN": total * nstoreys,
        })

    fieldnames = list(rows[0])
    with (RESULT_DIR / "element_loads.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (f"{v:.3f}" if isinstance(v, float) else v) for k, v in row.items()})

    level_fields = ["level", "floors_supported", "dead_kN", "live_kN", "total_kN"]
    with (RESULT_DIR / "building_level_totals.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=level_fields)
        writer.writeheader()
        for level, mult in zip(["Roof/F5", "F4", "F3", "F2", "F1/Base"], range(1, 6)):
            writer.writerow({
                "level": level, "floors_supported": mult,
                "dead_kN": f"{net.area * qd * mult:.3f}",
                "live_kN": f"{net.area * ql * mult:.3f}",
                "total_kN": f"{net.area * (qd + ql) * mult:.3f}",
            })

    geometry_export = {
        "source_config": str(CONFIG.relative_to(ROOT)),
        "gross_area_m2": round(gross.area, 6),
        "opening_area_m2": round(openings.area, 6),
        "net_floor_area_m2": round(net.area, 6),
        "raster_cell_m": grid,
        "raster_area_before_normalization_m2": round(float(raster_areas.sum()), 6),
        "area_closure_error_before_normalization_percent": round(
            100 * (float(raster_areas.sum()) - net.area) / net.area, 6
        ),
        "elements": elements,
    }
    with (INTERMEDIATE_DIR / "geometry_plan1.json").open("w", encoding="utf-8") as f:
        json.dump(geometry_export, f, indent=2, ensure_ascii=False)

    plot_geometry(cfg, gross, openings, net, elements)
    plot_tributaries(cfg, gross, openings, elements, xx, yy, inside, owner)
    plot_loads(rows)

    checks = {
        "net_area_m2": net.area,
        "sum_tributary_area_m2": float(areas.sum()),
        "area_difference_m2": float(areas.sum() - net.area),
        "dead_load_sum_kN": sum(r["dead_load_1floor_kN"] for r in rows),
        "dead_load_global_kN": net.area * qd,
        "live_load_sum_kN": sum(r["live_load_1floor_kN"] for r in rows),
        "live_load_global_kN": net.area * ql,
    }
    with (RESULT_DIR / "verification.json").open("w", encoding="utf-8") as f:
        json.dump(checks, f, indent=2)
    print(json.dumps(checks, indent=2))


def draw_polygon(ax, geom, **kwargs):
    geoms = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
    for part in geoms:
        x, y = part.exterior.xy
        ax.fill(x, y, **kwargs)


def plot_geometry(cfg, gross, openings, net, elements):
    fig, ax = plt.subplots(figsize=(8.2, 10.0), constrained_layout=True)
    draw_polygon(ax, gross, facecolor="#edf4fb", edgecolor="#204a6b", linewidth=2)
    draw_polygon(ax, openings, facecolor="white", edgecolor="#d1495b", linewidth=1.6, hatch="//")
    for e in elements:
        if e["type"] == "Column":
            x, y = e["point"]
            ax.scatter(x, y, s=55, marker="s", color="#173f5f", zorder=4)
        else:
            a, b = e["start"], e["end"]
            ax.plot([a[0], b[0]], [a[1], b[1]], color="#e07a5f", linewidth=5, solid_capstyle="round")
        x, y = label_point(e)
        ax.text(x + 0.10, y + 0.10, e["id"], fontsize=8, weight="bold")
    ax.set_title("Digitized Floor Outline and Vertical Elements - Floor Plan 1", weight="bold")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_aspect("equal")
    ax.grid(alpha=0.18)
    ax.text(0.02, 0.01, f"Net slab area = {net.area:.2f} m²", transform=ax.transAxes,
            bbox=dict(facecolor="white", edgecolor="#204a6b", alpha=0.9))
    fig.savefig(FIG_DIR / "01_extracted_geometry.png", dpi=220)
    plt.close(fig)


def plot_tributaries(cfg, gross, openings, elements, xx, yy, inside, owner):
    label_grid = np.full(xx.shape, np.nan)
    label_grid[inside] = owner
    cmap = ListedColormap(plt.cm.tab20(np.linspace(0, 1, len(elements))))
    fig, ax = plt.subplots(figsize=(8.2, 10.0), constrained_layout=True)
    ax.pcolormesh(xx, yy, label_grid, cmap=cmap, shading="nearest", alpha=0.62)
    draw_polygon(ax, openings, facecolor="white", edgecolor="#333", linewidth=1.2, hatch="//")
    for e in elements:
        x, y = label_point(e)
        ax.text(x, y, e["id"], ha="center", va="center", fontsize=8, weight="bold",
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="#333", alpha=0.9))
    ax.set_title("Nearest-Support Tributary Area Partition", weight="bold")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_aspect("equal")
    ax.set_xlim(gross.bounds[0] - 0.3, gross.bounds[2] + 0.3)
    ax.set_ylim(gross.bounds[1] - 0.3, gross.bounds[3] + 0.3)
    fig.savefig(FIG_DIR / "02_tributary_areas.png", dpi=220)
    plt.close(fig)


def plot_loads(rows):
    ids = [r["id"] for r in rows]
    dead = np.array([r["dead_load_1floor_kN"] for r in rows])
    live = np.array([r["live_load_1floor_kN"] for r in rows])
    x = np.arange(len(ids))
    fig, ax = plt.subplots(figsize=(10.5, 5.2), constrained_layout=True)
    ax.bar(x, dead, label="Dead load", color="#3d5a80")
    ax.bar(x, live, bottom=dead, label="Live load", color="#ee6c4d")
    ax.set_xticks(x, ids)
    ax.set_ylabel("One-floor axial load (kN)")
    ax.set_title("Gravity Load Assigned to Each Vertical Element", weight="bold")
    ax.legend(frameon=False, ncol=2)
    ax.grid(axis="y", alpha=0.2)
    fig.savefig(FIG_DIR / "03_element_loads.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    main()

