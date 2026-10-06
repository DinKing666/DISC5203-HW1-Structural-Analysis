from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from shapely import contains_xy

from analyze_floor_plan import load_geometry


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "hw2_beams.json"
FIG_DIR = ROOT / "output" / "figures"
RESULT_DIR = ROOT / "output" / "results"
INTERMEDIATE_DIR = ROOT / "output" / "intermediate"


def beam_inventory(cfg):
    xs = cfg["grid_x_m"]
    ys = cfg["grid_y_m"]
    panels = cfg["panel_labels_bottom_to_top"]
    beams = []
    for j, y in enumerate(ys):
        for i in range(len(xs) - 1):
            bordering = []
            if j > 0:
                bordering.append(panels[j - 1][i])
            if j < len(ys) - 1:
                bordering.append(panels[j][i])
            if j == 0:
                bordering.append("P10 (cantilever balcony where overlapping)")
            if j == len(ys) - 1:
                bordering.append("P11 (cantilever balcony where overlapping)")
            beams.append({
                "id": f"H{j}-{i+1}", "orientation": "H",
                "start": [xs[i], y], "end": [xs[i + 1], y],
                "grid": f"y={y:.2f} m, x-grid {i}-{i+1}",
                "panels": bordering,
            })
    for i, x in enumerate(xs):
        for j in range(len(ys) - 1):
            bordering = []
            if i > 0:
                bordering.append(panels[j][i - 1])
            if i < len(xs) - 1:
                bordering.append(panels[j][i])
            beams.append({
                "id": f"V{i}-{j+1}", "orientation": "V",
                "start": [x, ys[j]], "end": [x, ys[j + 1]],
                "grid": f"x={x:.2f} m, y-grid {j}-{j+1}",
                "panels": bordering,
            })
    for b in beams:
        a = np.asarray(b["start"], dtype=float)
        c = np.asarray(b["end"], dtype=float)
        b["length_m"] = float(np.linalg.norm(c - a))
        sides = 1 if b["orientation"] == "V" and (b["id"].startswith("V0-") or b["id"].startswith("V3-")) else 2
        if b["id"].startswith("H0-") or b["id"].startswith("H3-"):
            b["load_shape"] = "two-way triangle/trapezoid + balcony cantilever UDL"
            b["support_class"] = "two loaded sides locally (main slab + balcony)"
        elif sides == 1:
            b["load_shape"] = "one-sided triangle/trapezoid"
            b["support_class"] = "perimeter, slab on one side"
        else:
            b["load_shape"] = "two-sided superposed triangle/trapezoid"
            b["support_class"] = "interior, slab on both sides"
    return beams


