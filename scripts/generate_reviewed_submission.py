#!/usr/bin/env python3
"""Generate a standalone, plain-English project report from measured CSVs."""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT.parent / "EmergencyNavigation_Reviewed_400m_Submission" / "Emergency_Vehicle_Navigation_Final_Submission.docx"
CONFIGS = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback")
SHORT = ("Fog/Cloud", "Mist", "Mist Dynamic", "Mist + Fog")
DENSITIES = ("low", "medium", "high")
VEHICLES = {"low": 72, "medium": 144, "high": 200}
PRIMARY = (
    ("pdr", "PDR", "ratio"),
    ("nrl", "NRL", "packets/delivery"),
    ("throughput_bps", "EM throughput", "bit/s"),
    ("e2e_delay_ms", "EM end-to-end delay", "ms"),
    ("route_decision_ms", "Route decision latency", "ms"),
    ("ev_response_s", "EV response time", "s"),
    ("traffic_light_wait_s", "EV traffic-light waiting time", "s"),
)
GRAPH_INFO = (
    ("pdr", "Packet delivery ratio", "The share of generated emergency messages that reached the EV. Higher is better."),
    ("nrl", "Normalized routing load", "Control and EM transmissions per delivered emergency message. Lower means less communication overhead."),
    ("throughput_bps", "EM throughput", "Delivered EM payload bits divided by the fixed 900 second observation window. One delivery contributes 2.27556 bit/s."),
    ("e2e_delay_ms", "EM end-to-end delay", "Time from RSU message generation to EV reception, in milliseconds. Lower is faster."),
    ("route_decision_ms", "Route decision latency", "Time from EV message reception to the initial route being applied, in milliseconds."),
    ("ev_response_s", "EV response time", "Time from emergency message generation until the EV reaches the accident, in seconds."),
    ("traffic_light_wait_s", "EV traffic-light waiting time", "EV standstill near a signal stop line, in seconds. A value of zero means no measured wait."),
    ("fallback_triggered", "Fallback activation rate", "Share of fallback-configuration runs where the 800 ms Mist watchdog requested Fog."),
    ("route_changes", "Applied route changes", "Mean number of actual congestion or cost reroutes per run. Reviews without a replacement are excluded."),
    ("route_reviews", "Route computation frequency", "Mean number of periodic Dynamic A* route evaluations per run, normally scheduled every five seconds."),
    ("fallback_decision_ms", "Fallback decision latency", "Time to apply the Fog route in runs where the watchdog actually triggered, in milliseconds."),
    ("control_transmissions", "Control transmissions", "Mean number of control-packet transmissions per run. This is supporting communication-load evidence."),
    ("control_bytes", "Control bytes", "Mean control traffic volume in bytes per run. This is supporting communication-load evidence."),
    ("ev_delay_vs_freeflow_s", "EV corridor delay versus free flow", "Extra travel time relative to the modeled free-flow corridor, in seconds."),
    ("ev_distance_m", "EV route distance", "Distance traveled by the EV to reach the accident, in metres."),
    ("ev_travel_s", "EV travel time", "EV movement time from departure to accident arrival, in seconds."),
)
PROCESS_STEPS = (
    "Create a small road network with 16 junctions and traffic lights. Put three roadside units (RSUs) beside the roads. Each RSU can communicate within a 400 m radio neighborhood.",
    "Add normal traffic to the roads. The low, medium, and high traffic scenarios contain 72, 144, and 200 background vehicles. Thirty random seeds give different trips for each scenario.",
    "Start the emergency event. An accident vehicle stops, and the nearby RSU sends one 256-byte emergency message through the vehicle and roadside network to the emergency vehicle (EV).",
    "When the EV receives the message, calculate a route to the accident using the selected routing configuration. Some configurations use a fixed A* route; the dynamic configurations review live road costs every five seconds.",
    "While the EV drives, it requests priority at traffic lights. Dynamic routing changes the route only when a better route passes the improvement and stability rules.",
    "In the Mist with Fog configuration, Mist normally computes the route. The simulated onboard unit spends an assumed 20 ms validating each recently received road message. If Mist has not finished after 800 ms, Fog takes over the route decision.",
    "Record whether the message arrived, how long communication and route decisions took, how the EV traveled, and how many reviews, route changes, and fallback events occurred. Each run has a 900 second observation window.",
    "Repeat the experiment for four configurations, three traffic levels, and 30 matched seeds: 360 runs. Calculate averages and 95% confidence intervals from the recorded results, then draw the graphs.",
)


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fmt(value: float, key: str) -> str:
    if key == "pdr":
        return f"{value:.3f}"
    if key == "nrl":
        return f"{value:,.0f}"
    if key == "throughput_bps":
        return f"{value:.3f}"
    return f"{value:.1f}"


