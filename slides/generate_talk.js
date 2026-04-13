const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");

// ─── CONSTANTS ───────────────────────────────────────────────────────────────

const IMG = path.join(__dirname, "..", "static", "images");
const OUT = path.join(__dirname, "caveagent_talk.pptx");

const C = {
  brown:      "B5784E",
  darkBrown:  "3C2415",
  blue:       "054488",
  green:      "056B34",
  orange:     "FF8800",
  bg:         "F9F6F2",
  darkBg:     "2C1810",
  resultHi:   "EBF5EB",
  positive:   "009688",
  white:      "FFFFFF",
  lightGray:  "F5F5F5",
  medGray:    "E8E4E0",
  textGray:   "666666",
  lightText:  "D4C4B0",
  codeFont:   "Consolas",
  bodyFont:   "Calibri",
};

const W = 13.333;
const H = 7.5;
const MX = 0.6;
const CONTENT_W = W - 2 * MX;
const CONTENT_Y = 1.5;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "CaveAgent Team";
pres.title = "CaveAgent: Transforming LLMs into Stateful Runtime Operators";

// ─── HELPERS ─────────────────────────────────────────────────────────────────

function cardShadow() {
  return { type: "outer", color: "000000", blur: 4, offset: 2, angle: 135, opacity: 0.1 };
}

let slideNum = 0;
function addSlideNumber(slide, darkBg) {
  slideNum++;
  slide.addText(String(slideNum), {
    x: W - 0.8, y: H - 0.45, w: 0.5, h: 0.3,
    fontSize: 11, color: darkBg ? C.lightText : C.textGray, fontFace: C.bodyFont, align: "right",
  });
}

function addTitleBar(slide, title) {
  slide.background = { color: C.bg };
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: W, h: 1.1,
    fill: { color: C.brown },
  });
  slide.addText(title, {
    x: MX, y: 0.15, w: CONTENT_W, h: 0.8,
    fontSize: 30, fontFace: C.bodyFont, bold: true, color: C.white, margin: 0,
  });
  addSlideNumber(slide);
}

function addSectionDivider(title, subtitle) {
  const slide = pres.addSlide();
  slide.background = { color: C.darkBg };
  slide.addShape(pres.shapes.RECTANGLE, {
    x: W / 2 - 1.5, y: 2.8, w: 3, h: 0.06,
    fill: { color: C.orange },
  });
  slide.addText(title, {
    x: MX, y: 3.1, w: CONTENT_W, h: 1.2,
    fontSize: 38, fontFace: C.bodyFont, bold: true, color: C.white, align: "center",
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: MX + 1, y: 4.3, w: CONTENT_W - 2, h: 0.7,
      fontSize: 18, fontFace: C.bodyFont, color: C.lightText, align: "center", italic: true,
    });
  }
  addSlideNumber(slide, true);
}

function addScaledImage(slide, imgFile, maxX, maxY, maxW, maxH) {
  const imgPath = path.join(IMG, imgFile);
  if (!fs.existsSync(imgPath)) {
    slide.addText(`[Image: ${imgFile}]`, { x: maxX, y: maxY, w: maxW, h: maxH, fontSize: 14, color: C.textGray, align: "center", valign: "middle" });
    return;
  }
  slide.addImage({ path: imgPath, x: maxX, y: maxY, w: maxW, h: maxH, sizing: { type: "contain", w: maxW, h: maxH } });
}

function addCodeBlock(slide, code, x, y, w, h) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: C.lightGray }, line: { color: C.medGray, width: 1 } });
  slide.addText(code, { x: x + 0.15, y: y + 0.1, w: w - 0.3, h: h - 0.2, fontSize: 13, fontFace: C.codeFont, color: C.darkBrown, valign: "top", margin: 0 });
}

function addBullets(slide, items, x, y, w, h, opts = {}) {
  const textArr = items.map((item, i) => ({
    text: item,
    options: { bullet: true, breakLine: i < items.length - 1, fontSize: opts.fontSize || 18, color: opts.color || C.darkBrown, fontFace: C.bodyFont },
  }));
  slide.addText(textArr, { x, y, w, h, valign: "top" });
}

function addCalloutBox(slide, text, x, y, w, h, opts = {}) {
  const bgColor = opts.bgColor || C.resultHi;
  const borderColor = opts.borderColor || C.green;
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: bgColor }, line: { color: borderColor, width: 2 } });
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.08, h, fill: { color: borderColor } });
  slide.addText(text, { x: x + 0.25, y, w: w - 0.4, h, fontSize: opts.fontSize || 16, fontFace: C.bodyFont, color: C.darkBrown, valign: "middle" });
}

function addStatCallout(slide, number, label, x, y, w, color) {
  slide.addText(number, { x, y, w, h: 0.7, fontSize: 44, fontFace: C.bodyFont, bold: true, color: color || C.positive, align: "center", margin: 0 });
  slide.addText(label, { x, y: y + 0.65, w, h: 0.4, fontSize: 13, fontFace: C.bodyFont, color: C.darkBrown, align: "center", margin: 0 });
}

function addCard(slide, x, y, w, h, accentColor) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: C.white }, shadow: cardShadow() });
  if (accentColor) {
    slide.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h, fill: { color: accentColor } });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// A. OPENING (Slides 1–5, ~7 min)
// ═══════════════════════════════════════════════════════════════════════════════

