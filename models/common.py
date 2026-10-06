from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import openseespy.opensees as ops


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "hw2_beams.json"
PROFILES = ROOT / "output" / "results" / "hw2_beam_profiles.json"
MODEL_RESULTS = ROOT / "output" / "results" / "models"
FIG_DIR = ROOT / "output" / "figures"


def load_inputs(mark):
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    payload = json.loads(PROFILES.read_text(encoding="utf-8"))
    ids = cfg["marked_beams"][mark]["segments"]
    profiles = [payload["profiles"][bid] for bid in ids]
    return cfg, ids, profiles


def section_properties(cfg):
    props = cfg["materials_and_sections"]
    b = props["beam_width_m"]
    d = props["beam_depth_m"]
    cb = props["column_width_m"]
    cd = props["column_depth_m"]
    return {
        "E": props["concrete_E_kN_m2"],
        "Ab": b*d, "Ib": b*d**3/12,
        "Ac": cb*cd, "Ic": cb*cd**3/12,
        "H": props["storey_height_m"],
    }


def q_at(profile, s):
    return float(np.interp(s, profile["s_centres_m"], profile["total_kN_m"],
                           left=profile["total_kN_m"][0], right=profile["total_kN_m"][-1]))


def create_beam_nodes(cfg, profiles, y):
    ndiv = cfg["analysis"]["opensees_elements_per_segment"]
    support_nodes = []
    beam_nodes = []
    elements = []
    xoff = 0.0
    node_tag = 1
    ele_tag = 1
    first = True
    for span_idx, profile in enumerate(profiles):
        length = profile["length_m"]
        local_x = np.linspace(0.0, length, ndiv+1)
        span_nodes = []
        for k, lx in enumerate(local_x):
            if not first and k == 0:
                span_nodes.append(beam_nodes[-1])
                continue
            ops.node(node_tag, xoff+lx, y)
            beam_nodes.append(node_tag)
            span_nodes.append(node_tag)
            node_tag += 1
        if first:
            support_nodes.append(span_nodes[0])
            first = False
        support_nodes.append(span_nodes[-1])
        for k in range(ndiv):
            le = length/ndiv
            q = q_at(profile, (k+.5)*le)
            ops.element("elasticBeamColumn", ele_tag, span_nodes[k], span_nodes[k+1],
                        section_properties(cfg)["Ab"], section_properties(cfg)["E"],
                        section_properties(cfg)["Ib"], 1)
            elements.append({
                "tag": ele_tag, "ni": span_nodes[k], "nj": span_nodes[k+1],
                "x0": xoff+k*le, "length": le, "q": q,
                "span_index": span_idx,
            })
            ele_tag += 1
        xoff += length
    return beam_nodes, support_nodes, elements, node_tag, ele_tag