def distance_to_segment(x, y, start, end):
    x1, y1 = start
    x2, y2 = end
    xmin, xmax = sorted((x1, x2))
    ymin, ymax = sorted((y1, y2))
    dx = np.maximum.reduce((xmin - x, np.zeros_like(x), x - xmax))
    dy = np.maximum.reduce((ymin - y, np.zeros_like(y), y - ymax))
    return np.hypot(dx, dy)


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_partition(gross, openings, xx, yy, inside, owner, beams):
    labels = np.full(xx.shape, np.nan)
    labels[inside] = owner
    colors = plt.cm.tab20(np.linspace(0, 1, len(beams)))
    colors[:, :3] = 0.72 * colors[:, :3] + 0.28
    fig, ax = plt.subplots(figsize=(8.3, 10.5), constrained_layout=True)
    ax.pcolormesh(xx, yy, labels, shading="nearest", cmap=ListedColormap(colors), alpha=0.70, rasterized=True)
    for b in beams:
        x = [b["start"][0], b["end"][0]]
        y = [b["start"][1], b["end"][1]]
        marked_a = b["id"] in {"V0-1", "V0-2", "V0-3"}
        marked_b = b["id"] in {"H1-1", "H1-2", "H1-3"}
        color = "#d62828" if (marked_a or marked_b) else "#263238"
        ax.plot(x, y, color=color, lw=2.4 if (marked_a or marked_b) else 1.0, zorder=5)
        ax.text(np.mean(x), np.mean(y), b["id"], fontsize=6.5, ha="center", va="center",
                bbox=dict(facecolor="white", edgecolor="none", alpha=.75, pad=.5), zorder=6)
    for geom, face, edge in [(gross, "none", "#111111"), (openings, "white", "#111111")]:
        parts = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
        for p in parts:
            x, y = p.exterior.xy
            ax.fill(x, y, facecolor=face, edgecolor=edge, linewidth=1.2, hatch="//" if face == "white" else None)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("HW2 Beam Tributary Areas - Nearest-Edge 45-degree Construction", weight="bold")
    ax.legend(handles=[
        Line2D([0], [0], color="#d62828", lw=2.5, label="Marked Beam A / Beam B"),
        Line2D([0], [0], color="#263238", lw=1.2, label="Other beam segment"),
        Line2D([0], [0], color="#246b91", lw=5, alpha=.35, label="Tributary ownership field"),
    ], loc="upper center", bbox_to_anchor=(.5, -.055), ncol=3, frameon=False, fontsize=8)
    fig.savefig(FIG_DIR / "hw2_01_beam_tributary_areas.png", dpi=220)
    plt.close(fig)


def plot_summary(rows):
    ids = [r["beam_id"] for r in rows]
    dead = np.array([float(r["dead_eq_kN_m"]) for r in rows])
    live = np.array([float(r["live_eq_kN_m"]) for r in rows])
    fig, ax = plt.subplots(figsize=(12, 5.5), constrained_layout=True)
    x = np.arange(len(ids))
    ax.bar(x, dead, color="#3d5a80", label="Dead")
    ax.bar(x, live, bottom=dead, color="#ee6c4d", label="Live")
    ax.set_xticks(x, ids, rotation=55, ha="right")
    ax.set_ylabel("Equivalent UDL by total load (kN/m)")
    ax.set_title("All Beam Segments - Slab Line Loads", weight="bold")
    ax.grid(axis="y", alpha=.2)
    ax.legend(frameon=False, ncol=2)
    fig.savefig(FIG_DIR / "hw2_02_all_beam_line_loads.png", dpi=220)
    plt.close(fig)


def marked_profile(mark, cfg, profiles):
    ids = cfg["marked_beams"][mark]["segments"]
    data = []
    offset = 0.0
    supports = [0.0]
    for bid in ids:
        p = profiles[bid]
        s = np.asarray(p["s_centres_m"]) + offset
        for k, sval in enumerate(s):
            data.append((sval, p["dead_kN_m"][k], p["live_kN_m"][k], p["total_kN_m"][k], bid))
        offset += p["length_m"]
        supports.append(offset)
    return data, supports


def plot_marked_profiles(cfg, profiles):
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 7.2), constrained_layout=True)
    for ax, mark in zip(axes, ["A", "B"]):
        data, supports = marked_profile(mark, cfg, profiles)
        s = np.array([d[0] for d in data])
        dead = np.array([d[1] for d in data])
        live = np.array([d[2] for d in data])
        total = np.array([d[3] for d in data])
        ax.plot(s, total, color="#bc4749", lw=2.2, label="Total")
        ax.plot(s, dead, color="#386641", lw=1.3, label="Dead")
        ax.plot(s, live, color="#457b9d", lw=1.3, label="Live")
        for x in supports:
            ax.axvline(x, color="#555", lw=.7, ls="--", alpha=.7)
        ax.fill_between(s, 0, total, color="#bc4749", alpha=.12)
        ax.set_ylabel("Line load (kN/m)")
        ax.set_title(f"Beam {mark}: frozen 45-degree tributary line-load profile", weight="bold")
        ax.grid(alpha=.18)
        ax.legend(frameon=False, ncol=3)
    axes[-1].set_xlabel("Distance along marked beam (m)")
    fig.savefig(FIG_DIR / "hw2_03_marked_beam_load_profiles.png", dpi=220)
    plt.close(fig)