function buildOpening() {
  // ── Slide 1: Title ────────────────────────────────────────────────────────
  {
    const slide = pres.addSlide();
    slide.background = { color: C.darkBg };

    const logoPath = path.join(IMG, "logo.png");
    if (fs.existsSync(logoPath)) {
      slide.addImage({ path: logoPath, x: W / 2 - 0.6, y: 0.6, w: 1.2, h: 1.2 });
    }

    slide.addText("CaveAgent", {
      x: MX, y: 2.0, w: CONTENT_W, h: 0.9,
      fontSize: 48, fontFace: C.bodyFont, bold: true, color: C.white, align: "center", margin: 0,
    });
    slide.addText("Transforming LLMs into Stateful Runtime Operators", {
      x: MX + 1, y: 2.9, w: CONTENT_W - 2, h: 0.7,
      fontSize: 22, fontFace: C.bodyFont, color: C.lightText, align: "center", italic: true,
    });

    slide.addText("Maohao Ran*, Zhenglin Wan*, Cooper Lin, Yanting Zhang, Hongyu Xin, et al.", {
      x: MX + 1, y: 4.0, w: CONTENT_W - 2, h: 0.45,
      fontSize: 15, fontFace: C.bodyFont, color: C.white, align: "center",
    });
    slide.addText("HKUST \u00B7 HKBU \u00B7 NUS \u00B7 HKU \u00B7 CMU \u00B7 NTU \u00B7 Imperial \u00B7 Princeton \u00B7 UNC \u00B7 Harvard", {
      x: MX + 0.5, y: 4.45, w: CONTENT_W - 1, h: 0.4,
      fontSize: 12, fontFace: C.bodyFont, color: C.lightText, align: "center",
    });
    slide.addText("Hong Kong Generative AI Research and Development Center (HKGAI)", {
      x: MX + 1, y: 4.85, w: CONTENT_W - 2, h: 0.35,
      fontSize: 12, fontFace: C.bodyFont, color: C.lightText, align: "center", italic: true,
    });

    slide.addShape(pres.shapes.RECTANGLE, { x: W / 2 - 2, y: 5.35, w: 4, h: 0.04, fill: { color: C.orange } });
    slide.addText([
      { text: "arXiv: 2601.01569", options: { fontSize: 13, color: C.lightText, fontFace: C.bodyFont, breakLine: true } },
      { text: "GitHub: github.com/caveagent/cave-agent  \u00B7  PyPI: cave-agent v0.6.5", options: { fontSize: 13, color: C.lightText, fontFace: C.bodyFont } },
    ], { x: MX + 1.5, y: 5.6, w: CONTENT_W - 3, h: 0.7, align: "center" });

    addSlideNumber(slide, true);
  }

  // ── Slide 2: \u81EA\u6211\u4ECB\u7ECD + HKGAI ─────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u5173\u4E8E\u6211\u4EEC");

    // ── Left column: personal intro ──
    addCard(slide, MX, CONTENT_Y + 0.1, 6, 4.8, C.blue);

    slide.addText("\u4E07\u653F\u9716 Zhenglin (Carlos) Wan", {
      x: MX + 0.25, y: CONTENT_Y + 0.2, w: 5.5, h: 0.45,
      fontSize: 19, fontFace: C.bodyFont, bold: true, color: C.blue, margin: 0,
    });
    slide.addText("Ph.D. Student, National University of Singapore (NUS)", {
      x: MX + 0.25, y: CONTENT_Y + 0.65, w: 5.5, h: 0.3,
      fontSize: 13, fontFace: C.bodyFont, color: C.textGray, margin: 0,
    });
    slide.addText("HPC-AI Lab, Advisor: Prof. Yang You", {
      x: MX + 0.25, y: CONTENT_Y + 0.92, w: 5.5, h: 0.3,
      fontSize: 13, fontFace: C.bodyFont, color: C.textGray, margin: 0,
    });

    // Research interests
    slide.addText("\u7814\u7A76\u65B9\u5411", {
      x: MX + 0.25, y: CONTENT_Y + 1.35, w: 5.5, h: 0.3,
      fontSize: 14, fontFace: C.bodyFont, bold: true, color: C.darkBrown, margin: 0,
    });
    addBullets(slide, [
      "LLM Agents with RL as core methodology",
      "RL post-training & world models in LLM Agents",
      "Self-evolving agents (Learning to Evolve)",
      "Agent systems: tool/skill/runtime/context management",
    ], MX + 0.3, CONTENT_Y + 1.65, 5.4, 1.6, { fontSize: 12 });

    // Selected pubs
    slide.addText("\u4EE3\u8868\u6027\u5DE5\u4F5C", {
      x: MX + 0.25, y: CONTENT_Y + 3.2, w: 5.5, h: 0.3,
      fontSize: 14, fontFace: C.bodyFont, bold: true, color: C.darkBrown, margin: 0,
    });
    addBullets(slide, [
      "CaveAgent \u2014 \u672C\u6B21\u62A5\u544A\u7684\u5DE5\u4F5C\uFF0CHKGAI \u6838\u5FC3\u6280\u672F",
      "EBC: Diversifying Policy Behaviors (ICML 2025)",
      "POI Recommendation via Adversarial IL (AAAI 2025, oral)",
    ], MX + 0.3, CONTENT_Y + 3.5, 5.4, 1.1, { fontSize: 12 });

    // Link
    slide.addText("vanzll.github.io", {
      x: MX + 0.25, y: CONTENT_Y + 4.55, w: 5.5, h: 0.2,
      fontSize: 11, fontFace: C.bodyFont, color: C.blue, italic: true, margin: 0,
    });

    // ── Right column: HKGAI intro ──
    addCard(slide, 6.8, CONTENT_Y + 0.1, 5.9, 4.8, C.orange);

    slide.addText("HKGAI", {
      x: 7.05, y: CONTENT_Y + 0.2, w: 5.4, h: 0.45,
      fontSize: 19, fontFace: C.bodyFont, bold: true, color: C.orange, margin: 0,
    });
    slide.addText("Hong Kong Generative AI\nResearch & Development Center", {
      x: 7.05, y: CONTENT_Y + 0.65, w: 5.4, h: 0.5,
      fontSize: 13, fontFace: C.bodyFont, color: C.textGray, margin: 0,
    });

    slide.addText("\u673A\u6784\u7B80\u4ECB", {
      x: 7.05, y: CONTENT_Y + 1.3, w: 5.4, h: 0.3,
      fontSize: 14, fontFace: C.bodyFont, bold: true, color: C.darkBrown, margin: 0,
    });
    addBullets(slide, [
      "InnoHK \u652F\u6301\uFF0C2023\u5E74\u6210\u7ACB",
      "\u9999\u6E2F\u6700\u5927\u7684\u5408\u4F5C\u79D1\u7814\u9879\u76EE",
      "\u7531 HKUST \u5E38\u52A1\u526F\u6821\u957F Prof. Yike Guo \u9886\u5BFC",
      "\u8054\u5408 6 \u6240 QS \u767E\u5F3A\u9999\u6E2F\u9AD8\u6821 + NUS",
    ], 7.1, CONTENT_Y + 1.6, 5.2, 1.5, { fontSize: 12 });

    slide.addText("\u7814\u7A76\u65B9\u5411", {
      x: 7.05, y: CONTENT_Y + 2.95, w: 5.4, h: 0.3,
      fontSize: 14, fontFace: C.bodyFont, bold: true, color: C.darkBrown, margin: 0,
    });
    addBullets(slide, [
      "\u591A\u6A21\u6001\u3001\u591A\u8BED\u8A00\u57FA\u7840\u6A21\u578B",
      "\u5782\u76F4\u9886\u57DF\u57FA\u7840\u6A21\u578B\uFF08\u6CD5\u5F8B\u3001\u533B\u7597\u3001\u521B\u610F\uFF09",
      "HKGAI V1: \u9999\u6E2F\u9996\u4E2A\u672C\u5730 AI \u6A21\u578B\uFF08\u7CA4\u8BED/\u666E\u901A\u8BDD/\u82F1\u8BED\uFF09",
      "CaveAgent: \u6838\u5FC3\u6280\u672F\u4EA7\u54C1 HK E-Link",
    ], 7.1, CONTENT_Y + 3.25, 5.2, 1.5, { fontSize: 12 });

    slide.addText("www.hkgai.info", {
      x: 7.05, y: CONTENT_Y + 4.55, w: 5.4, h: 0.2,
      fontSize: 11, fontFace: C.bodyFont, color: C.orange, italic: true, margin: 0,
    });
  }

  // ── Slide 3: \u80CC\u666F\u4E0E\u52A8\u673A + JSON FC \u5C40\u9650 ────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u80CC\u666F\u4E0E\u52A8\u673A\uFF1AJSON Function Calling \u7684\u5C40\u9650");

    // Left: motivation + code
    addBullets(slide, [
      "LLM Agent \u5DF2\u65E0\u5904\u4E0D\u5728\uFF0CJSON function calling \u662F\u4E3B\u6D41\u8303\u5F0F",
      "\u4F46\u771F\u5B9E\u4E16\u754C\u4EFB\u52A1\u9700\u8981\u6709\u72B6\u6001\u7684\u6301\u4E45\u8BA1\u7B97",
    ], MX, CONTENT_Y + 0.1, 5.8, 1.2, { fontSize: 16 });

    const codeExample = `// \u5178\u578B JSON function call
{
  "name": "get_weather",
  "arguments": {"location": "SF"}
}
\u2192 Result returned as text string
\u2192 No persistent state between calls`;
    addCodeBlock(slide, codeExample, MX, CONTENT_Y + 1.4, 5.8, 2.2);

    // Right: 3 limitation cards
    const lims = [
      { title: "1. \u5E8F\u5217\u5316\u5F00\u9500", desc: "\u590D\u6742\u5BF9\u8C61\uFF08DataFrame\u3001\u6A21\u578B\uFF09\u5FC5\u987B\u8F6C\u4E3A\u6587\u672C", color: C.blue },
      { title: "2. \u65E0\u6301\u4E45\u72B6\u6001", desc: "\u6BCF\u6B21\u8C03\u7528\u90FD\u662F\u65E0\u72B6\u6001\u7684\uFF0C\u53D8\u91CF\u65E0\u6CD5\u8DE8\u6B65\u9A7E\u5B58\u6D3B", color: C.orange },
      { title: "3. \u53EF\u7EC4\u5408\u6027\u5DEE", desc: "\u65E0\u6CD5\u8DE8\u6B65\u9A7E\u5BF9\u5185\u5B58\u5BF9\u8C61\u8FDB\u884C\u94FE\u5F0F\u64CD\u4F5C", color: C.green },
    ];
    lims.forEach((lim, i) => {
      const cy = CONTENT_Y + 0.1 + i * 1.25;
      addCard(slide, 6.8, cy, 5.9, 1.1, lim.color);
      slide.addText(lim.title, { x: 7.05, y: cy + 0.08, w: 5.4, h: 0.35, fontSize: 16, fontFace: C.bodyFont, bold: true, color: C.darkBrown, margin: 0 });
      slide.addText(lim.desc, { x: 7.05, y: cy + 0.45, w: 5.4, h: 0.45, fontSize: 13, fontFace: C.bodyFont, color: C.textGray, margin: 0 });
    });

    addCalloutBox(slide, "\u7ED3\u679C\uFF1A\u4FE1\u606F\u4E22\u5931 + \u5197\u4F59\u8BA1\u7B97 + context window \u818A\u80C0", MX, CONTENT_Y + 4.0, CONTENT_W, 0.6, { borderColor: "CC3333", bgColor: "FFF0F0", fontSize: 15 });
  }

  // ── Slide 3: \u6587\u672C\u5316\u74F6\u9888 ─────────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u6587\u672C\u5316\u74F6\u9888 (Textualization Bottleneck)");

    // Two-column comparison
    addCard(slide, MX, CONTENT_Y + 0.1, 5.8, 3.5, "CC3333");
    slide.addText("\u5F53\u524D\uFF1AText-Bound Runtimes", { x: MX + 0.25, y: CONTENT_Y + 0.2, w: 5.3, h: 0.45, fontSize: 18, fontFace: C.bodyFont, bold: true, color: "CC3333", margin: 0 });
    addBullets(slide, [
      "\u6240\u6709\u5DE5\u5177\u7ED3\u679C\u5E8F\u5217\u5316\u4E3A\u6587\u672C\u5B57\u7B26\u4E32",
      "DataFrame \u2192 \u622A\u65AD\u6587\u672C\u8868\u683C",
      "ML \u6A21\u578B \u2192 \u53C2\u6570 dump",
      "DB \u8FDE\u63A5 \u2192 \u6BCF\u6B21\u91CD\u5EFA",
    ], MX + 0.3, CONTENT_Y + 0.75, 5.3, 2.5, { fontSize: 15 });

    addCard(slide, 6.8, CONTENT_Y + 0.1, 5.8, 3.5, C.green);
    slide.addText("CaveAgent: Runtime-Native", { x: 7.05, y: CONTENT_Y + 0.2, w: 5.3, h: 0.45, fontSize: 18, fontFace: C.bodyFont, bold: true, color: C.green, margin: 0 });
    addBullets(slide, [
      "\u5BF9\u8C61\u76F4\u63A5\u6D3B\u5728\u6301\u4E45 Python runtime \u4E2D",
      "DataFrame \u76F4\u63A5\u64CD\u4F5C\uFF0C\u65E0\u9700\u8F6C\u6362",
      "\u6A21\u578B\u52A0\u8F7D\u4E00\u6B21\uFF0C\u8DE8 turn \u4F7F\u7528",
      "\u53EA\u6709\u6458\u8981\u8FDB\u5165 context window",
    ], 7.1, CONTENT_Y + 0.75, 5.3, 2.5, { fontSize: 15 });

    addCalloutBox(slide, "\u6301\u4E45\u8FD0\u884C\u65F6\u6D88\u9664\u4E86\u6587\u672C\u5316\u74F6\u9888 \u2014 \u5BF9\u8C61\u59CB\u7EC8\u662F\u5BF9\u8C61\uFF0C\u800C\u975E\u5B57\u7B26\u4E32", MX + 0.5, CONTENT_Y + 3.9, CONTENT_W - 1, 0.7, { borderColor: C.orange, bgColor: "FFF8EE", fontSize: 15 });
  }

  // ── Slide 4: \u8303\u5F0F\u6F14\u8FDB ─────────────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "LLM-Tool \u4EA4\u4E92\u8303\u5F0F\u7684\u6F14\u8FDB");

    addScaledImage(slide, "evolve.png", MX + 0.5, CONTENT_Y + 0.1, CONTENT_W - 1, 4.5);

    slide.addText("Gen 0 Text-Only \u2192 Gen 1 JSON FC \u2192 Gen 2 Code-as-Action \u2192 Gen 3 Stateful Runtime (CaveAgent)", {
      x: MX + 0.5, y: H - 1.2, w: CONTENT_W - 1, h: 0.5,
      fontSize: 15, fontFace: C.bodyFont, bold: true, color: C.darkBrown, align: "center",
    });
  }

  // ── Slide 5: \u613F\u666F\u4E0E\u8D21\u732E ────────────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u6211\u4EEC\u7684\u613F\u666F\u4E0E\u8D21\u732E");

    addCalloutBox(slide,
      '\u201C\u80FD\u5426\u5C06 LLM \u4ECE\u6587\u672C\u751F\u6210\u5668\u8F6C\u53D8\u4E3A\u6709\u72B6\u6001\u7684\u8FD0\u884C\u65F6\u64CD\u4F5C\u5668\uFF0C\u7EF4\u62A4\u6301\u4E45\u7684\u8BA1\u7B97\u73AF\u5883\uFF1F\u201D',
      MX + 0.5, CONTENT_Y + 0.1, CONTENT_W - 1, 0.85,
      { borderColor: C.orange, bgColor: "FFF8EE", fontSize: 17 }
    );

    const contribs = [
      { num: "1", title: "\u53CC\u6D41\u67B6\u6784", desc: "Semantic Stream \u7528\u4E8E\u63A8\u7406 + Runtime Stream \u7528\u4E8E\u6301\u4E45\u6267\u884C\uFF0C\u8FD0\u884C\u65F6\u6280\u80FD\u7BA1\u7406", color: C.blue },
      { num: "2", title: "\u53EF\u7F16\u7A0B\u9A8C\u8BC1", desc: "Runtime state \u53EF\u786E\u5B9A\u6027\u8BBF\u95EE\uFF0C\u652F\u6301\u81EA\u52A8\u5316\u8BC4\u6D4B\u4E0E RLVR \u5956\u52B1\u4FE1\u53F7", color: C.green },
      { num: "3", title: "\u5168\u9762\u9A8C\u8BC1", desc: "6\u4E2A SOTA LLM\u3001Tau\u00B2-bench\u3001BFCL\u3001\u81EA\u5B9A\u4E49\u72B6\u6001\u7BA1\u7406 benchmark", color: C.orange },
    ];

    contribs.forEach((c, i) => {
      const cx = MX + 0.2 + i * 4.15;
      const cy = CONTENT_Y + 1.3;
      addCard(slide, cx, cy, 3.85, 3.2, c.color);

      slide.addShape(pres.shapes.OVAL, { x: cx + 1.55, y: cy + 0.2, w: 0.6, h: 0.6, fill: { color: c.color } });
      slide.addText(c.num, { x: cx + 1.55, y: cy + 0.2, w: 0.6, h: 0.6, fontSize: 22, fontFace: C.bodyFont, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });

      slide.addText(c.title, { x: cx + 0.25, y: cy + 1.0, w: 3.4, h: 0.45, fontSize: 18, fontFace: C.bodyFont, bold: true, color: C.darkBrown, align: "center", margin: 0 });
      slide.addText(c.desc, { x: cx + 0.25, y: cy + 1.5, w: 3.4, h: 1.4, fontSize: 14, fontFace: C.bodyFont, color: C.textGray, align: "center", margin: 0 });
    });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// B. ARCHITECTURE (Slides 6–10, ~10 min)