def solve_case(mark, model_type):
    cfg, ids, profiles = load_inputs(mark)
    sec = section_properties(cfg)
    ops.wipe()
    ops.model("basic", "-ndm", 2, "-ndf", 3)
    ops.geomTransf("Linear", 1)
    top_y = 0.0 if model_type == "pure" else sec["H"]
    beam_nodes, support_nodes, beam_elements, next_node, next_ele = create_beam_nodes(cfg, profiles, top_y)
    base_nodes = []
    column_elements = []
    if model_type == "pure":
        for k, node in enumerate(support_nodes):
            ops.fix(node, 1 if k == 0 else 0, 1, 0)
    else:
        for support_node in support_nodes:
            x, _ = ops.nodeCoord(support_node)
            base = next_node
            next_node += 1
            ops.node(base, x, 0.0)
            ops.fix(base, 1, 1, 1)
            ops.element("elasticBeamColumn", next_ele, base, support_node,
                        sec["Ac"], sec["E"], sec["Ic"], 1)
            base_nodes.append(base)
            column_elements.append({"tag": next_ele, "base": base, "top": support_node, "x": x})
            next_ele += 1

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for e in beam_elements:
        ops.eleLoad("-ele", e["tag"], "-type", "-beamUniform", -e["q"])
    ops.system("BandGeneral")
    ops.numberer("Plain")
    ops.constraints("Plain")
    ops.integrator("LoadControl", 1.0)
    ops.algorithm("Linear")
    ops.analysis("Static")
    status = ops.analyze(1)
    if status != 0:
        raise RuntimeError(f"OpenSees analysis failed for Beam {mark} {model_type}: {status}")

    ops.reactions()
    reaction_nodes = support_nodes if model_type == "pure" else base_nodes
    reactions = []
    for k, n in enumerate(reaction_nodes):
        reactions.append({
            "support_index": k, "node": n, "x_m": float(ops.nodeCoord(n)[0]),
            "Rx_kN": float(ops.nodeReaction(n, 1)),
            "Ry_kN": float(ops.nodeReaction(n, 2)),
            "Mz_kNm": float(ops.nodeReaction(n, 3)),
        })

    response = {"x_m": [], "N_kN": [], "V_kN": [], "M_kNm": []}
    applied = 0.0
    for e in beam_elements:
        f = ops.eleResponse(e["tag"], "localForce")
        le = e["length"]
        local = np.linspace(0, le, 9, endpoint=False)
        for s in local:
            response["x_m"].append(e["x0"]+s)
            response["N_kN"].append(float(-f[0]))
            response["V_kN"].append(float(f[1]-e["q"]*s))
            response["M_kNm"].append(float(-f[2]+f[1]*s-e["q"]*s*s/2))
        applied += e["q"]*le
    last = beam_elements[-1]
    flast = ops.eleResponse(last["tag"], "localForce")
    response["x_m"].append(last["x0"]+last["length"])
    response["N_kN"].append(float(flast[3]))
    response["V_kN"].append(float(-flast[4]))
    response["M_kNm"].append(float(flast[5]))

    nodes = []
    all_nodes = beam_nodes + base_nodes
    for n in all_nodes:
        x, y = ops.nodeCoord(n)
        d = ops.nodeDisp(n)
        nodes.append({"node": n, "x_m": float(x), "y_m": float(y),
                      "ux_m": float(d[0]), "uy_m": float(d[1]), "rz_rad": float(d[2])})
    column_forces = []
    for c in column_elements:
        f = ops.eleResponse(c["tag"], "localForce")
        column_forces.append({
            "support_index": len(column_forces), "element": c["tag"], "x_m": c["x"],
            "base_axial_kN": float(-f[0]), "top_axial_kN": float(f[3]),
            "base_shear_kN": float(f[1]), "top_shear_kN": float(f[4]),
            "base_moment_kNm": float(f[2]), "top_moment_kNm": float(f[5]),
        })

    result = {
        "beam": mark, "model": model_type, "segment_ids": ids,
        "units": "kN, m, kN/m, kN m", "analysis_status": status,
        "section": sec, "applied_vertical_load_kN": applied,
        "sum_vertical_reaction_kN": sum(r["Ry_kN"] for r in reactions),
        "equilibrium_error_kN": sum(r["Ry_kN"] for r in reactions)-applied,
        "reactions": reactions, "column_forces": column_forces,
        "beam_response": response, "nodes": nodes,
        "max_abs_moment_kNm": max(abs(v) for v in response["M_kNm"]),
        "max_downward_deflection_mm": -1000*min(n["uy_m"] for n in nodes),
    }
    MODEL_RESULTS.mkdir(parents=True, exist_ok=True)
    out = MODEL_RESULTS / f"beam_{mark}_{model_type}.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    plot_result(result, support_nodes, beam_nodes, base_nodes)
    ops.wipe()
    return result