def graph_value(value: float, key: str) -> str:
    if key in ("pdr", "fallback_triggered", "throughput_bps"):
        return f"{value:.3f}"
    if key in ("route_changes", "route_reviews"):
        return f"{value:.2f}"
    if key in ("nrl", "control_transmissions", "control_bytes"):
        return f"{value:,.0f}"
    return f"{value:.1f}"


def graph_blocks(summary: dict[tuple[str, str, str], dict[str, str]]) -> list[tuple[str, str, str, Path, str]]:
    blocks = []
    for key, label, explanation in GRAPH_INFO:
        for density in DENSITIES:
            path = ROOT / "results/graphs" / f"{key}-{density}.png"
            if not path.exists():
                if key == "fallback_decision_ms" and density == "low":
                    continue  # No low-density fallback; latency is undefined.
                raise SystemExit(f"Missing graph: {path}")
            values = []
            for cfg, short in zip(CONFIGS, SHORT):
                row = summary.get((cfg, density, key))
                if row is not None:
                    values.append(f"{short} {graph_value(float(row['mean']), key)}")
            caption = (f"{density.capitalize()} traffic ({VEHICLES[density]} background vehicles): "
                       + "; ".join(values) + ". Bars show means and 95% confidence intervals.")
            blocks.append((key, label, explanation, path, caption))
    if len(blocks) != 47:
        raise SystemExit(f"Expected all 47 current graphs, found {len(blocks)}")
    return blocks


def write_graph_guide(blocks: list[tuple[str, str, str, Path, str]]) -> None:
    lines = ["# Emergency vehicle navigation: project and graph guide", "",
             "This project studies how an emergency vehicle receives an accident alert and chooses a route through traffic. The Word report contains the complete project explanation and the same 47 graphs.", "",
             "## How the system works", ""]
    for index, step in enumerate(PROCESS_STEPS, 1):
        lines += [f"{index}. {step}", ""]
    lines += ["## How to read the figures", "",
              "Each bar is a density and configuration mean. Error bars show 95% confidence intervals; the exact methods are in [METHODOLOGY.md](METHODOLOGY.md). Metrics requiring EM delivery use only valid delivered runs. PDR, EM throughput, and fallback activation use all 30 scheduled runs where applicable. A missing low-density fallback decision graph means no fallback activated there; it is not a measured latency of zero.", "",
              "## All 47 graphs", ""]
    previous = None
    for key, label, explanation, path, caption in blocks:
        if key != previous:
            lines += [f"### {label}", "", explanation, ""]
            previous = key
        lines += [f"![{label} for {path.stem.rsplit('-', 1)[1]} traffic](../results/graphs/{path.name})", "",
                  caption, ""]
    lines += ["The complete numeric means, valid sample sizes, standard deviations, and intervals are in `../results/processed/summary-batch.csv`. The seven main measures are also tabulated in `VERIFICATION.md`.", ""]
    (ROOT / "docs/PROCESS_AND_GRAPHS.md").write_text("\n".join(lines), encoding="utf-8")