// ═══════════════════════════════════════════════════════════════════════════════

function buildArchitecture() {
  addSectionDivider("\u6838\u5FC3\u67B6\u6784", "CaveAgent Architecture");

  // ── Slide 7: \u53CC\u6D41\u67B6\u6784\u603B\u89C8 ────────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u53CC\u6D41\u67B6\u6784\u603B\u89C8 (Dual-Stream Architecture)");
    addScaledImage(slide, "framework.png", MX + 0.3, CONTENT_Y + 0.1, CONTENT_W - 0.6, 4.5);
    slide.addText("Semantic Stream\uFF08LLM\u63A8\u7406\uFF09+ Runtime Stream\uFF08\u6301\u4E45 Python \u73AF\u5883\uFF09", {
      x: MX, y: H - 1.1, w: CONTENT_W, h: 0.4,
      fontSize: 15, fontFace: C.bodyFont, italic: true, color: C.textGray, align: "center",
    });
  }

  // ── Slide 8: \u5F62\u5F0F\u5316\u6A21\u578B ────────────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u5F62\u5F0F\u5316\u6A21\u578B\u4E0E\u6838\u5FC3\u6D1E\u5BDF");

    // Left: equations
    addCard(slide, MX, CONTENT_Y + 0.1, 6, 1.6, C.blue);
    slide.addText("Semantic Stream", { x: MX + 0.25, y: CONTENT_Y + 0.15, w: 5.5, h: 0.3, fontSize: 15, fontFace: C.bodyFont, bold: true, color: C.blue, margin: 0 });
    slide.addText("h\u209C  =  LLM( x\u209C , h\u209C\u208B\u2081 )", { x: MX + 0.5, y: CONTENT_Y + 0.5, w: 5.0, h: 0.45, fontSize: 24, fontFace: C.bodyFont, bold: true, color: C.darkBrown, margin: 0 });
    slide.addText("Context history \u2014 \u4F1A\u8BDD/\u63A8\u7406\u8F68\u8FF9", { x: MX + 0.5, y: CONTENT_Y + 1.0, w: 5.0, h: 0.35, fontSize: 13, fontFace: C.bodyFont, italic: true, color: C.textGray, margin: 0 });

    addCard(slide, MX, CONTENT_Y + 2.0, 6, 1.6, C.green);
    slide.addText("Runtime Stream", { x: MX + 0.25, y: CONTENT_Y + 2.05, w: 5.5, h: 0.3, fontSize: 15, fontFace: C.bodyFont, bold: true, color: C.green, margin: 0 });
    slide.addText("S\u209C  =  Exec( c\u209C , S\u209C\u208B\u2081 )", { x: MX + 0.5, y: CONTENT_Y + 2.4, w: 5.0, h: 0.45, fontSize: 24, fontFace: C.bodyFont, bold: true, color: C.darkBrown, margin: 0 });
    slide.addText("\u6301\u4E45\u73AF\u5883 \u2014 \u53D8\u91CF\u3001\u5BF9\u8C61\u3001\u8FDE\u63A5\u8DE8 turn \u5B58\u6D3B", { x: MX + 0.5, y: CONTENT_Y + 2.9, w: 5.0, h: 0.35, fontSize: 13, fontFace: C.bodyFont, italic: true, color: C.textGray, margin: 0 });

    // Right: key insight
    addCard(slide, 7, CONTENT_Y + 0.1, 5.7, 3.5, C.orange);
    slide.addText("\u6838\u5FC3\u6D1E\u5BDF\uFF1A\u89E3\u8026", { x: 7.25, y: CONTENT_Y + 0.2, w: 5.2, h: 0.4, fontSize: 18, fontFace: C.bodyFont, bold: true, color: C.orange, margin: 0 });
    addBullets(slide, [
      "h\u209C = \u8BED\u4E49\u5386\u53F2\uFF08LLM \u770B\u5230\u7684\uFF09",
      "S\u209C = \u8FD0\u884C\u65F6\u72B6\u6001\uFF08\u6301\u4E45\u5B58\u50A8\u7684\uFF09",
      "N\u209C = \u5168\u5C40\u547D\u540D\u7A7A\u95F4",
      "\u03C4(\u00B7) = \u89C2\u5BDF\u5851\u5F62\u51FD\u6570",
      "",
      "Runtime \u624D\u662F\u4E3B\u8981\u5DE5\u4F5C\u7A7A\u95F4\uFF0C",
      "\u800C\u4E0D\u662F context window\uFF01",
    ], 7.25, CONTENT_Y + 0.75, 5.2, 2.6, { fontSize: 14 });

    // Bottom: loop
    addCalloutBox(slide, "CaveAgent.run(): \u6784\u5EFA\u63D0\u793A \u2192 \u53D1\u9001LLM \u2192 \u63D0\u53D6\u4EE3\u7801 \u2192 \u6267\u884C \u2192 \u53CD\u9988 \u2192 \u5FAA\u73AF", MX, CONTENT_Y + 4.0, CONTENT_W, 0.6, { borderColor: C.brown, bgColor: "FFF8EE", fontSize: 14 });
  }

  // ── Slide 9: Runtime \u4E0E\u6CE8\u5165 API ─────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u8FD0\u884C\u65F6\u6D41\u4E0E\u6CE8\u5165 API");

    // Left: code
    const code = `from cave_agent import CaveAgent, Variable, Function

agent = CaveAgent(model=model)

# \u6CE8\u5165\u771F\u5B9E Python \u5BF9\u8C61
agent.runtime.inject(Variable(
    name="sales_data",
    value=df,  # \u771F\u5B9E\u7684 pandas DataFrame!
    description="Q1 2024 sales data"
))

# Step 1: df \u6301\u4E45\u5B58\u5728
# Step 2: \u76F4\u63A5\u805A\u5408\uFF0C\u65E0\u9700\u91CD\u65B0\u52A0\u8F7D
# Step 3: \u5728\u5185\u5B58\u4E2D\u6784\u5EFA\u6A21\u578B`;
    addCodeBlock(slide, code, MX, CONTENT_Y + 0.1, 7.2, 3.8);

    // Right: explanation
    addCard(slide, 7.6, CONTENT_Y + 0.1, 5.1, 3.8, C.green);
    slide.addText("\u8FD0\u884C\u65F6\u539F\u8BED", { x: 7.85, y: CONTENT_Y + 0.2, w: 4.6, h: 0.4, fontSize: 17, fontFace: C.bodyFont, bold: true, color: C.green, margin: 0 });
    addBullets(slide, [
      "Variable \u2014 \u6CE8\u5165\u4EFB\u610F Python \u5BF9\u8C61",
      "Function \u2014 \u6CE8\u5165\u53EF\u8C03\u7528\u51FD\u6570",
      "Type \u2014 \u6CE8\u5165\u81EA\u5B9A\u4E49\u7C7B\u578B",
      "",
      "\u57FA\u4E8E IPython \u7684\u6301\u4E45\u5185\u6838",
      "\u5BF9\u8C61\u662F\u771F\u5B9E\u7684\uFF0C\u4E0D\u662F\u5E8F\u5217\u5316\u6587\u672C",
      "LLM \u770B\u5230\u5143\u6570\u636E\u6458\u8981",
      "\u4EE3\u7801\u64CD\u4F5C\u771F\u5B9E\u5BF9\u8C61",
    ], 7.85, CONTENT_Y + 0.75, 4.6, 2.8, { fontSize: 14 });

    // Bottom
    addCalloutBox(slide, "\u53D8\u91CF\u3001\u5BF9\u8C61\u3001\u8FDE\u63A5\u8DE8\u6240\u6709 agent step \u6301\u4E45\u5B58\u5728 \u2014 \u8FD0\u884C\u65F6\u662F\u4E3B\u8981\u5DE5\u4F5C\u7A7A\u95F4", MX, CONTENT_Y + 4.2, CONTENT_W, 0.6, { borderColor: C.green, bgColor: C.resultHi, fontSize: 14 });
  }

  // ── Slide 10: \u4E0A\u4E0B\u6587\u540C\u6B65\u4E0E\u5B89\u5168 ──────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u4E0A\u4E0B\u6587\u540C\u6B65\u4E0E\u5B89\u5168\u6A21\u578B");

    // Left: context sync
    addCard(slide, MX, CONTENT_Y + 0.1, 6, 4.3, C.blue);
    slide.addText("\u52A8\u6001\u4E0A\u4E0B\u6587\u540C\u6B65", { x: MX + 0.25, y: CONTENT_Y + 0.2, w: 5.5, h: 0.4, fontSize: 17, fontFace: C.bodyFont, bold: true, color: C.blue, margin: 0 });
    addBullets(slide, [
      "Runtime State Summary: \u7CFB\u7EDF\u63D0\u793A\u81EA\u52A8\u5305\u542B\u5F53\u524D\u53D8\u91CF/\u51FD\u6570",
      "Observation Shaping (\u03C4): \u8F93\u51FA\u6709 L_max \u9650\u5236\uFF0C\u5927\u7ED3\u679C\u622A\u65AD+\u6458\u8981",
      "Progressive Disclosure: skill \u5143\u6570\u636E ~100 tokens\uFF0C\u6309\u9700\u52A0\u8F7D",
      "",
      "\u4FDD\u6301 context \u7D27\u51D1\uFF0C\u540C\u65F6 runtime \u65E0\u9650\u6269\u5C55",
    ], MX + 0.3, CONTENT_Y + 0.75, 5.4, 3.2, { fontSize: 14 });

    // Right: security
    addCard(slide, 6.8, CONTENT_Y + 0.1, 5.9, 4.3, "CC3333");
    slide.addText("AST-Based \u5B89\u5168\u6A21\u578B", { x: 7.05, y: CONTENT_Y + 0.2, w: 5.4, h: 0.4, fontSize: 17, fontFace: C.bodyFont, bold: true, color: "CC3333", margin: 0 });
    addBullets(slide, [
      "ImportRule \u2014 \u767D\u540D\u5355/\u9ED1\u540D\u5355\u6A21\u5757\u5BFC\u5165",
      "FunctionRule \u2014 \u9650\u5236\u5371\u9669\u51FD\u6570\u8C03\u7528",
      "AttributeRule \u2014 \u63A7\u5236\u5C5E\u6027\u8BBF\u95EE",
      "RegexRule \u2014 \u6A21\u5F0F\u626B\u63CF",
      "",
      "\u81EA\u7EA0\u6B63\u6D41\u7A0B\uFF1A\u751F\u6210 \u2192 AST\u68C0\u67E5 \u2192 \u8FDD\u89C4\u53CD\u9988 \u2192 \u91CD\u65B0\u751F\u6210",
      "Pre-execution: \u5371\u9669\u4EE3\u7801\u6C38\u4E0D\u5230\u8FBE runtime",
    ], 7.1, CONTENT_Y + 0.75, 5.4, 3.2, { fontSize: 14 });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// C. SKILLS & CAPABILITIES (Slides 11–15, ~8 min)