def plot_hand_bounds(cfg, profiles):
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.5), constrained_layout=True)
    for row, mark in enumerate(["A", "B"]):
        ids = cfg["marked_beams"][mark]["segments"]
        lengths = [profiles[i]["length_m"] for i in ids]
        qmeans = [float(np.mean(profiles[i]["total_kN_m"])) for i in ids]
        simple = [q*l*l/8 for q, l in zip(qmeans, lengths)]
        fixed = [q*l*l/12 for q, l in zip(qmeans, lengths)]
        ax = axes[row, 0]
        x0 = 0.0
        for k, l in enumerate(lengths):
            x = np.linspace(x0, x0+l, 80)
            local = (x-x0)/l
            y = -0.9*np.sin(np.pi*local) + .18*np.sin(2*np.pi*local)
            ax.plot(x, y, color="#2b2d42", lw=2)
            ax.plot([x0, x0+l], [0, 0], color="#aaa", lw=.6)
            x0 += l
        for x in np.cumsum([0]+lengths):
            ax.plot(x, 0, marker="^", color="#606c38", ms=7)
        ax.axhline(0, color="#777", lw=.6)
        ax.set_title(f"Beam {mark} pre-solve curvature sketch")
        ax.set_ylabel("Downward deflection (schematic)")
        ax.set_yticks([])
        ax = axes[row, 1]
        pos = np.arange(len(lengths))
        ax.bar(pos-.18, simple, .36, label="qL2/8 simple bound", color="#dda15e")
        ax.bar(pos+.18, fixed, .36, label="qL2/12 fixed scale", color="#606c38")
        ax.set_xticks(pos, [f"Span {i+1}" for i in pos])
        ax.set_ylabel("Moment scale (kN m)")
        ax.set_title(f"Beam {mark} hand moment envelope")
        ax.grid(axis="y", alpha=.2)
        ax.legend(frameon=False, fontsize=8)
    fig.savefig(FIG_DIR / "hw2_04_hand_bounds_and_sketches.png", dpi=220)
    plt.close(fig)


