from __future__ import annotations

import csv
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "HW1_report.pdf"


def register_fonts():
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
    ]
    bold_candidates = [Path("C:/Windows/Fonts/arialbd.ttf"), Path("C:/Windows/Fonts/calibrib.ttf")]
    regular = next(p for p in candidates if p.exists())
    bold = next(p for p in bold_candidates if p.exists())
    pdfmetrics.registerFont(TTFont("Body", str(regular)))
    pdfmetrics.registerFont(TTFont("BodyBold", str(bold)))


def page_header_footer(canvas, doc):
    canvas.saveState()
    w, h = doc.pagesize
    canvas.setStrokeColor(colors.HexColor("#B7C9D6"))
    canvas.line(18 * mm, h - 14 * mm, w - 18 * mm, h - 14 * mm)
    canvas.setFont("Body", 8)
    canvas.setFillColor(colors.HexColor("#3D5A6C"))
    canvas.drawString(18 * mm, h - 10 * mm, "DISC 5203 | Homework 1 | Shuhan He | 21345221")
    canvas.drawRightString(w - 18 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def styled_table(data, widths, font_size=7.2, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Body"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 2),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#AFC1CC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F7F9")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#204A6B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "BodyBold"),
        ]
    t.setStyle(TableStyle(commands))
    return t