// ═══════════════════════════════════════════════════════════════════════════════

function buildSkillsAndCapabilities() {
  addSectionDivider("\u6280\u80FD\u4E0E\u80FD\u529B", "Skills & Key Capabilities");

  // ── Slide 12: Skills \u67B6\u6784\u4E0E\u5BF9\u6BD4 ──────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "Runtime-Integrated Skills \u67B6\u6784");

    // Left: figure
    addScaledImage(slide, "skills.png", MX, CONTENT_Y + 0.1, 5.5, 3.2);

    // Right: key points + comparison
    addBullets(slide, [
      "\u517C\u5BB9 agentskills.io \u5F00\u653E\u6807\u51C6",
      "\u6269\u5C55\uFF1Ainjection.py \u4E2D __exports__ \u5BFC\u51FA Function/Variable/Type",
      "\u6FC0\u6D3B\u65F6\u76F4\u63A5\u6CE8\u5165 runtime\uFF0C\u4E0D\u53EA\u662F\u6587\u672C\u6307\u4EE4",
      "\u6E10\u8FDB\u62AB\u9732\uFF1A\u542F\u52A8 ~100 tokens\uFF0C\u6309\u9700\u52A0\u8F7D\u5B8C\u6574\u6307\u4EE4",
    ], 6, CONTENT_Y + 0.1, 6.7, 2.5, { fontSize: 15 });

    // Compact comparison table
    const hOpts = { fill: { color: C.brown }, color: C.white, bold: true, fontSize: 12, fontFace: C.bodyFont, align: "center", valign: "middle" };
    const cOpts = { fontSize: 11, fontFace: C.bodyFont, color: C.darkBrown, valign: "middle" };
    const hiOpts = { ...cOpts, fill: { color: C.resultHi } };

    const rows = [
      [{ text: "\u7279\u6027", options: hOpts }, { text: "Standard Skills", options: hOpts }, { text: "CaveAgent Skills", options: hOpts }],
      [{ text: "\u51FD\u6570\u8BBF\u95EE", options: cOpts }, { text: "\u6587\u672C\u63CF\u8FF0\uFF0CLLM\u81EA\u884C\u5B9E\u73B0", options: cOpts }, { text: "\u53EF\u8C03\u7528\u5BF9\u8C61\u76F4\u63A5\u6CE8\u5165", options: hiOpts }],
      [{ text: "\u72B6\u6001\u7BA1\u7406", options: cOpts }, { text: "\u65E0 \u2014 \u65E0\u72B6\u6001", options: cOpts }, { text: "\u53D8\u91CF/\u7C7B\u578B\u6301\u4E45\u5728 runtime", options: hiOpts }],
      [{ text: "\u53EF\u7EC4\u5408\u6027", options: cOpts }, { text: "\u6587\u672C\u7EA7\u94FE\u63A5", options: cOpts }, { text: "Python \u4EE3\u7801\u7EC4\u5408\u5BF9\u8C61", options: hiOpts }],
      [{ text: "\u6FC0\u6D3B\u6210\u672C", options: cOpts }, { text: "\u5B8C\u6574 skill \u6587\u672C\u52A0\u8F7D", options: cOpts }, { text: "~100 tokens + \u6309\u9700\u52A0\u8F7D", options: hiOpts }],
    ];

    slide.addTable(rows, {
      x: MX, y: CONTENT_Y + 3.5, w: CONTENT_W,
      colW: [2.2, 4.5, 5.4],
      border: { pt: 0.5, color: C.medGray },
      rowH: [0.4, 0.38, 0.38, 0.38, 0.38],
    });
  }

  // ── Slide 13: \u4E0B\u6E38\u5E94\u7528\u4E0E\u591A Agent ─────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u4E0B\u6E38\u5E94\u7528\u4E0E\u591A Agent \u534F\u4F5C");

    // Left: downstream figure
    addScaledImage(slide, "downstream_applications.png", MX, CONTENT_Y + 0.1, 6, 3.0);

    // Right: multi-agent
    slide.addText("\u591A Agent \u534F\u4F5C\uFF1A\u5171\u4EAB Runtime", { x: 6.5, y: CONTENT_Y + 0.1, w: 6.2, h: 0.4, fontSize: 17, fontFace: C.bodyFont, bold: true, color: C.darkBrown });
    addBullets(slide, [
      "Agent \u4F5C\u4E3A runtime \u4E2D\u7684\u5BF9\u8C61",
      "\u76F4\u63A5\u4F20\u9012\u5BF9\u8C61\uFF0C\u65E0\u5E8F\u5217\u5316\u5F00\u9500",
      "Town simulation: \u591A Agent \u4EA4\u4E92\u6F14\u793A",
    ], 6.6, CONTENT_Y + 0.6, 6, 1.5, { fontSize: 14 });

    // Town simulation figure
    addScaledImage(slide, "town_simulation.png", 6.5, CONTENT_Y + 2.1, 6.2, 2.5);

    // Bottom: RLVR callout
    addCalloutBox(slide, "RLVR \u57FA\u7840\uFF1ARuntime state \u53EF\u786E\u5B9A\u6027\u8BBF\u95EE \u2192 \u81EA\u52A8\u5316\u8BC4\u6D4B + \u7EC6\u7C92\u5EA6\u5956\u52B1\u4FE1\u53F7\uFF0C\u65E0\u9700\u4EBA\u5DE5\u6807\u6CE8", MX, CONTENT_Y + 4.8, CONTENT_W, 0.55, { borderColor: C.green, bgColor: C.resultHi, fontSize: 14 });
  }

  // ── Slide 14: \u667A\u80FD\u5BB6\u5C45\u6F14\u793A ─────────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u5B9E\u9645\u5E94\u7528\uFF1A\u667A\u80FD\u5BB6\u5C45\u63A7\u5236");
    addScaledImage(slide, "smarthome.png", MX + 0.3, CONTENT_Y + 0.1, CONTENT_W - 0.6, 4.5);
    slide.addText("Agent \u7EF4\u62A4\u8BBE\u5907\u72B6\u6001\u3001\u573A\u666F\u3001\u81EA\u52A8\u5316\u89C4\u5219\uFF0C\u8DE8\u591A\u8F6E\u4EA4\u4E92\u6301\u4E45\u4FDD\u5B58", {
      x: MX, y: H - 1.1, w: CONTENT_W, h: 0.4,
      fontSize: 14, fontFace: C.bodyFont, italic: true, color: C.textGray, align: "center",
    });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// D. EXPERIMENTS (Slides 15–20, ~10 min)
