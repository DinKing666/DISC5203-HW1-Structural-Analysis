from __future__ import annotations

import csv
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, Image, LongTable, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "21345221_HW2_report.pdf"


def rows(name):
    with (ROOT / "output" / "results" / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fonts():
    reg = next(p for p in [Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/calibri.ttf")] if p.exists())
    bold = next(p for p in [Path("C:/Windows/Fonts/arialbd.ttf"), Path("C:/Windows/Fonts/calibrib.ttf")] if p.exists())
    pdfmetrics.registerFont(TTFont("Body", str(reg)))
    pdfmetrics.registerFont(TTFont("BodyBold", str(bold)))


def header_footer(canvas, doc):
    canvas.saveState()
    w, h = doc.pagesize
    canvas.setStrokeColor(colors.HexColor("#B8C9D3"))
    canvas.line(16*mm, h-14*mm, w-16*mm, h-14*mm)
    canvas.setFont("Body", 8)
    canvas.setFillColor(colors.HexColor("#35556B"))
    canvas.drawString(16*mm, h-10*mm, "DISC 5203 | HW2 | Shuhan He | 21345221")
    canvas.drawRightString(w-16*mm, 9*mm, f"Page {doc.page}")
    canvas.restoreState()


def styled_table(data, widths, size=7.0, repeat=1):
    t = LongTable(data, colWidths=widths, repeatRows=repeat, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Body"), ("FONTSIZE", (0,0), (-1,-1), size),
        ("LEADING", (0,0), (-1,-1), size+2), ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#AFC1CC")),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#204A6B")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("FONTNAME", (0,0), (-1,0), "BodyBold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F2F6F8")]),
        ("LEFTPADDING", (0,0), (-1,-1), 2.5), ("RIGHTPADDING", (0,0), (-1,-1), 2.5),
        ("TOPPADDING", (0,0), (-1,-1), 2.5), ("BOTTOMPADDING", (0,0), (-1,-1), 2.5),
    ]))
    return t


def fit_image(path, width_mm, height_mm):
    img = Image(str(path))
    ratio = min(width_mm*mm/img.imageWidth, height_mm*mm/img.imageHeight)
    img.drawWidth = img.imageWidth*ratio
    img.drawHeight = img.imageHeight*ratio
    return img


def main():
    fonts()
    cfg = json.loads((ROOT / "config" / "hw2_beams.json").read_text(encoding="utf-8"))
    checks = json.loads((ROOT / "output" / "results" / "hw2_load_verification.json").read_text(encoding="utf-8"))
    load_rows = rows("hw2_beam_line_loads.csv")
    model_rows = rows("hw2_model_summary.csv")
    cross_rows = rows("hw2_axial_crosscheck.csv")
    qd = cfg["loads"]["slab_thickness_m"]*cfg["loads"]["concrete_unit_weight_kN_m3"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=16*mm, rightMargin=16*mm,
                          topMargin=19*mm, bottomMargin=15*mm, title="DISC 5203 Homework 2",
                          author="Shuhan He")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="all", frames=frame, onPage=header_footer)])
    base = getSampleStyleSheet()
    S = {
        "title": ParagraphStyle("title", parent=base["Title"], fontName="BodyBold", fontSize=21, leading=26, textColor=colors.HexColor("#173F5F"), alignment=TA_LEFT, spaceAfter=6*mm),
        "sub": ParagraphStyle("sub", parent=base["Normal"], fontName="Body", fontSize=10.5, leading=15, textColor=colors.HexColor("#46697A"), spaceAfter=2*mm),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="BodyBold", fontSize=14, leading=17, textColor=colors.HexColor("#173F5F"), spaceBefore=4*mm, spaceAfter=2*mm, keepWithNext=1),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="BodyBold", fontSize=10.5, leading=13, textColor=colors.HexColor("#35556B"), spaceBefore=3*mm, spaceAfter=1.5*mm, keepWithNext=1),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Body", fontSize=8.8, leading=12.5, textColor=colors.HexColor("#202B33"), spaceAfter=2*mm),
        "cap": ParagraphStyle("cap", parent=base["BodyText"], fontName="Body", fontSize=7.3, leading=9, textColor=colors.HexColor("#5B6970"), alignment=TA_CENTER, spaceAfter=2.5*mm),
        "call": ParagraphStyle("call", parent=base["BodyText"], fontName="BodyBold", fontSize=9.4, leading=14, textColor=colors.white, backColor=colors.HexColor("#204A6B"), borderPadding=7, spaceAfter=3*mm),
    }
    P = lambda txt, style="body": Paragraph(txt, S[style])
    story = []
    logo = ROOT / "assets" / "UST_logo.png"
    if logo.exists():
        story.append(fit_image(logo, 17, 17))
    story += [Spacer(1, 10*mm), P("From Slab to Beam", "title"),
              P("Tributary Areas, Line Loads and a Two-Dimensional Subframe", "sub"),
              Spacer(1, 4*mm), styled_table([
                  ["Course", "Computer (& AI) Methods for Structural Engineering (DISC 5203)"],
                  ["Student", "Shuhan He"], ["Student ID", "21345221"],
                  ["Assigned plan", "Floor Plan 1 (final digit 1)"], ["Review date", "6 October 2026"],
              ], [36*mm, 116*mm], 8.7, 0), Spacer(1, 8*mm),
              P(f"24 beam segments | net slab {checks['net_slab_area_m2']:.3f} m2 | four OpenSees models | exact area and reaction equilibrium", "call"),
              P("Scope", "h1"), P("This report extends the existing HW1 Git working tree. It reuses the HW1 slab and vertical-element results, transfers the same gravity load to beams with 45-degree tributary boundaries, models the two marked beams as standalone continuous beams and one-floor subframes, and cross-checks subframe column forces against HW1 axial estimates."),
              PageBreak(), P("1. Reused plan and assumptions", "h1"),
              fit_image(ROOT/"assets"/"FloorPlan1_HW2.png", 120, 150), P("Figure 1. Assigned Floor Plan 1; red boxes mark Beam A and Beam B.", "cap"),
              P(f"Dead slab load = 25 x 0.150 = {qd:.2f} kN/m2; live load = 5.00 kN/m2. No finish load is printed. Beam self-weight is excluded from the requested slab-to-beam transfer. Unprinted beam size is explicitly assumed as 300 x 600 mm; columns are 400 x 400 mm, storey height 3.0 m and E = 30.0e6 kN/m2."),
              PageBreak(), P("2. 45-degree beam tributary construction", "h1"),
              P("Each cell of the unchanged HW1 net slab is assigned to its nearest finite beam edge. Parallel beams divide at mid-lines; equal distance to perpendicular edges gives |Delta x| = |Delta y| and a 45-degree corner line. Openings are removed before assignment. P10 and P11 are cantilevers and add a uniform component to their single support line."),
              P("For a two-way rectangle with short side a and long side b: A_short = a2/4 and A_long = a(2b-a)/4. The stored non-uniform profile, not the tabulated UDL, is used for local response."),
              fit_image(ROOT/"output"/"figures"/"hw2_01_beam_tributary_areas.png", 150, 174), P("Figure 2. Beam ownership field and 45-degree divisions.", "cap"),
              PageBreak(), P("3. Beam census and equivalent line-load table", "h1"),
              P("Equivalent UDL means equal total load only. It does not preserve local shear or the exact moment-diagram shape."),
    ]
    table = [["ID","Span","Panels","Class","Area","Dead","Live","Total"]]
    for r in load_rows:
        table.append([r["beam_id"], r["span_m"], Paragraph(r["bordering_panels"], S["cap"]), Paragraph(r["support_class"], S["cap"]), r["tributary_area_m2"], r["dead_eq_kN_m"], r["live_eq_kN_m"], r["total_eq_kN_m"]])
    story += [styled_table(table, [11*mm,13*mm,37*mm,37*mm,15*mm,15*mm,15*mm,16*mm], 6.2),
              P("Units: span in m; area in m2; line loads in kN/m.", "cap"), PageBreak(),
              P("4. Load profiles and worked example", "h1"),
              P("For H1-2, L = 4.410 m and the actual two-sided tributary area is read from P2 and P5 after the core opening is removed. D = 3.75 A, L_live = 5.00 A, and each equivalent line load is the corresponding total divided by 4.410 m. The figure retains the triangular/trapezoidal distribution used in OpenSees."),
              fit_image(ROOT/"output"/"figures"/"hw2_03_marked_beam_load_profiles.png", 172, 116), P("Figure 3. Frozen dead, live and total line-load profiles.", "cap"),
              fit_image(ROOT/"output"/"figures"/"hw2_04_hand_bounds_and_sketches.png", 172, 90), P("Figure 4. Pre-solve sketches and qL2 bounds.", "cap"),
              PageBreak(), P("5. OpenSees response diagrams", "h1"),
              P("Standalone models retain vertical supports with free rotations. Subframes replace them with fixed-base 3 m columns sharing the beam nodes. The same frozen profile is applied in every comparison."),
    ]
    for mark in ("A", "B"):
        for kind in ("pure", "subframe"):
            story += [fit_image(ROOT/"output"/"figures"/f"hw2_beam_{mark}_{kind}_response.png", 176, 135),
                      P(f"Figure. Beam {mark}, {kind} model: pre-solve sketch, deformed shape and N/V/M diagrams.", "cap"), PageBreak()]
    story += [P("6. Numerical comparison", "h1")]
    mt = [["Beam","Model","Load","Sag +","Hog -","Max |M|","Down mm","qL2/8","Check"]]
    for r in model_rows:
        mt.append([r["beam"],r["model"],r["applied_load_kN"],r["max_sagging_kNm"],r["max_hogging_kNm"],r["max_abs_moment_kNm"],r["max_downward_deflection_mm"],r["largest_qL2_over_8_bound_kNm"],r["bound_and_sign_verdict"]])
    story += [styled_table(mt, [11*mm,21*mm,20*mm,18*mm,18*mm,20*mm,18*mm,20*mm,17*mm], 7),
              P("Loads are kN; moments are kN m. Every model closes equilibrium below 1e-8 kN and has sagging-positive and hogging-negative regions. The subframe is the defensible beam-design model because it retains finite column stiffness; the standalone beam remains an independent bound."),
              P("7. HW1 axial cross-check", "h1")]
    ct = [["Strip","Grid","HW1 member","HW1 N","HW2 N","Diff %","Sign"]]
    for r in cross_rows:
        ct.append([r["beam_strip"],r["grid_point"],r["hw1_vertical_element"],r["hw1_column_axial_kN_compression_negative"],r["hw2_subframe_column_top_N_kN_compression_negative"],r["percent_difference_magnitude"],r["sign_check"]])
    story += [styled_table(ct, [13*mm,18*mm,25*mm,28*mm,28*mm,23*mm,18*mm], 7.2),
              fit_image(ROOT/"output"/"figures"/"hw2_09_axial_crosscheck.png", 168, 82),
              P("Figure. Magnitude difference between the 2D marked strips and HW1 whole-floor estimates.", "cap"),
              P("Compression sign agrees at every mapped support, but the magnitude is not within a few percent. HW1 includes the whole-floor nearest-support load and aggregated walls; each HW2 result contains only one marked strip and omits perpendicular beam paths. No load was tuned. The subframe is used for the beam design question; exact cross-model reconciliation requires a 3D grid or common nodal aggregation."),
              P("8. Agent workflow and reproducibility", "h1"),
              P("The word briefings were frozen before code generation. The agent transcribed them into four OpenSees entry files plus an audited shared implementation. Gates were: identify the deck, freeze loads, check units and signs, verify qL2 bounds, replace supports by columns, close equilibrium, compare HW1 axials, then leave Git commit/upload pending student review."),
              P("Run: analyze_hw2_beam_loads.py; run_hw2_models.py; summarize_hw2_models.py; build_hw2_report.py; render_hw2_report_pdf.py; verify_hw2_outputs.py."),
              P("Limitations", "h2"), P("The plan is raster; beam size and uncracked stiffness are assumptions; the subframes are 2D strips; and the student must add a literal handwritten/signature sheet if required. These limits are preserved rather than concealed."),
              P("Conclusion", "h1"), P("All required beam census, tributary areas, line loads, four OpenSees cases, N/V/M and deformation diagrams, reactions, hand bounds, prompt record, HW1 cross-check and reproducibility files are present. The repository remains uncommitted and unuploaded until student sign-off.")]
    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    main()