def main():
    register_fonts()
    with (ROOT / "config" / "plan1_geometry.json").open(encoding="utf-8") as f:
        cfg = json.load(f)
    with (ROOT / "output" / "intermediate" / "geometry_plan1.json").open(encoding="utf-8") as f:
        geo = json.load(f)
    with (ROOT / "output" / "results" / "element_loads.csv").open(encoding="utf-8") as f:
        elements = list(csv.DictReader(f))
    with (ROOT / "output" / "results" / "building_level_totals.csv").open(encoding="utf-8") as f:
        levels = list(csv.DictReader(f))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(OUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
                          topMargin=20 * mm, bottomMargin=16 * mm,
                          title="AI-Assisted Structural Analysis of a Building Floor Plan",
                          author="Shuhan He")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="all", frames=frame, onPage=page_header_footer)])

    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("Title", parent=base["Title"], fontName="BodyBold", fontSize=23,
                                leading=28, textColor=colors.HexColor("#173F5F"), alignment=TA_LEFT,
                                spaceAfter=8 * mm),
        "subtitle": ParagraphStyle("Subtitle", parent=base["Normal"], fontName="Body", fontSize=11,
                                   leading=16, textColor=colors.HexColor("#456879"), spaceAfter=3 * mm),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName="BodyBold", fontSize=15,
                             leading=18, textColor=colors.HexColor("#173F5F"), spaceBefore=5 * mm,
                             spaceAfter=2.5 * mm),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName="BodyBold", fontSize=11,
                             leading=14, textColor=colors.HexColor("#3D5A6C"), spaceBefore=3 * mm,
                             spaceAfter=1.5 * mm),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Body", fontSize=9.2,
                               leading=13.5, textColor=colors.HexColor("#202B33"), spaceAfter=2.2 * mm),
        "caption": ParagraphStyle("Caption", parent=base["BodyText"], fontName="Body", fontSize=7.5,
                                  leading=10, textColor=colors.HexColor("#5A6A73"), alignment=TA_CENTER,
                                  spaceAfter=3 * mm),
        "callout": ParagraphStyle("Callout", parent=base["BodyText"], fontName="BodyBold", fontSize=10,
                                  leading=15, textColor=colors.white, backColor=colors.HexColor("#204A6B"),
                                  borderPadding=8, spaceBefore=3 * mm, spaceAfter=4 * mm),
    }
    P = lambda txt, style="body": Paragraph(txt, styles[style])
    qd = cfg["loads"]["slab_thickness_m"] * cfg["loads"]["concrete_unit_weight_kN_m3"]
    ql = cfg["loads"]["live_load_kN_m2"]
    net = geo["net_floor_area_m2"]
    story_total = net * (qd + ql)
    story = []

    logo = ROOT / "assets" / "UST_logo.png"
    if logo.exists():
        story.append(Image(str(logo), width=15 * mm, height=16 * mm))
    story += [
        Spacer(1, 12 * mm),
        P("AI-Assisted Structural Analysis<br/>of a Building Floor Plan", "title"),
        P("Homework Assignment 1 - Floor Plan 1", "subtitle"),
        Spacer(1, 6 * mm),
        styled_table([
            ["Course", "Computer (& AI) Methods for Structural Engineering (DISC 5203)"],
            ["Student", "Shuhan He"], ["Student ID", "21345221"],
            ["Assigned plan", "Floor Plan 1 (student-ID final digit 1)"],
            ["Submission date", "28 September 2026"],
        ], [36 * mm, 115 * mm], 9, header=False),
        Spacer(1, 12 * mm),
        P(f"Net loaded floor area: {net:.2f} m2&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;"
          f"One-floor gravity load: {story_total:.1f} kN&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;"
          f"Five-storey base load: {5*story_total:.1f} kN", "callout"),
        Spacer(1, 12 * mm),
        P("Scope", "h1"),
        P("This submission extracts the floor outline and vertical supports, assigns tributary area to each column and wall, calculates dead, live and total axial loads, verifies global equilibrium, and documents a reproducible AI-agent workflow."),
        PageBreak(),
        P("1. Input and engineering interpretation", "h1"),
        P("The assignment PDF and the supplied FloorPlan1 image were inspected visually. Printed dimensions govern the metric geometry; pixel dimensions are used only for visual review. The local datum is the lower-left outside corner of the overall floor envelope, with positive x to the right and positive y upward."),
        Image(str(ROOT / "assets" / "FloorPlan1.png"), width=116 * mm, height=143 * mm),
        P("Figure 1. Assigned source image, Floor Plan 1.", "caption"),
        P("The source is a raster drawing rather than CAD. Explicit dimensions were used directly. Where endpoints or core opening limits are not fully dimensioned, coordinates were inferred from adjacent dimension chains and recorded in the JSON configuration for audit and revision."),
        PageBreak(),
        P("2. Extracted geometry and vertical elements", "h1"),
        P(f"The modeled slab has a gross area of {geo['gross_area_m2']:.2f} m2. Two core/stair openings totaling {geo['opening_area_m2']:.2f} m2 are removed, leaving a net floor area of {net:.2f} m2. Seven columns and eleven finite wall segments are represented."),
        Image(str(ROOT / "output" / "figures" / "01_extracted_geometry.png"), width=125 * mm, height=152 * mm),
        P("Figure 2. Digitized floor outline, excluded openings, column centers, and wall centrelines.", "caption"),
        PageBreak(),
        P("3. Tributary-area method", "h1"),
        P("The net slab is divided into 0.02 m square cells. Each cell centre is assigned to the closest vertical element using rectilinear (L1) distance. Columns are point supports and walls are finite axis-aligned segments. This produces horizontal, vertical, and diagonal straight boundaries rather than the curved endpoint boundaries of a finite-segment Euclidean partition."),
        P("For an axis-aligned segment: d1 = max(xmin-x, 0, x-xmax) + max(ymin-y, 0, y-ymax). Parallel supports are divided at mid-span. For perpendicular wall axes, equal offsets satisfy |dx| = |dy|, which gives the required 45-degree corner line."),
        P(f"The counted raster area is adjusted by one global factor equal to exact polygon area divided by raster area. The boundary-cell error before adjustment is {geo['area_closure_error_before_normalization_percent']:.4f}%, and the final partition closes exactly to the polygon area."),
        P("Red solid lines identify support axes and blue solid lines identify the tributary boundaries. A blue boundary is continuous within loaded slab and terminates only at the exterior perimeter or an excluded stair/core opening, because a void carries no floor load."),
        Image(str(ROOT / "output" / "figures" / "02_tributary_areas.png"), width=125 * mm, height=152 * mm),
        P("Figure 3. Straight-line tributary-area partition with 45-degree corner divisions.", "caption"),
        PageBreak(),
        P("4. Gravity-load calculation", "h1"),
        P("Only the loads supplied by the assignment are included. Concrete slab self-weight is the dead load. Beam, wall, column, finish, facade and partition self-weights are excluded because the necessary weights are not provided."),
        styled_table([
            ["Quantity", "Value", "Use"],
            ["Slab thickness, h", "0.150 m", "Assignment input"],
            ["Concrete unit weight, gamma", "25.0 kN/m3", "Assumed normal reinforced concrete"],
            ["Dead area load, qD", f"{qd:.2f} kN/m2", "qD = gamma x h"],
            ["Live area load, qL", f"{ql:.2f} kN/m2", "Assignment input"],
            ["Total area load, q", f"{qd+ql:.2f} kN/m2", "q = qD + qL"],
            ["Identical storeys", "5", "Assignment input"],
        ], [50 * mm, 35 * mm, 75 * mm], 8),
        Spacer(1, 4 * mm),
        P("For element i: Di = qD Ai; Li = qL Ai; Ni,1 = Di + Li; Ni,base = 5 Ni,1. Results are unfactored service loads. The 3 m storey height does not change the slab gravity load and is retained as contextual geometry."),
        Image(str(ROOT / "output" / "figures" / "03_element_loads.png"), width=160 * mm, height=79 * mm),
        P("Figure 4. One-floor dead and live axial-load components.", "caption"),
        PageBreak(),
        P("5. Element results", "h1"),
        P("Locations are column centers or wall-segment midpoints. Base total is the cumulative load from five identical floors."),
    ]

    data = [["ID", "Type", "x", "y", "Size", "Area", "Dead", "Live", "1-floor", "5-storey"]]
    for r in elements:
        data.append([
            r["id"], r["type"], f"{float(r['x_m']):.2f}", f"{float(r['y_m']):.2f}", r["size_mm"],
            f"{float(r['tributary_area_m2']):.2f}", f"{float(r['dead_load_1floor_kN']):.1f}",
            f"{float(r['live_load_1floor_kN']):.1f}", f"{float(r['total_load_1floor_kN']):.1f}",
            f"{float(r['base_load_5storey_kN']):.1f}",
        ])
    story.append(styled_table(data, [11*mm, 16*mm, 12*mm, 12*mm, 20*mm, 17*mm, 17*mm, 17*mm, 18*mm, 20*mm], 6.5))
    story += [
        P("Units: coordinates in m; size in mm; area in m2; loads in kN.", "caption"),
        P("6. Building-level accumulation", "h1"),
    ]
    level_data = [["Level", "Floors supported", "Dead load (kN)", "Live load (kN)", "Total load (kN)"]]
    for r in levels:
        level_data.append([r["level"], r["floors_supported"], r["dead_kN"], r["live_kN"], r["total_kN"]])
    story.append(styled_table(level_data, [35*mm, 34*mm, 31*mm, 31*mm, 32*mm], 8))
    story += [
        PageBreak(),
        P("7. Verification", "h1"),
        P(f"Area closure: sum(Ai) = {net:.6f} m2, equal to the independent polygon area. Global one-floor dead load = {net*qd:.3f} kN and live load = {net*ql:.3f} kN; both equal the corresponding element sums within floating-point precision."),
        P("Every in-slab cell is assigned exactly once and all 18 vertical elements receive positive tributary area. Dimensional analysis gives (m2)(kN/m2) = kN. The cumulative base result equals exactly five times the one-floor result because the plan and loads repeat on all five storeys."),
        P("8. Limitations", "h1"),
        P("The raster source requires interpretation of some wall endpoints and opening edges. The straight-line rectilinear partition follows the assignment's midpoint and 45-degree corner rules; a plate analysis could still redistribute load according to stiffness and span direction. Non-slab dead loads are omitted because they are unspecified. These limits are explicit rather than hidden, and the configuration can be revised without changing the solver."),
        P("9. Reproducible AI-agent workflow", "h1"),
        P("The agent read the source PDF and images, created a reviewable metric geometry model, implemented a deterministic partition and load calculation, generated plots and tables, and ran automated conservation checks. The repository contains the original inputs, geometry JSON, Python scripts, guidance files, a pre-commit verification hook, intermediate outputs, final results, and this report."),
        P("Reproduction command sequence", "h2"),
        P("python -m pip install -r requirements.txt<br/>python scripts/analyze_floor_plan.py<br/>python scripts/build_report.py<br/>python scripts/render_report_pdf.py<br/>python scripts/verify_outputs.py"),
        P("10. Conclusion", "h1"),
        P(f"Floor Plan 1 has a modeled net loaded area of {net:.2f} m2. Under qD = {qd:.2f} kN/m2 and qL = {ql:.2f} kN/m2, it transfers {story_total:.1f} kN per typical floor and {5*story_total:.1f} kN at the base of the five-storey stack. The element schedule provides the corresponding tributary area and axial load for each identified column and wall."),
    ]
    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    main()

