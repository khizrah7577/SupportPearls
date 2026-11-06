"""Generate PDF and DOCX knowledge-base documents.

Run once after installing dependencies:
    python scripts/generate_kb_binaries.py
"""

from __future__ import annotations

from pathlib import Path

from docx import Document as DocxDocument
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "data" / "knowledge_base"


def styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "PearlzTitle",
        parent=base["Heading1"],
        fontSize=18,
        spaceAfter=12,
    )
    h2 = ParagraphStyle(
        "PearlzH2",
        parent=base["Heading2"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8,
    )
    body = ParagraphStyle(
        "PearlzBody",
        parent=base["BodyText"],
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )
    small = ParagraphStyle(
        "PearlzSmall",
        parent=base["BodyText"],
        fontSize=8,
        leading=10,
        textColor=colors.grey,
    )
    return title, h2, body, small


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, 1.2 * cm, "Pearlz Home Systems — Confidential product documentation")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_product_manual():
    title, h2, body, small = styles()
    path = KB / "product_manual_aquapearl500.pdf"
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="AquaPearl 500 Pro Product Manual",
    )
    story = []
    story.append(Paragraph("AquaPearl 500 Pro — Product Manual", title))
    story.append(Paragraph("Document ID: MAN-AP500-2026.1 | Version 2026.1 | January 2026", small))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Pearlz Home Systems (Pvt.) Ltd. This manual covers box contents, specifications, "
        "controls, operation, filter intervals, cleaning, safety, and audible alert codes E-01 to E-08.",
        body,
    ))

    story.append(Paragraph("1. Box contents", h2))
    for item in [
        "AquaPearl 500 Pro main unit",
        "Sediment pre-filter cartridge (pre-installed)",
        "Carbon filter cartridge",
        "RO membrane cartridge",
        "UV lamp module (factory installed)",
        "Inlet and outlet tubing kit (2 m)",
        "Adaptor valves and mounting screws",
        "Power adapter 24V DC",
        "Quick-start card and warranty leaflet",
    ]:
        story.append(Paragraph(f"• {item}", body))

    story.append(Paragraph("2. Technical specifications", h2))
    spec_data = [
        ["Parameter", "Value"],
        ["Flow rate (purified)", "Up to 15 L/hour"],
        ["Tank capacity", "8 litres storage"],
        ["Dimensions (W×D×H)", "40 × 25 × 48 cm"],
        ["Power", "24V DC, 65W peak"],
        ["Inlet pressure", "0.1 – 0.4 MPa"],
        ["Inlet water temp", "5 – 38 °C"],
        ["Filter stages", "Sediment, Carbon, RO, UV"],
        ["Max inlet TDS", "1500 ppm"],
    ]
    t = Table(spec_data, colWidths=[8 * cm, 8 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]
        )
    )
    story.append(t)

    story.append(PageBreak())
    story.append(Paragraph("3. Control panel and indicator lights", h2))
    story.append(Paragraph(
        "Power LED (white): solid = on. Status LED: green = normal; amber = maintenance due; "
        "blinking red = fault (see alert codes). TDS display shows purified water estimate in ppm. "
        "RESET button clears certain alerts after corrective action. PAIR button enables Bluetooth pairing.",
        body,
    ))

    story.append(Paragraph("4. Operating instructions", h2))
    story.append(Paragraph(
        "1. Ensure inlet tap is open and power is connected. 2. Wait for the tank to fill on first run. "
        "3. Dispense from the purified water tap. 4. Check the app dashboard weekly for filter life. "
        "5. Do not store hot liquids in the tank. 6. Keep 10 cm clearance around vents.",
        body,
    ))

    story.append(Paragraph("5. Filter replacement intervals", h2))
    filt = [
        ["Filter", "Typical interval", "SKU"],
        ["Sediment pre-filter", "3–6 months or on E-03", "FLT-SED-01"],
        ["Carbon filter", "6–12 months", "FLT-CAR-01"],
        ["RO membrane", "18–24 months", "FLT-RO-01"],
        ["UV lamp", "24 months or on E-08", "FLT-UV-01"],
    ]
    tf = Table(filt, colWidths=[5.5 * cm, 6.5 * cm, 4 * cm])
    tf.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(tf)

    story.append(Paragraph("6. Cleaning and descaling schedule", h2))
    story.append(Paragraph(
        "Wipe the exterior weekly with a damp cloth. Every 3 months, run a descaling cycle using Pearlz "
        "Descale Solution (or food-grade citric acid per quick-start card): fill the tank with solution, "
        "run a complete dispense-and-refill cycle twice, then flush with two full tanks of clean water. "
        "Never use abrasive cleaners or bleach on internal wet paths.",
        body,
    ))

    story.append(Paragraph("7. Safety warnings", h2))
    for w in [
        "Do not immerse the main unit in water.",
        "Use only the supplied 24V adapter.",
        "Disconnect power before filter changes.",
        "Keep away from children during filter replacement.",
        "If you smell burning or see smoke, unplug immediately and contact support.",
    ]:
        story.append(Paragraph(f"• {w}", body))

    story.append(PageBreak())
    story.append(Paragraph("8. Audible alert codes (E-01 to E-08)", h2))
    story.append(Paragraph(
        "Filter maintenance section reference. Three short beeps indicate E-03 sediment pre-filter saturation. "
        "Replace the pre-filter cartridge, then press and hold RESET for five seconds.",
        body,
    ))
    alerts = [
        ["Code", "Pattern", "Meaning"],
        ["E-01", "2 long beeps", "Inlet valve timeout"],
        ["E-02", "1 long + 1 short", "Tank full sensor fault"],
        ["E-03", "3 short beeps", "Sediment pre-filter saturation"],
        ["E-04", "4 short beeps", "Low inlet pressure"],
        ["E-05", "Blinking red LED", "Leak sensor wet"],
        ["E-06", "Continuous 2s tone", "Over-temperature (firmware 2.4+)"],
        ["E-07", "Alternating beeps", "Communication fault"],
        ["E-08", "5 rapid beeps", "UV lamp failure — escalate"],
    ]
    ta = Table(alerts, colWidths=[3 * cm, 5 * cm, 8 * cm])
    ta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(ta)
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Filtration performance: multi-stage RO+UV reduces dissolved solids and addresses microbiological risk "
        "under specified inlet conditions. Always follow local boil-water advisories when issued by authorities. "
        "This manual does not claim any third-party certification mark.",
        body,
    ))

    # Extended chapters for length / page-structure requirements (12–18 pages target)
    extended = [
        (
            "9. Daily use tips",
            [
                "Dispense water only from the purified tap. Avoid leaving the inlet closed for more than "
                "seven days without a flush cycle. If the unit will be unused for over two weeks, drain the "
                "tank and power off. On return, run a full flush before drinking.",
                "Do not store ice cubes made from unflushed water after a filter change. Taste issues after "
                "cartridge replacement are almost always resolved by completing the Installation Guide "
                "first-run flush (discard the first two full tanks).",
                "Keep serial numbers photographed with the invoice. The rating label is on the rear panel "
                "above the power inlet. Support requests without a serial number take longer to process.",
            ],
        ),
        (
            "10. Storage tank care",
            [
                "The 8-litre storage tank is food-contact safe plastic. Empty and wipe the tank interior "
                "every six months. Do not store flavoured beverages in the tank.",
                "If the tank develops biofilm odour, perform a citric-acid descaling cycle followed by two "
                "full flush tanks. Never use chlorine bleach inside the purified water path.",
                "Tank capacity is nominal; usable volume is slightly less when the float sensor cuts inlet "
                "fill. Continuous pump running with a full tank may indicate a stuck float — see Troubleshooting.",
            ],
        ),
        (
            "11. App connectivity overview",
            [
                "The Pearlz app shows filter life, TDS, and firmware version. Pairing requires Bluetooth. "
                "Firmware updates install overnight when the unit is idle and powered.",
                "Hold PAIR for three seconds until the status LED blinks blue. Keep the phone within two "
                "metres during pairing. If pairing fails, reboot the phone Bluetooth stack and retry once.",
                "App filter-life percentages are estimates based on flow and time. An E-03 alert overrides "
                "the estimate: replace the sediment pre-filter even if the app still shows remaining life.",
            ],
        ),
        (
            "12. Spare parts philosophy",
            [
                "Use only Pearlz SKUs listed in the Pricing Guide. Non-Pearlz cartridges may void warranty "
                "for damage attributed to those parts.",
                "Sediment FLT-SED-01, carbon FLT-CAR-01, RO FLT-RO-01, and UV FLT-UV-01 are the supported "
                "consumables for AquaPearl 500 Pro. Intervals are in Section 5; prices are not listed here.",
                "UV lamp replacement is recommended via an Authorised Service Partner. Customer self-install "
                "of UV modules can leave the chamber misaligned and will void related coverage.",
            ],
        ),
        (
            "13. Water quality assumptions",
            [
                "The unit expects cold municipal or well water within the inlet pressure and TDS limits in "
                "Section 2. It is not designed for seawater, untreated industrial effluent, or hot-water lines.",
                "High inlet TDS shortens RO membrane life. If purified TDS rises sharply, check membrane age "
                "and inlet TDS before assuming a sensor fault.",
                "This manual discusses filtration performance under specified conditions. It does not claim "
                "any third-party certification mark such as NSF. Do not invent certification language.",
            ],
        ),
        (
            "14. Seasonal maintenance calendar",
            [
                "Spring: inspect tubing for UV damage if the unit is near a window; wipe vents.",
                "Monsoon: check inlet strainer more often; sediment load rises and E-03 may trigger earlier.",
                "Winter: if inlet temperature approaches 5 °C, expect slower production; do not add heaters "
                "inside the cabinet without Pearlz guidance.",
                "Annually: consider AMC Plus or Premium if you prefer scheduled Service Partner visits "
                "(see Service & Maintenance Agreement).",
            ],
        ),
        (
            "15. Relocation and moving house",
            [
                "Before moving: close inlet, drain tank, disconnect power, cap open tubing ends.",
                "After relocating: leak-check all joints, run a full first-run flush, and re-pair the app.",
                "Warranty remains with the unit when transfer rules in the Warranty Policy are followed. "
                "Extended warranties on discontinued models are not transferable.",
            ],
        ),
        (
            "16. Indicator light quick reference",
            [
                "White power LED solid: unit powered. Off: no power or deep sleep after extended idle.",
                "Green status: normal operation. Amber: maintenance due soon. Blinking red: active fault "
                "(map pattern to E-codes in Section 8).",
                "Blue blink on status during PAIR: Bluetooth advertising mode active for two minutes.",
            ],
        ),
        (
            "17. Descaling procedure detail",
            [
                "Every three months under hard-water conditions, run Pearlz Descale Solution or food-grade "
                "citric acid per the quick-start card. Fill the tank with solution, complete two "
                "dispense-and-refill cycles, then flush with two full tanks of clean water.",
                "Never mix descaler with bleach. Never pour boiling water into the tank. If white scale "
                "remains on the dispense spout exterior, wipe with a soft cloth only.",
            ],
        ),
        (
            "18. End-of-life recycling",
            [
                "Return end-of-life units through Pearlz take-back weeks announced on the website, or "
                "dispose electronics via certified e-waste channels in your city.",
                "Remove batteries from any remote accessories before recycling. Filters may be bagged "
                "separately according to local solid-waste rules.",
            ],
        ),
        (
            "19. Glossary",
            [
                "TDS: total dissolved solids, estimated in ppm on the display for AquaPearl 500 Pro.",
                "RO: reverse osmosis membrane stage. UV: ultraviolet lamp stage on 500 Pro only.",
                "E-03: three short beeps indicating sediment pre-filter saturation — replace FLT-SED-01 "
                "then hold RESET five seconds.",
            ],
        ),
        (
            "20. Document control",
            [
                "This manual version 2026.1 supersedes 2025.4. Alert code E-06 meaning follows firmware 2.4+ "
                "as documented in the Product Changelog. Always confirm firmware in the app before advising "
                "on E-06.",
                "For warranty, refund, and shipping terms, use the dedicated policy documents — this manual "
                "does not redefine commercial policy windows.",
            ],
        ),
    ]
    for heading, paras in extended:
        story.append(PageBreak())
        story.append(Paragraph(heading, h2))
        for para in paras:
            story.append(Paragraph(para, body))
            story.append(Spacer(1, 4))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Wrote {path}")


