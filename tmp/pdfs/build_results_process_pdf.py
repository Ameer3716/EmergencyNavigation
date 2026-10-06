from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
    PageBreak, Preformatted,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/pdf/EmergencyNavigation_Results_Generation_Process.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

NAVY = colors.HexColor("#18324B")
BLUE = colors.HexColor("#25617F")
PALE = colors.HexColor("#EAF2F6")
GRAY = colors.HexColor("#4C5963")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="DocTitleX", fontName="Helvetica-Bold", fontSize=20,
                          leading=25, textColor=NAVY, spaceAfter=10))
styles.add(ParagraphStyle(name="SubtitleX", fontName="Helvetica", fontSize=10,
                          leading=15, textColor=GRAY, spaceAfter=16))
styles.add(ParagraphStyle(name="SectionX", fontName="Helvetica-Bold", fontSize=12.5,
                          leading=16, textColor=NAVY, spaceBefore=15, spaceAfter=7,
                          keepWithNext=True))
styles.add(ParagraphStyle(name="SubsectionX", fontName="Helvetica-Bold", fontSize=10.5,
                          leading=14, textColor=BLUE, spaceBefore=9, spaceAfter=5,
                          keepWithNext=True))
styles.add(ParagraphStyle(name="BodyX", fontName="Helvetica", fontSize=9.2,
                          leading=14.2, spaceAfter=7))
styles.add(ParagraphStyle(name="SmallX", fontName="Helvetica", fontSize=8,
                          leading=11.5, spaceAfter=4))
styles.add(ParagraphStyle(name="TableHeadX", parent=styles["SmallX"],
                          fontName="Helvetica-Bold", textColor=colors.white))
styles.add(ParagraphStyle(name="BulletX", parent=styles["BodyX"], leftIndent=13,
                          firstLineIndent=-9, spaceAfter=4))
styles.add(ParagraphStyle(name="CodeX", fontName="Courier", fontSize=7.5,
                          leading=11, leftIndent=8, backColor=PALE, borderPadding=8,
                          spaceBefore=5, spaceAfter=8))
styles.add(ParagraphStyle(name="CalloutX", fontName="Helvetica-Bold", fontSize=9.2,
                          leading=14, textColor=NAVY, backColor=PALE,
                          borderPadding=10, spaceBefore=7, spaceAfter=12))

story = []


def p(text, style="BodyX"):
    story.append(Paragraph(text, styles[style]))


def bullet(text):
    p("&#8226; " + text, "BulletX")


def section(text):
    p(text, "SectionX")


def subsection(text):
    p(text, "SubsectionX")


def table(rows, widths, header=True):
    t = Table([[Paragraph(str(c), styles["TableHeadX"] if header and i == 0 else styles["SmallX"])
                for c in row] for i, row in enumerate(rows)],
              colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY if header else PALE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white if header else NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F8FA")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#C7D6DE")),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))


p("Simulation Results: Methods and Verification", "DocTitleX")
p("Emergency vehicle navigation study | 27 September 2026", "SubtitleX")
p("The results were produced by coupling road traffic and wireless-network simulation. SUMO 1.18.0 models vehicle movement and traffic signals; OMNeT++ 6.3.0 with Veins 5.3.1 models communication and application logic. TraCI links the simulators. The comparison covers five configurations, three traffic densities, and 30 matched random seeds: <b>450 completed runs</b>.", "CalloutX")

section("1. What was simulated")
p("The scenario uses a 4 x 4 road grid with 16 signalized intersections, three roadside units (RSUs), ordinary vehicles, an accident vehicle, and an emergency vehicle (EV). Background traffic is generated at low, medium, and high densities. The accident is initiated at simulation time 60 s; after standstill detection, the nearby RSU generates an emergency message. The EV receives that message, computes a route, travels toward the incident, and may request signal preemption.")
p("The simulation runs to 900 s with a 0.5 s SUMO step. Wireless beacons and RSU traffic summaries inform routing. The same road geometry, accident placement, and generated traffic demand are used when comparing configurations at a given density and seed. This matched design helps isolate the effect of the routing/preemption configuration.")