def shade(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def table(doc: Document, headers: tuple[str, ...], body: list[tuple[str, ...]]) -> None:
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    tr_pr = t.rows[0]._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    tr_pr.append(repeat)
    for i, title in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = title
        shade(cell, "1F3957")
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(8)
    for index, values in enumerate(body):
        row = t.add_row()
        for i, value in enumerate(values):
            cell = row.cells[i]
            cell.text = value
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if index % 2:
                shade(cell, "F2F6FA")
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                for run in paragraph.runs:
                    run.font.size = Pt(8)
    doc.add_paragraph()


def heading(doc: Document, title: str, level: int = 1) -> None:
    doc.add_heading(title, level=level)


def main() -> None:
    summary_rows = read(ROOT / "results/processed/summary-batch.csv")
    individual = read(ROOT / "results/processed/individual_runs-batch.csv")
    fallback = read(ROOT / "results/processed/fallback_validation.csv")
    if len(individual) != 360:
        raise SystemExit("The 360-run study is required")
    summary = {(r["configuration"], r["density"], r["metric"]): r for r in summary_rows}
    blocks = graph_blocks(summary)
    real_fallback = [r for r in fallback if r["configuration"] == "MistDynamicFogFallback" and r["fallback_triggered"] == "1"]
    if not real_fallback:
        raise SystemExit("No real batch fallback found")

    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(0.7)
    section.left_margin = section.right_margin = Inches(0.65)
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(9.5)
    normal.font.color.rgb = RGBColor(25, 25, 25)
    normal.paragraph_format.space_after = Pt(6)
    for style_name in ("Title", "Heading 1", "Heading 2"):
        style = doc.styles[style_name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
    title_properties = doc.styles["Title"].element.get_or_add_pPr()
    for border in title_properties.findall(qn("w:pBdr")):
        title_properties.remove(border)
    doc.styles["Title"].font.size = Pt(20)
    doc.styles["Heading 1"].font.size = Pt(14)
    doc.styles["Heading 2"].font.size = Pt(11)

    cover_title = doc.add_paragraph(style="Title")
    cover_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover_title.paragraph_format.space_before = Pt(105)
    cover_title.add_run("Emergency Vehicle Navigation in a Vehicular Network")
    cover_subtitle = doc.add_paragraph()
    cover_subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover_subtitle.paragraph_format.space_before = Pt(18)
    cover_subtitle.add_run("A simulation study of Fog, Mist, dynamic routing, and fallback").italic = True
    cover_details = doc.add_paragraph()
    cover_details.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover_details.paragraph_format.space_before = Pt(105)
    cover_details.add_run("SUMO + OMNeT++ + Veins\n")
    cover_details.add_run("4 routing configurations  |  3 traffic levels  |  30 seeds\n")
    cover_details.add_run("360 simulation runs  |  47 result graphs\n")
    cover_details.add_run("October 2026")
    doc.add_page_break()

    heading(doc, "Project overview")
    doc.add_paragraph(
        "An emergency vehicle needs to reach an accident quickly. It must first learn where the "
        "accident is, then choose a road route while normal traffic keeps moving. This project "
        "tests four ways to make that route decision in a simulated vehicular network."
    )
    doc.add_paragraph(
        "The central question is how the location of route computation, live traffic updates, "
        "and a Fog backup affect message delivery, routing work, and the emergency vehicle's "
        "journey. All four approaches use traffic-light priority for the emergency vehicle."
    )

    heading(doc, "The simulated road and communication system")
    doc.add_paragraph(
        "The road is a 4 by 4 grid of signalized junctions. SUMO moves the vehicles and operates "
        "the traffic lights. OMNeT++ and Veins simulate wireless messages between vehicles and "
        "three roadside units (RSUs). The RSUs have a 400 m communication neighborhood. The "
        "accident vehicle, RSUs, and emergency vehicle exchange the information needed to "
        "start the response."
    )
    doc.add_paragraph(
        "Normal traffic comes in three levels: 72 vehicles in low traffic, 144 in medium traffic, "
        "and 200 in high traffic. Thirty random seeds create different trips at each level. The "
        "same seed and traffic are used for each routing approach so the comparisons are fair."
    )

    heading(doc, "How the system works, step by step")
    for step in PROCESS_STEPS:
        doc.add_paragraph(step, style="List Number")

    heading(doc, "The four routing approaches")
    table(doc, ("Approach", "Plain-English description"), [
        ("FogCloudAStar", "Fog and cloud services calculate the first A* route. The EV follows that route without periodic route reviews."),
        ("MistAStar", "The EV's nearby Mist layer calculates the first A* route. There are no periodic route reviews."),
        ("MistDynamicAStar", "Mist calculates the route and checks live road costs every five seconds. A better, stable route can replace the current route."),
        ("MistDynamicFogFallback", "Dynamic Mist routing runs normally. If the initial Mist decision exceeds the 800 ms watchdog, Fog calculates the route instead."),
    ])
    doc.add_paragraph(
        "A* is a shortest-path search. The dynamic versions use recent vehicle and roadside "
        "messages to estimate changing road costs. A route review is only a check; it counts "
        "as a route change when the EV actually receives a replacement route."
    )

    heading(doc, "What was measured")
    table(doc, ("Main measure", "What it tells us"), [
        ("Packet delivery ratio (PDR)", "The share of accident alerts that reached the emergency vehicle."),
        ("Normalized routing load (NRL)", "The number of message transmissions per delivered accident alert."),
        ("EM throughput", "Delivered emergency-message payload bits per second of the fixed observation window."),
        ("EM end-to-end delay", "Milliseconds from sending the accident alert to its arrival at the emergency vehicle."),
        ("Route decision latency", "Milliseconds from alert reception until the first route is applied."),
        ("EV response time", "Seconds from alert generation until the emergency vehicle reaches the accident."),
        ("EV traffic-light waiting time", "Seconds the emergency vehicle waits near a signal stop line."),
    ])
    doc.add_paragraph(
        "We also counted Fog fallback activations, actual route changes, five-second route "
        "reviews, and the time taken to apply a Fog route after fallback. Each graph shows an "
        "average with a 95% confidence interval."
    )

    heading(doc, "Main results")
    doc.add_paragraph(
        "The accident alert reached the emergency vehicle in 332 of the 360 runs. Delivery "
        "succeeded in 24 of 30 seeds in low traffic, 29 of 30 in medium traffic, and all 30 "
        "in high traffic for each approach. These outcomes reflect this grid and its radio "
        "connections; they do not imply that heavier traffic always improves delivery."
    )
    doc.add_paragraph(
        "The tables give the average, its 95% confidence interval in brackets, and the "
        "number of valid runs. Delivery ratio and EM throughput use all 30 runs at each "
        "traffic level. Travel and timing measures use runs in which the alert arrived."
    )
    for density in DENSITIES:
        heading(doc, f"{density.capitalize()} traffic", 2)
        data = []
        for key, label, unit in PRIMARY:
            cells = []
            for cfg in CONFIGS:
                r = summary[(cfg, density, key)]
                cells.append(f"{fmt(float(r['mean']), key)}\n[{fmt(float(r['ci95_lower']), key)}, {fmt(float(r['ci95_upper']), key)}]\nn={r['n']}")
            data.append((f"{label}\n({unit})", *cells))
        table(doc, ("Metric", *SHORT), data)

    heading(doc, "What the main results mean")
    doc.add_paragraph(
        "Message delivery and end-to-end delay are the same across the four approaches at "
        "each traffic level because the alert travels through the same network before the "
        "route calculation starts. Average end-to-end delay is 44.36 ms in low traffic, "
        "37.12 ms in medium traffic, and 32.17 ms in high traffic for delivered alerts."
    )
    doc.add_paragraph(
        "The clearest difference between approaches is the first route decision. Fog/Cloud "
        "averages about 626.54 ms at every traffic level. Mist averages 625.17 ms in low "
        "traffic, 844.62 ms in medium traffic, and 1075.33 ms in high traffic. Mist with Fog "
        "fallback averages 946.38 ms in medium traffic and 1087.24 ms in high traffic "
        "because the Fog takeover adds time in runs that exceed the watchdog."
    )
    doc.add_paragraph(
        "The emergency vehicle's average response time stays near 142 seconds in this "
        "network. Measured traffic-light waiting is zero in low and medium traffic. In high "
        "traffic, the two dynamic approaches average 0.13 seconds of waiting. These small "
        "differences should be read alongside the confidence intervals."
    )

    heading(doc, "Fallback and route changes")
    body = []
    for density in DENSITIES:
        group = [r for r in individual if r["density"] == density and r["configuration"] == "MistDynamicFogFallback"]
        count = sum(int(float(r["fallback_triggered"])) for r in group)
        dynamic = [r for r in individual if r["density"] == density and r["configuration"] == "MistDynamicAStar"]
        body.append((density.capitalize(), f"{count}/30 ({count/30:.1%})",
                     str(sum(int(float(r["route_changes"])) for r in dynamic)),
                     str(sum(int(float(r["route_reviews"])) for r in dynamic)),
                     str(sum(int(float(r["route_changes"])) for r in group)),
                     str(sum(int(float(r["route_reviews"])) for r in group))))
    table(doc, ("Traffic", "Fog takeovers", "Dynamic Mist route changes", "Dynamic Mist reviews", "Mist + Fog route changes", "Mist + Fog reviews"), body)
    example = real_fallback[0]
    doc.add_paragraph(
        "Fog took over in 45 of the 90 Mist with Fog runs: zero in low traffic, 18 in "
        "medium traffic, and 27 in high traffic. The trigger is a modeled queue of recently "
        "received vehicle and roadside messages that the onboard unit checks before using "
        "its route. Each check adds an assumed 20 ms of service time. This is a simulation "
        "assumption, not a measured processor benchmark. For example, in medium traffic "
        f"seed {example['seed']}, the Mist decision exceeded 800 ms and Fog applied the route "
        f"after {float(example['final_decision_latency_ms']):.2f} ms."
    )
    doc.add_paragraph(
        "Dynamic Mist reviewed routes 625, 758, and 784 times across the 30 low, medium, "
        "and high traffic runs, but actually changed them only 3, 6, and 6 times. Most "
        "reviews therefore kept the current route. Mist with Fog produced 3, 5, and 5 "
        "route changes across those traffic levels."
    )

    heading(doc, "Why EM throughput appears flat")
    doc.add_paragraph(
        "The accident alert has a fixed 256-byte useful payload. Throughput divides the "
        "delivered alert bits by the same 900 second window in every run. One successful "
        "delivery therefore contributes 2.27556 bit/s, regardless of how many normal "
        "vehicles are on the road. This measure describes emergency-message delivery over "
        "the observation window; it is not the total capacity of the wireless network."
    )
    doc.add_paragraph(
        "Traffic does change with density: the scenarios contain 72, 144, or 200 normal "
        "vehicles; trip starting points differ between random seeds; and the dynamic route "
        "logs contain different live road costs and route changes. The similar throughput "
        "bars follow from the fixed message size and fixed measurement window."
    )

    heading(doc, "Conclusion and limits")
    doc.add_paragraph(
        "The four approaches delivered alerts at the same rate within each traffic level. "
        "Dynamic routing checked current road conditions many times and made a small number "
        "of actual route changes. The Fog backup activated under the modeled Mist workload, "
        "especially in medium and high traffic. In this grid, its extra decision time did "
        "not produce a clear response-time advantage."
    )
    doc.add_paragraph(
        "These findings apply to the simulated 4 by 4 grid, three RSUs, 400 m radio setting, "
        "traffic scenarios, and assumed onboard message-check time. They should be tested "
        "on other road layouts and with measured onboard processing times before being "
        "generalized to real emergency deployments."
    )

    heading(doc, "How to read every graph")
    doc.add_paragraph(
        "Each bar is a mean for one configuration at one density. Error bars show the 95% "
        "confidence interval; the method used for each metric is specified in docs/METHODOLOGY.md. "
        "PDR and EM throughput include all 30 scheduled runs. Delivery-dependent measures "
        "use only runs with a delivered emergency message. A graph can contain fewer than "
        "four bars when a metric applies only to dynamic routing or fallback."
    )
    doc.add_paragraph(
        "There is no low-traffic fallback decision-latency graph because none of the 30 "
        "low-traffic Mist with Fog runs needed a takeover. That latency has no value there. "
        "The following gallery contains all 47 result graphs."
    )

    heading(doc, "Complete graph gallery")
    previous = None
    for number, (key, label, explanation, path, caption) in enumerate(blocks, 1):
        if key != previous:
            heading(doc, label, 2)
            doc.add_paragraph(explanation)
            previous = key
        figure = doc.add_picture(str(path), width=Inches(6.1))
        figure_paragraph = doc.paragraphs[-1]
        figure_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        figure_paragraph.paragraph_format.keep_with_next = True
        description = doc.add_paragraph(f"Figure {number}. {caption}")
        description.paragraph_format.space_after = Pt(10)
        description.paragraph_format.keep_together = True
    doc.add_paragraph(
        "Detailed metric definitions and model assumptions are in METHODOLOGY.md. "
        "The processed data and individual graph files accompany this report."
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    shutil.copy2(OUTPUT, ROOT / "docs" / OUTPUT.name)
    write_graph_guide(blocks)
    print(OUTPUT)


if __name__ == "__main__":
    main()
