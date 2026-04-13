"""Generate a formatted PDF of the CaveAgent talk speaker outline (23 slides)."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
F = "STSong-Light"

BROWN = HexColor("#B5784E")
DARK = HexColor("#3C2415")
BLUE = HexColor("#054488")
GREEN = HexColor("#056B34")
ORANGE = HexColor("#FF8800")
GRAY = HexColor("#666666")

outpath = "/mnt/data/wanzl/cave-agent/slides/speaker_outline.pdf"
doc = SimpleDocTemplate(outpath, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm, leftMargin=22*mm, rightMargin=22*mm, title="CaveAgent Talk Outline", author="CaveAgent Team")

styles = getSampleStyleSheet()
sTitle = ParagraphStyle("T", parent=styles["Title"], fontName=F, fontSize=22, leading=28, textColor=DARK, spaceAfter=4)
sSub = ParagraphStyle("Sub", parent=styles["Normal"], fontName=F, fontSize=12, leading=16, textColor=GRAY, alignment=TA_CENTER, spaceAfter=14)
sSec = ParagraphStyle("Sec", parent=styles["Heading1"], fontName=F, fontSize=16, leading=20, textColor=BROWN, spaceBefore=16, spaceAfter=5, borderWidth=0)
sSlide = ParagraphStyle("Sl", parent=styles["Heading2"], fontName=F, fontSize=13, leading=17, textColor=BLUE, spaceBefore=9, spaceAfter=2, leftIndent=0)
sB = ParagraphStyle("B", parent=styles["Normal"], fontName=F, fontSize=10.5, leading=15, textColor=DARK, leftIndent=18, bulletIndent=6, spaceBefore=1, spaceAfter=1)
sSB = ParagraphStyle("SB", parent=sB, fontName=F, fontSize=10, leading=14, leftIndent=34, bulletIndent=22, textColor=GRAY)
sTr = ParagraphStyle("Tr", parent=styles["Normal"], fontName=F, fontSize=10.5, leading=14, textColor=ORANGE, leftIndent=18, spaceBefore=1, spaceAfter=1)

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=BROWN, spaceBefore=6, spaceAfter=6)

s = []  # story

s.append(Paragraph("CaveAgent 45-Minute Research Talk", sTitle))
s.append(Paragraph("演讲提纲 (24 slides)", sSub))
s.append(hr())

# ── A ──
s.append(Paragraph("A. 开场 + 问题（Slides 1\u20136, ~8 min）", sSec))

s.append(Paragraph("Slide 1 \u2014 <b>Title Slide</b>", sSlide))
s.append(Paragraph("点明主题：把 LLM 从文本生成器变成有状态的运行时操作器", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 2 \u2014 <b>关于我们</b>", sSlide))
s.append(Paragraph("左：万政霖（NUS Ph.D., HPC-AI Lab, Prof. Yang You）", sB, bulletText="\u2022"))
s.append(Paragraph("研究方向：LLM Agents + RL、self-evolving agents、agent systems", sSB, bulletText=""))
s.append(Paragraph("代表工作：CaveAgent、EBC (ICML 2025)、POI Rec (AAAI 2025 oral)", sSB, bulletText=""))
s.append(Paragraph("右：HKGAI（InnoHK 支持，2023 成立，HKUST Prof. Yike Guo 领导）", sB, bulletText="\u2022"))
s.append(Paragraph("6 所 QS 百强香港高校 + NUS，多模态/垂直领域基础模型", sSB, bulletText=""))
s.append(Paragraph("CaveAgent 是 HKGAI 核心技术产品 HK E-Link 的底层框架", sSB, bulletText=""))

s.append(Paragraph("Slide 3 \u2014 <b>背景与动机：JSON FC 的局限</b>", sSlide))
s.append(Paragraph("LLM Agent 已无处不在，JSON function calling 是主流范式", sB, bulletText="\u2022"))
s.append(Paragraph("三个核心局限：序列化开销、无持久状态、可组合性差", sB, bulletText="\u2022"))
s.append(Paragraph("结果：信息丢失 + 冗余计算 + context window 膨胀", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 4 \u2014 <b>文本化瓶颈</b>", sSlide))
s.append(Paragraph("左右对比：当前 text-bound 方法 vs CaveAgent runtime-native", sB, bulletText="\u2022"))
s.append(Paragraph("核心信息：持久运行时消除了文本化瓶颈", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 5 \u2014 <b>范式演进</b>", sSlide))
s.append(Paragraph("evolve.png 全图：Gen 0 \u2192 Gen 1 \u2192 Gen 2 \u2192 Gen 3", sB, bulletText="\u2022"))
s.append(Paragraph("我们的定位：Gen 3 \u2014 stateful runtime operators", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 6 \u2014 <b>愿景与贡献</b>", sSlide))
s.append(Paragraph("提出核心研究问题", sB, bulletText="\u2022"))
s.append(Paragraph("三大贡献：双流架构、可编程验证/RLVR、全面验证", sB, bulletText="\u2022"))

s.append(hr())

# ── B ──
s.append(Paragraph("B. 核心架构（Slides 7\u201311, ~10 min）", sSec))

s.append(Paragraph("Slide 7 \u2014 <b>Section Divider</b>", sSlide))
s.append(Paragraph('过渡：\u201C核心架构\u201D', sTr))

s.append(Paragraph("Slide 8 \u2014 <b>双流架构总览</b>", sSlide))
s.append(Paragraph("framework.png 全图", sB, bulletText="\u2022"))
s.append(Paragraph("Semantic Stream（推理）+ Runtime Stream（持久环境）", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 9 \u2014 <b>形式化模型与核心洞察</b>", sSlide))
s.append(Paragraph("h<sub>t</sub> = LLM(x<sub>t</sub>, h<sub>t-1</sub>) 和 S<sub>t</sub> = Exec(c<sub>t</sub>, S<sub>t-1</sub>)", sB, bulletText="\u2022"))
s.append(Paragraph("核心洞察：解耦！runtime 才是主要工作空间", sB, bulletText="\u2022"))
s.append(Paragraph("CaveAgent.run() 核心循环", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 10 \u2014 <b>运行时流与注入 API</b>", sSlide))
s.append(Paragraph("代码示例：Variable、Function、Type 注入", sB, bulletText="\u2022"))
s.append(Paragraph("IPython 持久内核，对象跨 step 存活", sB, bulletText="\u2022"))
s.append(Paragraph("LLM 看元数据，代码操作真实对象", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 11 \u2014 <b>上下文同步与安全模型</b>", sSlide))
s.append(Paragraph("左：State Summary / Observation Shaping / Progressive Disclosure", sB, bulletText="\u2022"))
s.append(Paragraph("右：AST-based 安全检查 + 自纠正流程", sB, bulletText="\u2022"))

s.append(hr())

# ── C ──
s.append(Paragraph("C. 技能与能力（Slides 12\u201315, ~8 min）", sSec))

s.append(Paragraph("Slide 12 \u2014 <b>Section Divider</b>", sSlide))
s.append(Paragraph('过渡：\u201C技能与能力\u201D', sTr))

s.append(Paragraph("Slide 13 \u2014 <b>Skills 架构与对比</b>", sSlide))
s.append(Paragraph("兼容 agentskills.io + injection.py 扩展", sB, bulletText="\u2022"))
s.append(Paragraph("对比表：Standard vs CaveAgent Skills（函数、状态、成本）", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 14 \u2014 <b>下游应用与多 Agent 协作</b>", sSlide))
s.append(Paragraph("Agent 作为 runtime 对象，共享 runtime", sB, bulletText="\u2022"))
s.append(Paragraph("RLVR 基础：runtime state 可确定性访问 \u2192 自动化评测", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 15 \u2014 <b>智能家居演示</b>", sSlide))
s.append(Paragraph("smarthome.png \u2014 设备状态/场景/自动化跨多轮持久保存", sB, bulletText="\u2022"))

s.append(hr())

# ── D ──
s.append(Paragraph("D. 实验验证（Slides 16\u201320, ~10 min）", sSec))

s.append(Paragraph("Slide 16 \u2014 <b>Section Divider</b>", sSlide))
s.append(Paragraph('过渡：\u201C实验验证\u201D', sTr))

s.append(Paragraph("Slide 17 \u2014 <b>实验设置</b>", sSlide))
s.append(Paragraph("Tau\u00B2-bench、BFCL、自定义状态管理 benchmark", sB, bulletText="\u2022"))
s.append(Paragraph("6 个 SOTA LLM（3 开源 + 3 闭源），每个 3 次", sB, bulletText="\u2022"))
s.append(Paragraph("预览：<b>11/12 胜出、+40.9% BFCL、-28.4% token</b>", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 18 \u2014 <b>Tau\u00B2-bench 结果</b>", sSlide))
s.append(Paragraph("11/12 设置 CaveAgent 胜出", sB, bulletText="\u2022"))
s.append(Paragraph("Qwen3 Retail +13.5%, Kimi Retail +10.5%, 平均 ~4.7%", sSB, bulletText=""))
s.append(Paragraph("唯一下降：Claude Airline -0.6%", sSB, bulletText=""))

s.append(Paragraph("Slide 19 \u2014 <b>BFCL 结果与 Token 效率</b>", sSlide))
s.append(Paragraph("DeepSeek 无 prompt: 53.1% \u2192 94.0% (+40.9%)", sB, bulletText="\u2022"))
s.append(Paragraph("-28.4% token、-38.6% 步骤、+5.4% 成功率", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 20 \u2014 <b>状态管理 Benchmark 与案例研究</b>", sSlide))
s.append(Paragraph("Type proficiency 雷达图 + multi-variable 热力图", sB, bulletText="\u2022"))
s.append(Paragraph("数据密集任务三方对比 + geospatial/automl 领域应用", sB, bulletText="\u2022"))

s.append(hr())

# ── E ──
s.append(Paragraph("E. 总结（Slides 21\u201324, ~5 min）", sSec))

s.append(Paragraph("Slide 21 \u2014 <b>Section Divider</b>", sSlide))
s.append(Paragraph('过渡：\u201C总结\u201D', sTr))

s.append(Paragraph("Slide 22 \u2014 <b>定位与贡献总结</b>", sSlide))
s.append(Paragraph("四代演进定位：Gen 0 \u2192 Gen 3", sB, bulletText="\u2022"))
s.append(Paragraph("三大贡献卡片回顾", sB, bulletText="\u2022"))
s.append(Paragraph("底部总结：text-bound \u2192 runtime-native 是根本性提升", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 23 \u2014 <b>局限与未来方向</b>", sSlide))
s.append(Paragraph("局限：Python-centric、内存增长、benchmark 不完善、多 agent 定性", sB, bulletText="\u2022"))
s.append(Paragraph("未来：定量多 agent、完善 benchmark、内存管理、跨语言", sB, bulletText="\u2022"))

s.append(Paragraph("Slide 24 \u2014 <b>谢谢！问答与讨论</b>", sSlide))
s.append(Paragraph("Logo + 联系方式 + 链接", sB, bulletText="\u2022"))

doc.build(s)
print(f"PDF: {outpath}")
