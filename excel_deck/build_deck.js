const pptxgen = require("pptxgenjs");
const { FaBoxOpen, FaShippingFast, FaMapMarkerAlt, FaChartLine } = require("react-icons/fa");
const { iconToBase64Png } = require("./icons.js");

// Palette: deep navy dominant, steel blue secondary, coral red accent
// (content-informed: logistics/delivery risk theme, navy = trust/scale,
// coral reserved strictly for risk/urgency figures)
const NAVY = "1B263B";
const STEEL = "415A77";
const STEEL_LIGHT = "778DA9";
const CORAL = "E63946";
const WHITE = "FFFFFF";
const OFFWHITE = "F7F7F5";
const LIGHT_TEXT = "E0E1DD";
const DARK_TEXT = "1B263B";
const MUTED = "8D99AE";

async function build() {
  let pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
  pres.author = "Pranay Sawant";
  pres.title = "RetailIQ - Executive Summary";

  const boxIconWhite = await iconToBase64Png(FaBoxOpen, "#FFFFFF", 256);
  const boxIconNavy = await iconToBase64Png(FaBoxOpen, "#" + NAVY, 256);
  const shipIconWhite = await iconToBase64Png(FaShippingFast, "#FFFFFF", 256);
  const mapIconWhite = await iconToBase64Png(FaMapMarkerAlt, "#FFFFFF", 256);
  const chartIconWhite = await iconToBase64Png(FaChartLine, "#FFFFFF", 256);

  // ============================================================
  // SLIDE 1: SITUATION (dark, title slide)
  // ============================================================
  let s1 = pres.addSlide();
  s1.background = { color: NAVY };

  // Icon motif in colored circle, top-left
  s1.addShape(pres.shapes.OVAL, {
    x: 0.6, y: 0.55, w: 0.85, h: 0.85,
    fill: { color: STEEL }, line: { type: "none" },
  });
  s1.addImage({ data: boxIconWhite, x: 0.83, y: 0.78, w: 0.4, h: 0.4 });

  s1.addText("RetailIQ", {
    x: 0.6, y: 1.6, w: 8, h: 0.7, fontSize: 40, bold: true, color: WHITE,
    fontFace: "Cambria", margin: 0,
  });
  s1.addText("Protecting Revenue at Risk from Delivery Delays", {
    x: 0.6, y: 2.3, w: 8.5, h: 0.6, fontSize: 20, color: STEEL_LIGHT,
    fontFace: "Calibri", italic: true, margin: 0,
  });
  s1.addText("Olist Brazilian E-Commerce Marketplace · ~100K Orders, 2017-2018", {
    x: 0.6, y: 2.85, w: 8.5, h: 0.4, fontSize: 13, color: MUTED,
    fontFace: "Calibri", margin: 0,
  });

  // Stat callouts row
  const stats1 = [
    ["R$15.84M", "Total Revenue Analyzed"],
    ["99,441", "Orders, 2017-2018"],
    ["3,095", "Active Sellers"],
  ];
  stats1.forEach((stat, i) => {
    const x = 0.6 + i * 2.9;
    s1.addText(stat[0], {
      x, y: 3.7, w: 2.6, h: 0.75, fontSize: 32, bold: true, color: WHITE,
      fontFace: "Cambria", margin: 0,
    });
    s1.addText(stat[1], {
      x, y: 4.45, w: 2.6, h: 0.4, fontSize: 12, color: STEEL_LIGHT,
      fontFace: "Calibri", margin: 0,
    });
  });

  // Revenue trend chart, right side
  const monthLabels = ["2017-01","2017-04","2017-07","2017-10","2018-01","2018-04","2018-07"];
  const monthValues = [280, 380000, 670000, 900000, 1170000, 1150000, 1040000];
  s1.addChart(pres.charts.LINE, [{ name: "Monthly Revenue (R$)", labels: monthLabels, values: monthValues }], {
    x: 9.0, y: 1.5, w: 3.7, h: 3.4,
    lineSize: 2.5, lineSmooth: true, chartColors: [CORAL],
    chartArea: { fill: { color: NAVY } },
    plotArea: { fill: { color: NAVY } },
    catAxisLabelColor: MUTED, valAxisLabelColor: MUTED,
    catAxisLabelFontSize: 8, valAxisLabelFontSize: 8,
    valGridLine: { color: STEEL, size: 0.5 },
    catGridLine: { style: "none" },
    showTitle: true, title: "Monthly Revenue Trend", titleColor: WHITE, titleFontSize: 11,
    showLegend: false, lineDataSymbol: "circle", lineDataSymbolSize: 4,
  });

  s1.addText("Source: Olist public e-commerce dataset · Analysis by Pranay Sawant", {
    x: 0.6, y: 6.95, w: 8, h: 0.3, fontSize: 9, color: MUTED, fontFace: "Calibri", margin: 0,
  });

  s1.addNotes(
    "Open with the revenue growth story - this marketplace scaled from near zero to over a million reais " +
    "monthly within about a year. That growth is the backdrop; the real story is in the next slide."
  );

  // ============================================================
  // SLIDE 2: COMPLICATION (light background, sandwich structure)
  // ============================================================
  let s2 = pres.addSlide();
  s2.background = { color: OFFWHITE };

  s2.addShape(pres.shapes.OVAL, {
    x: 0.6, y: 0.45, w: 0.7, h: 0.7,
    fill: { color: CORAL }, line: { type: "none" },
  });
  s2.addImage({ data: shipIconWhite, x: 0.79, y: 0.64, w: 0.32, h: 0.32 });

  s2.addText("Delivery Delays Are Costing Real Revenue", {
    x: 1.5, y: 0.5, w: 11, h: 0.65, fontSize: 28, bold: true, color: DARK_TEXT,
    fontFace: "Cambria", margin: 0, valign: "middle",
  });

  // Big risk callout card
  s2.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 1.5, w: 3.7, h: 2.5, rectRadius: 0.08,
    fill: { color: WHITE },
    shadow: { type: "outer", color: "000000", blur: 8, offset: 3, angle: 45, opacity: 0.12 },
  });
  s2.addText("R$607,588", {
    x: 0.85, y: 1.65, w: 3.2, h: 0.7, fontSize: 34, bold: true, color: CORAL,
    fontFace: "Cambria", margin: 0,
  });
  s2.addText("in revenue tied to orders delivered 7+ days late", {
    x: 0.85, y: 2.35, w: 3.2, h: 0.55, fontSize: 13, color: DARK_TEXT,
    fontFace: "Calibri", margin: 0,
  });
  s2.addText("4.28 → 1.73 / 5", {
    x: 0.85, y: 2.95, w: 3.2, h: 0.4, fontSize: 17, bold: true, color: NAVY,
    fontFace: "Calibri", margin: 0,
  });
  s2.addText("avg review score: on-time vs. 7+ days late", {
    x: 0.85, y: 3.35, w: 3.2, h: 0.35, fontSize: 11, color: MUTED,
    fontFace: "Calibri", margin: 0,
  });

  // Review score by delivery bucket - column chart
  s2.addChart(pres.charts.BAR, [{
    name: "Avg Review Score",
    labels: ["On Time", "Late 1-7 Days", "Late 7+ Days"],
    values: [4.28, 3.16, 1.73],
  }], {
    x: 4.6, y: 1.5, w: 3.9, h: 3.3, barDir: "col",
    chartColors: ["2A9D8F", "F4A261", CORAL],
    chartArea: { fill: { color: WHITE } },
    catAxisLabelColor: MUTED, valAxisLabelColor: MUTED,
    catAxisLabelFontSize: 9, valAxisLabelFontSize: 9,
    valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: DARK_TEXT, dataLabelFontSize: 10,
    dataLabelFormatCode: "0.00",
    showLegend: false,
    showTitle: true, title: "Avg Review Score by Delivery Performance", titleColor: DARK_TEXT, titleFontSize: 12,
    valAxisMaxVal: 5,
  });

  // Late delivery rate by state - bar chart
  s2.addChart(pres.charts.BAR, [{
    name: "Late Delivery Rate %",
    labels: ["AL", "MA", "PI", "CE"],
    values: [23.9, 19.7, 16.0, 15.3],
  }], {
    x: 8.85, y: 1.5, w: 3.9, h: 3.3, barDir: "bar",
    chartColors: [STEEL],
    chartArea: { fill: { color: WHITE } },
    catAxisLabelColor: MUTED, valAxisLabelColor: MUTED,
    catAxisLabelFontSize: 9, valAxisLabelFontSize: 9,
    valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: DARK_TEXT, dataLabelFontSize: 10,
    dataLabelFormatCode: "0.0",
    showLegend: false,
    showTitle: true, title: "Late Delivery Rate by State (%)", titleColor: DARK_TEXT, titleFontSize: 12,
  });

  s2.addText(
    "These 4 states (Alagoas, Maranhão, Piauí, Ceará) have late-delivery rates 2-3x the national average (8.1%) " +
    "and disproportionately drive the revenue tied to severe customer dissatisfaction.",
    {
      x: 0.6, y: 4.25, w: 3.7, h: 1.1, fontSize: 11.5, color: DARK_TEXT,
      fontFace: "Calibri", margin: 0, valign: "top",
    }
  );

  s2.addText("Source: RetailIQ SQL analysis (sql/02_analysis.sql, Q4-Q5) · Olist e-commerce dataset", {
    x: 0.6, y: 6.95, w: 8, h: 0.3, fontSize: 9, color: MUTED, fontFace: "Calibri", margin: 0,
  });

  s2.addNotes(
    "The core finding: late delivery doesn't just inconvenience customers, it correlates with a review score " +
    "collapse from 4.28 to 1.73. Four specific states drive most of this risk - that's the lever we have."
  );

  // ============================================================
  // SLIDE 3: RECOMMENDATION (dark, sandwich close)
  // ============================================================
  let s3 = pres.addSlide();
  s3.background = { color: NAVY };

  s3.addShape(pres.shapes.OVAL, {
    x: 0.6, y: 0.45, w: 0.7, h: 0.7,
    fill: { color: STEEL }, line: { type: "none" },
  });
  s3.addImage({ data: mapIconWhite, x: 0.79, y: 0.64, w: 0.32, h: 0.32 });

  s3.addText("Recommendation: Target the 4 Worst States First", {
    x: 1.5, y: 0.5, w: 11.2, h: 0.65, fontSize: 26, bold: true, color: WHITE,
    fontFace: "Cambria", margin: 0, valign: "middle",
  });

  s3.addText(
    "Prioritize logistics intervention in AL, MA, PI, and CE rather than a blanket overhaul. " +
    "Even the conservative scenario protects meaningful revenue — the recommendation holds under a pessimistic assumption, not just the best case.",
    {
      x: 0.6, y: 1.35, w: 12, h: 0.6, fontSize: 13, color: STEEL_LIGHT,
      fontFace: "Calibri", italic: true, margin: 0,
    }
  );

  // Sensitivity table
  const tableRows = [
    [
      { text: "Scenario", options: { bold: true, color: WHITE, fill: { color: STEEL }, fontFace: "Calibri", fontSize: 12 } },
      { text: "Approach", options: { bold: true, color: WHITE, fill: { color: STEEL }, fontFace: "Calibri", fontSize: 12 } },
      { text: "Orders Shifted", options: { bold: true, color: WHITE, fill: { color: STEEL }, fontFace: "Calibri", fontSize: 12, align: "right" } },
      { text: "Revenue Protected", options: { bold: true, color: WHITE, fill: { color: STEEL }, fontFace: "Calibri", fontSize: 12, align: "right" } },
    ],
    [
      { text: "Conservative", options: { color: DARK_TEXT, fill: { color: WHITE }, fontFace: "Calibri", fontSize: 12, bold: true } },
      { text: "Each state -5 percentage points", options: { color: DARK_TEXT, fill: { color: WHITE }, fontFace: "Calibri", fontSize: 11 } },
      { text: "159", options: { color: DARK_TEXT, fill: { color: WHITE }, fontFace: "Calibri", fontSize: 12, align: "right" } },
      { text: "R$30,680", options: { color: DARK_TEXT, fill: { color: WHITE }, fontFace: "Calibri", fontSize: 12, align: "right", bold: true } },
    ],
    [
      { text: "Moderate", options: { color: DARK_TEXT, fill: { color: "F1F4F8" }, fontFace: "Calibri", fontSize: 12, bold: true } },
      { text: "All 4 states reach national avg (8.1%)", options: { color: DARK_TEXT, fill: { color: "F1F4F8" }, fontFace: "Calibri", fontSize: 11 } },
      { text: "307", options: { color: DARK_TEXT, fill: { color: "F1F4F8" }, fontFace: "Calibri", fontSize: 12, align: "right" } },
      { text: "R$59,394", options: { color: DARK_TEXT, fill: { color: "F1F4F8" }, fontFace: "Calibri", fontSize: 12, align: "right", bold: true } },
    ],
    [
      { text: "Optimistic", options: { color: DARK_TEXT, fill: { color: WHITE }, fontFace: "Calibri", fontSize: 12, bold: true } },
      { text: "All 4 states match best state (2.9%)", options: { color: DARK_TEXT, fill: { color: WHITE }, fontFace: "Calibri", fontSize: 11 } },
      { text: "473", options: { color: DARK_TEXT, fill: { color: WHITE }, fontFace: "Calibri", fontSize: 12, align: "right" } },
      { text: "R$91,362", options: { color: DARK_TEXT, fill: { color: WHITE }, fontFace: "Calibri", fontSize: 12, align: "right", bold: true } },
    ],
  ];
  s3.addTable(tableRows, {
    x: 0.6, y: 2.15, w: 7.6, colW: [1.7, 3.5, 1.2, 1.2],
    border: { pt: 0.5, color: "D0D5DD" }, autoPage: false, rowH: 0.55,
  });

  // Next steps icon rows
  s3.addText("Next Steps", {
    x: 8.6, y: 2.15, w: 4, h: 0.4, fontSize: 15, bold: true, color: WHITE,
    fontFace: "Cambria", margin: 0,
  });

  const nextSteps = [
    "Pilot expedited carrier in AL, MA, PI, CE",
    "A/B test against a 5pp on-time-rate improvement target",
    "Track On-Time Delivery Rate as the North Star metric",
  ];
  nextSteps.forEach((step, i) => {
    const y = 2.7 + i * 0.85;
    s3.addShape(pres.shapes.OVAL, {
      x: 8.6, y: y, w: 0.45, h: 0.45,
      fill: { color: STEEL }, line: { type: "none" },
    });
    s3.addText(String(i + 1), {
      x: 8.6, y: y, w: 0.45, h: 0.45, fontSize: 14, bold: true, color: WHITE,
      fontFace: "Calibri", align: "center", valign: "middle", margin: 0,
    });
    s3.addText(step, {
      x: 9.2, y: y - 0.05, w: 3.5, h: 0.6, fontSize: 12, color: LIGHT_TEXT,
      fontFace: "Calibri", margin: 0, valign: "middle",
    });
  });

  s3.addText(
    "Live dashboard: retailiq-wq4exudkd9nfhh8aio6yjy.streamlit.app  ·  Full analysis: github.com/psawant14890-wq/retailiq",
    { x: 0.6, y: 6.95, w: 12, h: 0.3, fontSize: 9.5, color: MUTED, fontFace: "Calibri", margin: 0 }
  );

  s3.addNotes(
    "Close with the sensitivity range - even the conservative scenario, with no rosy assumptions, protects " +
    "over R$30,000. That's the floor, not the ceiling. Point to the live dashboard if asked to go deeper."
  );

  await pres.writeFile({ fileName: "RetailIQ_Executive_Deck.pptx" });
  console.log("Deck written.");
}

build().catch((e) => { console.error(e); process.exit(1); });