// ═══════════════════════════════════════════════════════════════════════════════

function buildExperiments() {
  addSectionDivider("\u5B9E\u9A8C\u9A8C\u8BC1", "Experiments & Results");

  // ── Slide 16: Setup ───────────────────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u5B9E\u9A8C\u8BBE\u7F6E");

    addCard(slide, MX, CONTENT_Y + 0.1, 5.8, 2.5, C.blue);
    slide.addText("Benchmarks", { x: MX + 0.25, y: CONTENT_Y + 0.2, w: 5.3, h: 0.35, fontSize: 17, fontFace: C.bodyFont, bold: true, color: C.blue, margin: 0 });
    addBullets(slide, [
      "Tau\u00B2-bench (Airline + Retail)",
      "BFCL (Berkeley Function Calling Leaderboard)",
      "\u81EA\u5B9A\u4E49\u72B6\u6001\u7BA1\u7406 Benchmark",
      "\u6570\u636E\u5BC6\u96C6\u4EFB\u52A1 (query, analysis, visualization)",
    ], MX + 0.3, CONTENT_Y + 0.65, 5.2, 1.8, { fontSize: 14 });

    addCard(slide, 6.8, CONTENT_Y + 0.1, 5.9, 2.5, C.green);
    slide.addText("6 \u4E2A SOTA LLM", { x: 7.05, y: CONTENT_Y + 0.2, w: 5.4, h: 0.35, fontSize: 17, fontFace: C.bodyFont, bold: true, color: C.green, margin: 0 });
    addBullets(slide, [
      "\u5F00\u6E90: DeepSeek-V3.2 (685B), Qwen3-Coder (30B), Kimi-K2 (1000B)",
      "\u95ED\u6E90: Claude Sonnet 4.5, GPT-5.1, Gemini 3 Pro",
      "\u6BCF\u4E2A\u8BBE\u7F6E 3 \u6B21\u8FD0\u884C\uFF0C\u4FDD\u8BC1\u7EDF\u8BA1\u53EF\u9760\u6027",
    ], 7.1, CONTENT_Y + 0.65, 5.4, 1.8, { fontSize: 14 });

    addCalloutBox(slide, "\u5BF9\u6BD4\u65B9\u5F0F\uFF1A\u540C\u4E00\u6A21\u578B\u3001\u540C\u4E00\u5DE5\u5177\u3001\u540C\u4E00\u4EFB\u52A1 \u2014 \u53EA\u6362\u4EA4\u4E92\u8303\u5F0F\uFF08JSON FC vs CaveAgent\uFF09", MX + 0.3, CONTENT_Y + 2.9, CONTENT_W - 0.6, 0.55, { borderColor: C.orange, bgColor: "FFF8EE", fontSize: 14 });

    // Stats preview
    addStatCallout(slide, "11/12", "Tau\u00B2-bench \u80DC\u51FA", MX + 0.5, CONTENT_Y + 3.8, 3.5, C.positive);
    addStatCallout(slide, "+40.9%", "BFCL \u6700\u5927\u63D0\u5347", MX + 4.5, CONTENT_Y + 3.8, 3.5, C.blue);
    addStatCallout(slide, "-28.4%", "Token \u51CF\u5C11", MX + 8.5, CONTENT_Y + 3.8, 3.5, C.positive);
  }

  // ── Slide 17: Tau\u00B2-bench + BFCL ──────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "Tau\u00B2-bench \u7ED3\u679C\uFF1A11/12 \u8BBE\u7F6E CaveAgent \u80DC\u51FA");

    const hOpts = { fill: { color: C.brown }, color: C.white, bold: true, fontSize: 11, fontFace: C.bodyFont, align: "center", valign: "middle" };
    const cOpts = { fontSize: 11, fontFace: C.bodyFont, color: C.darkBrown, align: "center", valign: "middle" };
    const hiCell = { ...cOpts, fill: { color: C.resultHi }, bold: true };
    const dCell = { ...cOpts, color: C.positive, bold: true };

    const rows = [
      [{ text: "Model", options: hOpts }, { text: "Domain", options: hOpts }, { text: "FC", options: hOpts }, { text: "CaveAgent", options: hOpts }, { text: "\u0394", options: hOpts }],
      [{ text: "DeepSeek-V3.2", options: cOpts }, { text: "Airline", options: cOpts }, { text: "55.3%", options: cOpts }, { text: "60.0%", options: hiCell }, { text: "+4.7%", options: dCell }],
      [{ text: "", options: cOpts }, { text: "Retail", options: cOpts }, { text: "77.2%", options: cOpts }, { text: "81.9%", options: hiCell }, { text: "+4.7%", options: dCell }],
      [{ text: "Qwen3-Coder", options: cOpts }, { text: "Airline", options: cOpts }, { text: "38.0%", options: cOpts }, { text: "40.7%", options: hiCell }, { text: "+2.7%", options: dCell }],
      [{ text: "", options: cOpts }, { text: "Retail", options: cOpts }, { text: "41.2%", options: cOpts }, { text: "54.7%", options: hiCell }, { text: "+13.5%", options: dCell }],
      [{ text: "Kimi-K2", options: cOpts }, { text: "Airline", options: cOpts }, { text: "54.0%", options: cOpts }, { text: "55.3%", options: hiCell }, { text: "+1.3%", options: dCell }],
      [{ text: "", options: cOpts }, { text: "Retail", options: cOpts }, { text: "60.8%", options: cOpts }, { text: "71.3%", options: hiCell }, { text: "+10.5%", options: dCell }],
      [{ text: "Claude 4.5", options: cOpts }, { text: "Airline", options: cOpts }, { text: "57.3%", options: cOpts }, { text: "56.7%", options: cOpts }, { text: "-0.6%", options: { ...cOpts, color: "CC3333" } }],
      [{ text: "", options: cOpts }, { text: "Retail", options: cOpts }, { text: "72.5%", options: cOpts }, { text: "76.6%", options: hiCell }, { text: "+4.1%", options: dCell }],
      [{ text: "GPT-5.1", options: cOpts }, { text: "Airline", options: cOpts }, { text: "52.7%", options: cOpts }, { text: "56.0%", options: hiCell }, { text: "+3.3%", options: dCell }],
      [{ text: "", options: cOpts }, { text: "Retail", options: cOpts }, { text: "65.8%", options: cOpts }, { text: "69.6%", options: hiCell }, { text: "+3.8%", options: dCell }],
      [{ text: "Gemini 3 Pro", options: cOpts }, { text: "Airline", options: cOpts }, { text: "61.3%", options: cOpts }, { text: "68.0%", options: hiCell }, { text: "+6.7%", options: dCell }],
      [{ text: "", options: cOpts }, { text: "Retail", options: cOpts }, { text: "70.8%", options: cOpts }, { text: "76.3%", options: hiCell }, { text: "+5.5%", options: dCell }],
    ];

    slide.addTable(rows, {
      x: MX + 0.3, y: CONTENT_Y + 0.05, w: CONTENT_W - 0.6,
      colW: [2.4, 1.3, 2.0, 2.5, 1.5],
      border: { pt: 0.5, color: C.medGray },
      rowH: [0.38, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32],
    });

    addCalloutBox(slide, "\u6700\u5927\u63D0\u5347: +13.5% (Qwen3-Coder Retail)  |  \u5E73\u5747 ~4.7%  |  \u552F\u4E00\u4E0B\u964D: Claude Airline -0.6%", MX + 0.5, H - 1.05, CONTENT_W - 1, 0.5, { borderColor: C.positive, bgColor: C.resultHi, fontSize: 13 });
  }

  // ── Slide 18: BFCL + Token Efficiency ──────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "BFCL \u7ED3\u679C\u4E0E Token \u6548\u7387");

    // Left: BFCL table (compact)
    const hOpts = { fill: { color: C.brown }, color: C.white, bold: true, fontSize: 11, fontFace: C.bodyFont, align: "center", valign: "middle" };
    const cOpts = { fontSize: 11, fontFace: C.bodyFont, color: C.darkBrown, align: "center", valign: "middle" };
    const hiCell = { ...cOpts, fill: { color: C.resultHi }, bold: true };
    const dCell = { ...cOpts, color: C.positive, bold: true };

    const bfclRows = [
      [{ text: "Model", options: hOpts }, { text: "FC", options: hOpts }, { text: "CaveAgent", options: hOpts }, { text: "\u0394", options: hOpts }],
      [{ text: "DeepSeek-V3.2", options: cOpts }, { text: "86.9%", options: cOpts }, { text: "94.0%", options: hiCell }, { text: "+7.1%", options: dCell }],
      [{ text: "DeepSeek (w/o prompt)", options: cOpts }, { text: "53.1%", options: cOpts }, { text: "94.0%", options: hiCell }, { text: "+40.9%", options: dCell }],
      [{ text: "Qwen3-Coder", options: cOpts }, { text: "89.8%", options: cOpts }, { text: "94.4%", options: hiCell }, { text: "+4.6%", options: dCell }],
      [{ text: "Kimi-K2", options: cOpts }, { text: "89.2%", options: cOpts }, { text: "94.7%", options: hiCell }, { text: "+5.5%", options: dCell }],
      [{ text: "Claude 4.5", options: cOpts }, { text: "94.4%", options: cOpts }, { text: "94.4%", options: hiCell }, { text: "0.0%", options: cOpts }],
      [{ text: "GPT-5.1", options: cOpts }, { text: "89.6%", options: cOpts }, { text: "88.9%", options: cOpts }, { text: "-0.7%", options: { ...cOpts, color: "CC3333" } }],
      [{ text: "Gemini 3 Pro", options: cOpts }, { text: "94.3%", options: cOpts }, { text: "94.3%", options: hiCell }, { text: "0.0%", options: cOpts }],
    ];

    slide.addTable(bfclRows, {
      x: MX, y: CONTENT_Y + 0.1, w: 6,
      colW: [2.2, 1.1, 1.5, 1.2],
      border: { pt: 0.5, color: C.medGray },
      rowH: [0.35, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32],
    });

    // Right: Token efficiency stats
    addStatCallout(slide, "-28.4%", "Total Token \u51CF\u5C11", 7, CONTENT_Y + 0.1, 2.8, C.positive);
    addStatCallout(slide, "-38.6%", "\u6B65\u9AA4\u51CF\u5C11", 9.8, CONTENT_Y + 0.1, 2.8, C.positive);

    // Token consumption figure
    addScaledImage(slide, "token_consumption.png", 6.8, CONTENT_Y + 1.5, 5.9, 2.4);

    slide.addText("DeepSeek V3.2: 504K vs 704K tokens | 145 vs 236 steps | 100% vs 94.6% success", {
      x: 6.8, y: CONTENT_Y + 3.9, w: 5.9, h: 0.35,
      fontSize: 11, fontFace: C.bodyFont, italic: true, color: C.textGray, align: "center",
    });

    // Bottom
    addCalloutBox(slide, "BFCL: DeepSeek \u65E0 prompt \u65F6 53.1% \u2192 94.0% (+40.9%) \u2014 CaveAgent \u5BF9 prompt \u683C\u5F0F\u7684\u9C81\u68D2\u6027\u66F4\u5F3A", MX, CONTENT_Y + 4.5, CONTENT_W, 0.55, { borderColor: C.blue, bgColor: "EBF0F5", fontSize: 13 });
  }

  // ── Slide 19: \u72B6\u6001\u7BA1\u7406 + \u6848\u4F8B ─────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u72B6\u6001\u7BA1\u7406 Benchmark \u4E0E\u6848\u4F8B\u7814\u7A76");

    // Left: radar + heatmap
    addScaledImage(slide, "type_proficiency_multi_radar.png", MX, CONTENT_Y + 0.1, 4.2, 2.8);
    slide.addText("Type Proficiency", { x: MX, y: CONTENT_Y + 2.95, w: 4.2, h: 0.3, fontSize: 11, fontFace: C.bodyFont, italic: true, color: C.textGray, align: "center" });

    addScaledImage(slide, "vars_count_heatmap.png", 4.6, CONTENT_Y + 0.1, 4.2, 2.8);
    slide.addText("Multi-Variable (5V\u201325V)", { x: 4.6, y: CONTENT_Y + 2.95, w: 4.2, h: 0.3, fontSize: 11, fontFace: C.bodyFont, italic: true, color: C.textGray, align: "center" });

    // Right: data-intensive comparison (compact)
    const hOpts2 = { fill: { color: C.brown }, color: C.white, bold: true, fontSize: 10, fontFace: C.bodyFont, align: "center", valign: "middle" };
    const cOpts2 = { fontSize: 10, fontFace: C.bodyFont, color: C.darkBrown, align: "center", valign: "middle" };
    const hiCell2 = { ...cOpts2, fill: { color: C.resultHi }, bold: true };

    const dataRows = [
      [{ text: "\u4EFB\u52A1", options: hOpts2 }, { text: "CaveAgent", options: hOpts2 }, { text: "CodeAct", options: hOpts2 }, { text: "JSON FC", options: hOpts2 }],
      [{ text: "Query", options: cOpts2 }, { text: "100%", options: hiCell2 }, { text: "80%", options: cOpts2 }, { text: "80%", options: cOpts2 }],
      [{ text: "Analysis", options: cOpts2 }, { text: "100%", options: hiCell2 }, { text: "100%", options: cOpts2 }, { text: "10%", options: { ...cOpts2, color: "CC3333" } }],
      [{ text: "Viz", options: cOpts2 }, { text: "90%", options: hiCell2 }, { text: "40%", options: cOpts2 }, { text: "30%", options: { ...cOpts2, color: "CC3333" } }],
      [{ text: "Viz tokens", options: cOpts2 }, { text: "405K", options: hiCell2 }, { text: "1M", options: cOpts2 }, { text: "662K", options: cOpts2 }],
    ];

    slide.addTable(dataRows, {
      x: 9.1, y: CONTENT_Y + 0.1, w: 3.6,
      colW: [0.9, 0.9, 0.9, 0.9],
      border: { pt: 0.5, color: C.medGray },
      rowH: [0.35, 0.32, 0.32, 0.32, 0.32],
    });
    slide.addText("\u6570\u636E\u5BC6\u96C6\u4EFB\u52A1\u5BF9\u6BD4", { x: 9.1, y: CONTENT_Y + 1.8, w: 3.6, h: 0.3, fontSize: 11, fontFace: C.bodyFont, italic: true, color: C.textGray, align: "center" });

    // Bottom: domain apps
    addScaledImage(slide, "geospatial.png", MX, CONTENT_Y + 3.5, 4.2, 1.8);
    addScaledImage(slide, "automl.png", 4.5, CONTENT_Y + 3.5, 4.2, 1.8);
    addScaledImage(slide, "benchmark_combined.png", 9, CONTENT_Y + 2.3, 3.7, 1.2);

    slide.addText("Geospatial", { x: MX, y: H - 0.55, w: 4.2, h: 0.3, fontSize: 11, fontFace: C.bodyFont, italic: true, color: C.textGray, align: "center" });
    slide.addText("AutoML Multi-Agent", { x: 4.5, y: H - 0.55, w: 4.2, h: 0.3, fontSize: 11, fontFace: C.bodyFont, italic: true, color: C.textGray, align: "center" });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// E. CONCLUSION (Slides 20–24, ~5 min)