def plot_result(result, support_nodes, beam_nodes, base_nodes):
    mark = result["beam"]
    model = result["model"]
    nodes = {n["node"]: n for n in result["nodes"]}
    response = result["beam_response"]
    fig = plt.figure(figsize=(11, 8.5), constrained_layout=True)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.05, 1, 1])
    ax_sketch = fig.add_subplot(gs[0, 0])
    ax_def = fig.add_subplot(gs[0, 1])
    ax_n = fig.add_subplot(gs[1, 0])
    ax_v = fig.add_subplot(gs[1, 1])
    ax_m = fig.add_subplot(gs[2, :])

    # Independent pre-solve schematic: continuous curvature with hogging near
    # interior supports.  It is intentionally not computed from solver output.
    support_x = [nodes[n]["x_m"] for n in support_nodes]
    for a, b in zip(support_x[:-1], support_x[1:]):
        x = np.linspace(a, b, 80)
        t = (x-a)/(b-a)
        y = -.9*np.sin(np.pi*t)+.20*np.sin(2*np.pi*t)
        ax_sketch.plot(x, y, color="#2b2d42", lw=2)
    ax_sketch.axhline(0, color="#aaa", lw=.7)
    ax_sketch.plot(support_x, np.zeros(len(support_x)), "^", color="#606c38")
    ax_sketch.set_title("Pre-solve hand-check sketch (schematic)")
    ax_sketch.set_yticks([])
    ax_sketch.set_xlabel("Distance along beam (m)")

    # Exaggerate the largest vertical displacement to 1.5 drawing units so
    # the curvature is visible without making the axis look like tens of metres.
    scale = 1.5/max(max(abs(n["uy_m"]) for n in nodes.values()), 1e-9)
    top = [nodes[n] for n in beam_nodes]
    ax_def.plot([n["x_m"] for n in top], [n["y_m"] for n in top], color="#999", lw=1, label="undeformed")
    ax_def.plot([n["x_m"]+scale*n["ux_m"] for n in top],
                [n["y_m"]+scale*n["uy_m"] for n in top], color="#d62828", lw=2, label=f"deformed x{scale:.0f}")
    if base_nodes:
        for base, top_node in zip(base_nodes, support_nodes):
            nb, nt = nodes[base], nodes[top_node]
            ax_def.plot([nb["x_m"], nt["x_m"]], [nb["y_m"], nt["y_m"]], color="#999", lw=1)
            ax_def.plot([nb["x_m"]+scale*nb["ux_m"], nt["x_m"]+scale*nt["ux_m"]],
                        [nb["y_m"]+scale*nb["uy_m"], nt["y_m"]+scale*nt["uy_m"]], color="#d62828", lw=2)
    ax_def.set_title(f"OpenSees deformed shape - Beam {mark} {model}")
    ax_def.set_xlabel("Model x (m)")
    ax_def.set_ylabel("Model y + exaggerated displacement")
    ax_def.legend(frameon=False, fontsize=8)
    ax_def.grid(alpha=.18)

    x = response["x_m"]
    ax_n.plot(x, response["N_kN"], color="#264653", lw=1.5)
    ax_n.axhline(0, color="#777", lw=.7)
    ax_n.set_title("Axial-force diagram N")
    ax_n.set_ylabel("N (kN); tension +")
    ax_n.grid(alpha=.18)
    ax_v.plot(x, response["V_kN"], color="#2a9d8f", lw=1.5)
    ax_v.axhline(0, color="#777", lw=.7)
    ax_v.set_title("Shear-force diagram V")
    ax_v.set_ylabel("V (kN)")
    ax_v.grid(alpha=.18)
    ax_m.plot(x, response["M_kNm"], color="#e76f51", lw=1.8)
    ax_m.fill_between(x, 0, response["M_kNm"], color="#e76f51", alpha=.15)
    ax_m.axhline(0, color="#777", lw=.7)
    for sx in support_x:
        ax_m.axvline(sx, color="#888", ls="--", lw=.6)
    ax_m.set_title("Bending-moment diagram M (sagging +, hogging -)")
    ax_m.set_xlabel("Distance along beam (m)")
    ax_m.set_ylabel("M (kN m)")
    ax_m.grid(alpha=.18)
    fig.suptitle(f"Beam {mark} - {model.capitalize()} Model | applied {result['applied_vertical_load_kN']:.1f} kN | equilibrium error {result['equilibrium_error_kN']:.2e} kN", weight="bold")
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / f"hw2_beam_{mark}_{model}_response.png", dpi=220)
    plt.close(fig)


def run_case(mark, model_type):
    if mark not in {"A", "B"} or model_type not in {"pure", "subframe"}:
        raise ValueError("mark must be A/B and model_type pure/subframe")
    result = solve_case(mark, model_type)
    print(json.dumps({k: result[k] for k in ["beam", "model", "applied_vertical_load_kN", "sum_vertical_reaction_kN", "equilibrium_error_kN", "max_abs_moment_kNm", "max_downward_deflection_mm"]}, indent=2))