section("2. Comparison design")
table([
    ["Configuration", "Route behavior", "Signal preemption"],
    ["FogCloudAStar", "Static A* through fog/cloud services", "Enabled"],
    ["MistAStar", "Static A* on the EV onboard unit", "Enabled"],
    ["MistDynamicAStar", "Dynamic A* on the EV; checks routes every 5 s", "Enabled"],
    ["MistDynamicFogFallback", "Dynamic mist routing with 800 ms fog failover watchdog", "Enabled"],
    ["NoPreemptionBaseline", "Same static route approach as FogCloudAStar", "Disabled"],
], [135, 268, 88])
p("Each of these five configurations is run for seeds 1-30 at each of the three densities. Separate diagnostic runs deliberately trigger a mist failure, a mist timeout, and a congestion reroute to test those mechanisms. Those diagnostic cases are not part of the 450-run comparison matrix.")

section("3. From scenario to raw evidence")
p("For each density and seed, <b>scripts/generate_demand.py</b> creates a seeded SUMO route file for ordinary traffic. <b>scripts/run_batch.py</b> builds the matching SUMO and OMNeT++ configuration, starts each selected case through <b>opp_run</b>, and copies completed outputs to <b>results/raw/</b>. The WSL wrapper <b>scripts/run_batch_env.sh</b> sets the toolchain paths and starts the SUMO launch daemon on port 9998 if needed.")
p("Every run produces OMNeT++ scalar (<b>.sca</b>), vector (<b>.vec</b>), and vector-index (<b>.vci</b>) files. CSV event logs record emergency-message actions, routing decisions, vehicle mobility, fallback actions, and signal phase changes under <b>artifacts/logs/batch/</b>. These files are the evidence used to derive the tables and figures.")

story.append(PageBreak())
section("4. How a single run becomes a data row")
p("<b>analysis/process_results.py</b> reads each raw scalar file and the corresponding emergency-event CSV. It identifies generated and EV-processed emergency messages by message ID, calculates message metrics from event timestamps, and reads mobility and routing measurements from named OMNeT++ scalars. It writes one record per run to <b>results/processed/individual_runs-batch.csv</b>.")
table([
    ["Metric", "Calculation / observation"],
    ["Packet delivery ratio (PDR)", "Unique emergency messages processed by EV / unique messages generated"],
    ["Message end-to-end delay", "EV processing time - emergency message generation time, for delivered messages"],
    ["EV response time", "EV arrival time at accident destination - message generation time"],
    ["Route decision latency", "Time from route computation start to route application on EV"],
    ["Traffic light waiting", "Cumulative near-standstill time (speed below 0.1 m/s) within 20 m of a stop line"],
    ["Delay vs. free flow", "max(0, EV travel time - 140 s green-wave reference)"],
    ["Useful throughput", "Delivered emergency-message payload bits / 900 s"],
    ["Normalized routing load", "Control plus emergency transmissions / delivered unique emergency messages"],
], [151, 340])
p("Other recorded measures include EV travel time, distance, control transmissions, and control bytes. A missing arrival or delivery does not become a zero-second response: conditional metrics remain unavailable for that run. This distinction is important when interpreting averages.")

section("5. Aggregation and statistical comparison")
p("The processor groups per-run records by configuration and traffic density. <b>results/processed/summary-batch.csv</b> contains each metric's mean, sample standard deviation, valid sample count, and 95% confidence interval. For ordinary continuous metrics the interval uses Student's t distribution. Nonnegative, often zero-heavy waiting and free-flow-delay measures use a percentile bootstrap with 10,000 resamples and fixed seed 42. PDR uses a bounded Wilson score interval.")
p("<b>results/processed/paired_comparisons.csv</b> compares selected configurations seed by seed at the same density. It records the mean paired difference, confidence interval, two-sided paired t-test p-value, and Cohen's d<sub>z</sub>. Matching seeds reduces noise from traffic-demand variation.")
p("Network delivery is assessed over all <b>30 scheduled runs per configuration and density</b>. In the documented batch, the emergency message reached the EV in 28/30 low-density, 29/30 medium-density, and 28/30 high-density seeds. Thus arrival-based metrics use the delivered/arrived subset (n=28, 29, or 28), while PDR retains N=30. Across five configurations, this corresponds to 425 delivered cases and 25 genuine partition cases in the 450-run matrix.")