// ═══════════════════════════════════════════════════════════════════════════════

function buildConclusion() {
  addSectionDivider("\u603B\u7ED3", "Conclusion");

  // ── Slide 21: \u5B9A\u4F4D\u4E0E\u8D21\u732E ────────────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u5B9A\u4F4D\u4E0E\u8D21\u732E\u603B\u7ED3");

    // Top: 4 generations
    const gens = [
      { gen: "Gen 0", label: "Text-Only", color: C.textGray },
      { gen: "Gen 1", label: "JSON FC", color: C.blue },
      { gen: "Gen 2", label: "Code-as-Action", color: C.orange },
      { gen: "Gen 3", label: "Stateful Runtime", color: C.green },
    ];
    gens.forEach((g, i) => {
      const cx = MX + 0.2 + i * 3.1;
      slide.addShape(pres.shapes.RECTANGLE, { x: cx, y: CONTENT_Y + 0.1, w: 2.8, h: 0.7, fill: { color: g.color } });
      slide.addText(`${g.gen}: ${g.label}`, { x: cx, y: CONTENT_Y + 0.1, w: 2.8, h: 0.7, fontSize: 14, fontFace: C.bodyFont, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
      if (i < 3) {
        slide.addText("\u2192", { x: cx + 2.75, y: CONTENT_Y + 0.1, w: 0.4, h: 0.7, fontSize: 20, fontFace: C.bodyFont, color: C.darkBrown, align: "center", valign: "middle", margin: 0 });
      }
    });

    // 3 contribution cards
    const contribs = [
      { num: "1", title: "\u53CC\u6D41\u67B6\u6784 + Skills", points: "Semantic + Runtime stream\n\u8FD0\u884C\u65F6\u6280\u80FD\u7BA1\u7406", color: C.blue },
      { num: "2", title: "\u53EF\u7F16\u7A0B\u9A8C\u8BC1 + RLVR", points: "\u786E\u5B9A\u6027\u72B6\u6001\u68C0\u67E5\n\u81EA\u52A8\u5316\u5956\u52B1\u4FE1\u53F7", color: C.green },
      { num: "3", title: "\u5168\u9762\u5B9E\u9A8C\u9A8C\u8BC1", points: "11/12 Tau\u00B2-bench\n+40.9% BFCL, -28.4% tokens", color: C.orange },
    ];
    contribs.forEach((c, i) => {
      const cx = MX + 0.2 + i * 4.15;
      const cy = CONTENT_Y + 1.2;
      addCard(slide, cx, cy, 3.85, 2.5, c.color);

      slide.addShape(pres.shapes.OVAL, { x: cx + 1.55, y: cy + 0.15, w: 0.5, h: 0.5, fill: { color: c.color } });
      slide.addText(c.num, { x: cx + 1.55, y: cy + 0.15, w: 0.5, h: 0.5, fontSize: 20, fontFace: C.bodyFont, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
      slide.addText(c.title, { x: cx + 0.2, y: cy + 0.8, w: 3.5, h: 0.4, fontSize: 16, fontFace: C.bodyFont, bold: true, color: C.darkBrown, align: "center", margin: 0 });
      slide.addText(c.points, { x: cx + 0.2, y: cy + 1.3, w: 3.5, h: 1.0, fontSize: 13, fontFace: C.bodyFont, color: C.textGray, align: "center", margin: 0 });
    });

    addCalloutBox(slide, "\u4ECE text-bound \u5230 runtime-native \u662F\u6839\u672C\u6027\u63D0\u5347\uFF0C\u663E\u8457\u6539\u5584\u4E86\u51C6\u786E\u7387\u3001\u6548\u7387\u548C\u72B6\u6001\u7BA1\u7406\u80FD\u529B", MX + 0.5, CONTENT_Y + 4.0, CONTENT_W - 1, 0.6, { borderColor: C.brown, bgColor: "FFF8EE", fontSize: 14 });
  }

  // ── Slide 22: \u5C40\u9650\u4E0E\u672A\u6765 ────────────────────────────────────────────────
  {
    const slide = pres.addSlide();
    addTitleBar(slide, "\u5C40\u9650\u4E0E\u672A\u6765\u65B9\u5411");

    addCard(slide, MX, CONTENT_Y + 0.1, 5.8, 3.5, "CC3333");
    slide.addText("\u5F53\u524D\u5C40\u9650", { x: MX + 0.25, y: CONTENT_Y + 0.2, w: 5.3, h: 0.4, fontSize: 17, fontFace: C.bodyFont, bold: true, color: "CC3333", margin: 0 });
    addBullets(slide, [
      "Python-centric: \u5DE5\u5177\u5FC5\u987B\u662F Python \u53EF\u8C03\u7528\u7684",
      "\u5185\u5B58\u968F\u5B58\u50A8\u5BF9\u8C61\u590D\u6742\u5EA6\u589E\u957F",
      "\u72B6\u6001\u7BA1\u7406 benchmark \u4ECD\u5728\u65E9\u671F\u9636\u6BB5",
      "\u591A Agent \u534F\u4F5C\u4EC5\u6709\u5B9A\u6027\u7ED3\u679C",
    ], MX + 0.3, CONTENT_Y + 0.75, 5.2, 2.5, { fontSize: 15 });

    addCard(slide, 6.8, CONTENT_Y + 0.1, 5.9, 3.5, C.green);
    slide.addText("\u672A\u6765\u65B9\u5411", { x: 7.05, y: CONTENT_Y + 0.2, w: 5.4, h: 0.4, fontSize: 17, fontFace: C.bodyFont, bold: true, color: C.green, margin: 0 });
    addBullets(slide, [
      "\u591A Agent \u7CFB\u7EDF\u7684\u4E25\u683C\u5B9A\u91CF\u8BC4\u6D4B",
      "\u5B8C\u5584\u72B6\u6001\u7BA1\u7406\u7684\u7EFC\u5408 benchmark",
      "\u957F\u671F\u4EFB\u52A1\u7684\u5185\u5B58\u7BA1\u7406\u7B56\u7565",
      "\u8DE8\u8BED\u8A00\u5DE5\u5177\u751F\u6001\u96C6\u6210",
    ], 7.1, CONTENT_Y + 0.75, 5.4, 2.5, { fontSize: 15 });
  }

  // ── Slide 23: Thank You ────────────────────────────────────────────────────
  {
    const slide = pres.addSlide();
    slide.background = { color: C.darkBg };

    const logoPath = path.join(IMG, "logo.png");
    if (fs.existsSync(logoPath)) {
      slide.addImage({ path: logoPath, x: W / 2 - 0.6, y: 0.8, w: 1.2, h: 1.2 });
    }

    slide.addText("\u8C22\u8C22\uFF01", {
      x: MX, y: 2.2, w: CONTENT_W, h: 0.9,
      fontSize: 48, fontFace: C.bodyFont, bold: true, color: C.white, align: "center", margin: 0,
    });

    slide.addShape(pres.shapes.RECTANGLE, { x: W / 2 - 1.5, y: 3.2, w: 3, h: 0.04, fill: { color: C.orange } });

    slide.addText("\u95EE\u7B54\u4E0E\u8BA8\u8BBA", {
      x: MX, y: 3.5, w: CONTENT_W, h: 0.6,
      fontSize: 24, fontFace: C.bodyFont, color: C.lightText, align: "center", italic: true,
    });

    slide.addText([
      { text: "arXiv: 2601.01569", options: { fontSize: 15, color: C.lightText, fontFace: C.bodyFont, breakLine: true } },
      { text: "GitHub: github.com/caveagent/cave-agent", options: { fontSize: 15, color: C.lightText, fontFace: C.bodyFont, breakLine: true } },
      { text: "PyPI: pip install cave-agent", options: { fontSize: 15, color: C.lightText, fontFace: C.bodyFont, breakLine: true } },
      { text: "", options: { fontSize: 8, breakLine: true } },
      { text: "Contact: junsong@hkbu.edu.hk  |  vanzl@u.nus.edu", options: { fontSize: 14, color: C.white, fontFace: C.bodyFont } },
    ], { x: MX + 2, y: 4.3, w: CONTENT_W - 4, h: 2.0, align: "center" });

    addSlideNumber(slide, true);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════

buildOpening();
buildArchitecture();
buildSkillsAndCapabilities();
buildExperiments();
buildConclusion();

pres.writeFile({ fileName: OUT }).then(() => {
  console.log(`Generated: ${OUT}`);
  console.log(`Total slides: ${slideNum}`);
}).catch(err => {
  console.error("Error:", err);
  process.exit(1);
});