def main():
    with CONFIG.open(encoding="utf-8") as f:
        cfg = json.load(f)
    _, gross, openings, net = load_geometry()
    beams = beam_inventory(cfg)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

    cell = cfg["analysis"]["tributary_cell_m"]
    xmin, ymin, xmax, ymax = net.bounds
    xs = np.arange(xmin + cell/2, xmax, cell)
    ys = np.arange(ymin + cell/2, ymax, cell)
    xx, yy = np.meshgrid(xs, ys)
    inside = contains_xy(net, xx, yy)
    px, py = xx[inside], yy[inside]
    owner = np.zeros(px.size, dtype=np.int16)
    minimum = np.full(px.size, np.inf)
    for idx, b in enumerate(beams):
        d = distance_to_segment(px, py, b["start"], b["end"])
        update = d < minimum
        minimum[update] = d[update]
        owner[update] = idx

    raw_area = px.size * cell * cell
    factor = net.area / raw_area
    qd = cfg["loads"]["slab_thickness_m"] * cfg["loads"]["concrete_unit_weight_kN_m3"] + cfg["loads"]["superimposed_dead_load_kN_m2"]
    ql = cfg["loads"]["live_load_kN_m2"]
    nbins = cfg["analysis"]["profile_bins_per_segment"]
    profiles = {}
    table_rows = []
    for idx, b in enumerate(beams):
        selected = owner == idx
        bx, by = px[selected], py[selected]
        length = b["length_m"]
        if b["orientation"] == "H":
            along = bx - b["start"][0]
        else:
            along = by - b["start"][1]
        # Corner/edge overhang cells can project just beyond a beam endpoint but
        # still belong to that finite segment.  Retain them in the end bin so
        # the line-load integration closes to the complete reused HW1 slab.
        along = np.clip(along, 0.0, np.nextafter(length, 0.0))
        counts, edges = np.histogram(along, bins=nbins, range=(0, length))
        bin_width = length/nbins
        raw_widths = counts * cell * cell * factor / bin_width
        # Suppress harmless cell/bin aliasing while preserving the exact area
        # under every profile.  The physical 45-degree envelopes are smooth;
        # the alternating teeth otherwise visible are only raster sampling.
        padded = np.pad(raw_widths, (2, 2), mode="edge")
        widths = np.convolve(padded, np.ones(5)/5, mode="valid")
        if widths.sum() > 0:
            widths *= raw_widths.sum()/widths.sum()
        centres = (edges[:-1] + edges[1:]) / 2
        area = float(counts.sum() * cell * cell * factor)
        dead = qd * area / length
        live = ql * area / length
        profiles[b["id"]] = {
            "beam_id": b["id"], "start": b["start"], "end": b["end"],
            "orientation": b["orientation"], "length_m": length,
            "s_centres_m": centres.tolist(), "tributary_width_m": widths.tolist(),
            "dead_kN_m": (qd*widths).tolist(), "live_kN_m": (ql*widths).tolist(),
            "total_kN_m": ((qd+ql)*widths).tolist(),
        }
        table_rows.append({
            "beam_id": b["id"], "location_grid": b["grid"],
            "start_m": f"({b['start'][0]:.2f},{b['start'][1]:.2f})",
            "end_m": f"({b['end'][0]:.2f},{b['end'][1]:.2f})",
            "span_m": f"{length:.3f}", "depth_m": "0.600 assumed",
            "bordering_panels": "; ".join(b["panels"]),
            "support_class": b["support_class"], "load_shape": b["load_shape"],
            "tributary_area_m2": f"{area:.3f}", "mean_tributary_width_m": f"{area/length:.3f}",
            "dead_eq_kN_m": f"{dead:.3f}", "live_eq_kN_m": f"{live:.3f}",
            "total_eq_kN_m": f"{dead+live:.3f}",
            "equivalence_basis": "same total load; exact profile retained for OpenSees and moment shape"
        })

    write_csv(RESULT_DIR / "hw2_beam_line_loads.csv", table_rows)
    payload = {
        "method": "Nearest finite beam edge within reused HW1 net slab; perpendicular equal-distance loci are 45-degree bisectors",
        "area_loads_kN_m2": {"dead": qd, "live": ql, "total": qd+ql},
        "raster_cell_m": cell, "normalization_factor": factor,
        "profiles": profiles,
    }
    (RESULT_DIR / "hw2_beam_profiles.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    geometry_payload = {"beams": beams, "marked_beams": cfg["marked_beams"], "net_slab_area_m2": net.area}
    (INTERMEDIATE_DIR / "hw2_beam_geometry.json").write_text(json.dumps(geometry_payload, indent=2), encoding="utf-8")

    area_sum = sum(float(r["tributary_area_m2"]) for r in table_rows)
    checks = {
        "beam_count": len(beams), "net_slab_area_m2": net.area,
        "sum_beam_tributary_area_m2_rounded_csv": area_sum,
        "sum_beam_tributary_area_m2_exact": sum(sum(p["tributary_width_m"])*p["length_m"]/nbins for p in profiles.values()),
        "global_dead_load_kN": net.area*qd, "global_live_load_kN": net.area*ql,
        "beam_dead_load_kN": sum(float(r["dead_eq_kN_m"])*float(r["span_m"]) for r in table_rows),
        "beam_live_load_kN": sum(float(r["live_eq_kN_m"])*float(r["span_m"]) for r in table_rows),
    }
    (RESULT_DIR / "hw2_load_verification.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    plot_partition(gross, openings, xx, yy, inside, owner, beams)
    plot_summary(table_rows)
    plot_marked_profiles(cfg, profiles)
    plot_hand_bounds(cfg, profiles)
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