section("6. Graph generation")
p("The processing script renders one figure for each of 12 metric families at each density (36 density-specific figures) under <b>results/graphs/</b>. Bar heights are metric means, and error bars show the appropriate 95% interval. It also writes <b>results/processed/graph_plot_data.csv</b>, so plotted means, limits, and sample sizes can be inspected as data. <b>scripts/generate_final_graph.py</b> separately creates the three-panel EV response-time figure from the summary CSV.")

story.append(PageBreak())
section("7. How the results were checked")
bullet("The run matrix and raw outputs are audited against the intended 5 x 3 x 30 experimental design.")
bullet("<b>scripts/verify_response_times.py</b> independently checks response-time values against timestamps and raw simulation results; the project records 425/425 delivered response times verified, with 25 partition cases marked not applicable.")
bullet("<b>scripts/audit_batch.py</b> checks the batch outputs, processed tables, graph data, and supporting evidence and writes <b>artifacts/audit_report.json</b>.")
bullet("<b>scripts/validate_integrated.py</b> and the targeted diagnostic runs check routing, message forwarding, watchdog fallback, traffic-signal phase changes, and arrival behavior.")
bullet("The checksum generation script can create a manifest for a locally reproduced output package. Figure image hashes can vary with the rendering environment even when the underlying table values match.")

section("8. Reproduction sequence")
p("The repository's <b>README.md</b> and <b>docs/INSTALLATION.md</b> provide environment setup. The core sequence, from the project root, is:")
story.append(Preformatted(
    "# Build the OMNeT++ project library in the configured opp_env WSL environment\n"
    "bash scripts/build.sh\n\n"
    "# Run five configurations, three densities, seeds 1-30\n"
    "bash scripts/run_batch_env.sh --configs FogCloudAStar MistAStar \\\n"
    "  MistDynamicAStar MistDynamicFogFallback NoPreemptionBaseline \\\n"
    "  --densities low medium high --seed-start 1 --seed-end 30\n\n"
    "# With Python analysis dependencies installed\n"
    "python analysis/process_results.py --batch --require-all\n"
    "python scripts/generate_final_graph.py\n"
    "python analysis/extract_fallback_evidence.py\n"
    "python scripts/verify_response_times.py\n"
    "python scripts/audit_batch.py",
    styles["CodeX"]
))
p("The batch runner skips cases whose three raw files already exist and are nonempty unless <b>--force</b> is supplied. The repository README notes that a fresh source checkout may not include the original complete evidence package; reproducing the published tables requires running the matrix or using the corresponding raw outputs and logs.")

section("9. Interpretation")
p("The comparisons describe performance within the specified road grid, traffic demand, radio model, routing rules, and signal-control logic. Emergency messages were delivered in 425 of the 450 runs; response-time and arrival-based summaries therefore use the applicable delivered cases. The study provides simulation evidence, not measurements from vehicles deployed on public roads.")

section("Source files used for this explanation")
p("Project documentation: <b>README.md</b>, <b>docs/METHODOLOGY.md</b>, <b>docs/EXPERIMENTS.md</b>, and <b>docs/VERIFICATION.md</b>. Pipeline code: <b>scripts/run_batch.py</b>, <b>scripts/run_batch_env.sh</b>, <b>analysis/process_results.py</b>, <b>scripts/generate_final_graph.py</b>, and <b>scripts/audit_batch.py</b>.", "SmallX")


def decorate(canvas, doc):
    canvas.saveState()
    w, h = doc.pagesize
    canvas.setStrokeColor(colors.HexColor("#D6E2E8"))
    canvas.line(47, h - 38, w - 47, h - 38)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(47, 31, "EmergencyNavigation | Methods and verification")
    canvas.drawRightString(w - 47, 31, f"Page {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=(595.28, 841.89),
                        rightMargin=48, leftMargin=48, topMargin=57,
                        bottomMargin=51, title="EmergencyNavigation Simulation Results: Methods and Verification",
                        author="EmergencyNavigation project")
doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
print(OUT)