def build_installation_guide():
    title, h2, body, small = styles()
    path = KB / "installation_guide.pdf"
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Pearlz Installation Guide",
    )
    story = []
    story.append(Paragraph("Pearlz Installation Guide — AquaPearl Series", title))
    story.append(Paragraph("Document ID: GUIDE-INST-2026.1 | Version 2026.1", small))

    story.append(Paragraph("1. Pre-installation checklist", h2))
    story.append(Paragraph(
        "Confirm inlet water pressure is between 0.1 and 0.4 MPa. Confirm a grounded socket matching the "
        "supplied adapter region. Allow 10 cm clearance on all sides for ventilation. Verify cold-water "
        "feed only — never connect to a hot-water line. Have a bucket and towels ready for the flush.",
        body,
    ))

    story.append(Paragraph("2. Tools required", h2))
    for tool in [
        "Adjustable wrench",
        "PTFE thread tape",
        "Phillips screwdriver",
        "Bucket and absorbent towels",
        "Spirit level (for wall-mount)",
    ]:
        story.append(Paragraph(f"• {tool}", body))

    story.append(Paragraph("3. Wall-mount installation steps", h2))
    story.append(Paragraph(
        "1. Mark mounting holes using the template. 2. Drill and insert wall plugs rated for 15 kg. "
        "3. Hang the unit and verify level. 4. Connect inlet tubing with PTFE tape on threaded joints. "
        "5. Connect drain and purified outlet. 6. Plug in power only after leak-check of dry joints.",
        body,
    ))

    story.append(Paragraph("4. Under-sink installation steps", h2))
    story.append(Paragraph(
        "1. Shut off the cold-water angle valve. 2. Install the feed adaptor. 3. Route tubing without kinks. "
        "4. Place the unit on a stable flat base inside the cabinet. 5. Restore water and inspect for drips "
        "for ten minutes before leaving the site.",
        body,
    ))

    story.append(PageBreak())
    story.append(Paragraph("5. First-run flushing procedure (required)", h2))
    story.append(Paragraph(
        "After installing new filters or a new unit, you must flush before drinking. Why: carbon fines and "
        "membrane preservatives can cause a strange or chalky taste and cloudy water. Procedure: "
        "(1) Open the inlet and power on. (2) Fill the tank completely. (3) Dispense and discard the entire "
        "first tank. (4) Fill again and discard the second tank. (5) The third tank is ready for use. "
        "If taste remains odd, repeat one additional flush cycle. This procedure is the correct response "
        "when customers report weird taste immediately after a filter change.",
        body,
    ))

    story.append(Paragraph("6. Professional installation", h2))
    story.append(Paragraph(
        "Professional installation by a Pearlz Authorised Service Partner can be booked for "
        "PKR 2,500 in metro areas (Karachi, Lahore, Islamabad). Secondary-city rates are quoted on request. "
        "SKU INST-PROF-METRO on the Pricing Guide.",
        body,
    ))

    story.append(Paragraph("7. What voids warranty during self-installation", h2))
    story.append(Paragraph(
        "Connecting to hot water, exceeding inlet pressure without a reducer, using non-Pearlz adapters that "
        "crack fittings, or applying sealant inside electrical compartments voids warranty for the damaged "
        "subsystems. Follow this guide carefully. When unsure, book professional installation.",
        body,
    ))

    for heading, text in [
        (
            "8. Leak check protocol",
            "After pressurising, dry all joints with a paper towel and watch for wicking moisture for ten minutes. "
            "Any drip requires shut-off and re-seating of the fitting before use.",
        ),
        (
            "9. Electrical notes",
            "Use a surge-protected socket where possible. Do not share the circuit with high-draw kitchen heaters "
            "if nuisance trips occur.",
        ),
        (
            "10. Post-install customer briefing",
            "Show the customer the RESET and PAIR buttons, explain filter intervals, and leave the quick-start card "
            "visible. Remind them that filters are consumables and not covered by warranty.",
        ),
    ]:
        story.append(Paragraph(heading, h2))
        story.append(Paragraph(text, body))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Wrote {path}")


def build_service_agreement():
    path = KB / "service_maintenance_agreement.docx"
    d = DocxDocument()
    d.add_heading("Pearlz Home Systems — Service & Maintenance Agreement", level=1)
    d.add_paragraph("Document ID: POL-SVC-2026.1 | Version 2026.1 | Last updated: 15 January 2026")

    d.add_heading("1. Purpose", level=2)
    d.add_paragraph(
        "This agreement describes Annual Maintenance Contract (AMC) tiers, visit frequency, "
        "response-time SLAs, parts coverage, cancellation terms, and the Warranty Claim Procedure "
        "referenced by the Warranty Policy."
    )

    d.add_heading("2. AMC tiers", level=2)
    table = d.add_table(rows=4, cols=4)
    headers = ["Tier", "Visits / year", "Response SLA (metro)", "SKU"]
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
    rows = [
        ["Basic", "1 scheduled", "Next working day for P2+", "AMC-BASIC"],
        ["Plus", "2 scheduled", "8 hours for P2", "AMC-PLUS"],
        ["Premium", "4 scheduled", "24 hours including Sunday for P1/P2 metro", "AMC-PREMIUM"],
    ]
    for r_i, row in enumerate(rows, start=1):
        for c_i, val in enumerate(row):
            table.rows[r_i].cells[c_i].text = val

    d.add_heading("3. What each tier includes", level=2)
    d.add_paragraph(
        "All tiers include inspection, filter condition check, leak check, and firmware verification. "
        "Plus and Premium include one complimentary sediment filter per contract year. Premium includes "
        "priority scheduling and waived call-out fee in metro areas."
    )

    d.add_heading("4. Parts covered vs billed", level=2)
    d.add_paragraph(
        "Labour for covered warranty defects is free during warranty. Under AMC, labour for maintenance "
        "visits is included; replacement filters and out-of-warranty parts are billed at Pricing Guide rates "
        "unless the tier explicitly includes them."
    )

    d.add_heading("5. Cancellation and pro-rata refund", level=2)
    d.add_paragraph(
        "AMC may be cancelled within 14 days of purchase for a full refund if no visit has occurred. "
        "After a visit, refunds are pro-rata on unused whole months minus a PKR 1,000 admin fee."
    )

    d.add_heading("6. Warranty Claim Procedure", level=2)
    d.add_paragraph(
        "This is the procedure referenced by Warranty Policy §6. Follow these steps:"
    )
    for step in [
        "Email support@pearlzhome.example with subject CLAIM and attach invoice, serial number, and fault photos.",
        "Receive a claim reference within one working day (P3) or faster for P1/P2.",
        "Tier-2 validates coverage against Warranty Policy (period, exclusions, unauthorised repair).",
        "If approved, Pearlz schedules repair, replacement of covered parts, or depot service.",
        "If denied (e.g. consumables, unauthorised repair, property damage), Pearlz offers paid service options under this agreement.",
        "Customer must not ship the unit without a claim reference; unauthorised parcels may be refused.",
    ]:
        d.add_paragraph(step, style="List Number")

    d.add_heading("7. Property damage and consequential loss", level=2)
    d.add_paragraph(
        "Neither the Warranty Policy nor this Service Agreement authorises compensation for consequential "
        "property damage (for example, a kitchen cabinet damaged by a leak). Agents must not promise such "
        "compensation. Customers may pursue separate insurance or legal routes; Pearlz support documents "
        "product coverage only."
    )

    d.add_heading("8. Paid out-of-warranty service", level=2)
    d.add_paragraph(
        "When warranty is voided by unauthorised repair or the period has expired, customers may purchase "
        "diagnosis (metro call-out PKR 1,500) plus parts at list price. AMC holders receive discounted labour."
    )

    d.save(path)
    print(f"Wrote {path}")


def main():
    KB.mkdir(parents=True, exist_ok=True)
    build_product_manual()
    build_installation_guide()
    build_service_agreement()
    print("Done.")


if __name__ == "__main__":
    main()
