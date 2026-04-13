# CaveAgent Research Desk Speaker Notes

## Slide 1: Title

时间：20-25 秒

开场直接一句话：

“这是我们在 NUS CS5260 做的 final project，目标不是做一个静态看盘网页，而是做一个 public financial research agent。用户只需要输入 ticker 和问题，系统就会自动抓取公开数据，生成研究摘要、对比表和图表。”

## Slide 2: Why this product exists

时间：30-35 秒

这里强调痛点：

- 金融研究最麻烦的不是拿到单一数据，而是把价格、财报、宏观数据和结论串起来
- 传统 workflow 需要开很多网页、手动复制和整理
- 现场 demo 还会遇到 API 限流、模型延迟、结果不稳定的问题

收束到一句话：

“所以我们做的是一个 task-driven 的 research desk，而不是一个固定 dashboard。”

## Slide 3: Product overview

时间：35-40 秒

这一页解释输入和输出：

- 输入是 `tickers + natural language question`
- 中间是 CaveAgent runtime 和 finance skills
- 输出固定为三类 artifact：
  - markdown brief
  - comparison table
  - chart artifact

这页最好点一句：

“重点不是显示更多小组件，而是让 agent 根据问题决定应该生成什么。”

## Slide 4: System architecture

时间：40 秒

这一页讲技术实现，不要讲太细：

- 外层是结构化数据 provider：Alpha Vantage、SEC EDGAR、FRED
- 中间是 normalization layer，把不同数据源统一成 runtime objects
- 然后 CaveAgent 调用 skills，例如 market-data、fundamentals、comparison、charting
- 最后前端通过 SSE 实时显示执行过程和结果

一句话总结：

“我们先把数据结构化，再让 agent 推理，而不是直接把原始 JSON 塞给模型。”

## Slide 5: Grounding, safety, and cost control

时间：35 秒

这页是答辩时很有用的安全页：

- 数据是公开来源，不是凭空生成
- 产品定位是 `research assistant`，不是投资顾问
- 页面和结果都明确标注 `For research use only. Not investment advice.`
- 我们准备了 deterministic demo mode，所以现场展示可以做到 `SGD 0` 成本、零 API 风险

如果老师问为什么这样设计，直接回答：

“因为 final demo 最重要的是稳定性和可验证性。”

## Slide 6: 5-minute demo plan

时间：40 秒

按照这三个 case 讲：

1. `AAPL`
   目标是展示单股票研究能力
2. `AMD, NVDA`
   目标是展示 peer comparison 和 artifact 输出
3. `SPY`
   目标是展示 ETF 和 macro-aware framing

这页不用展开太多，主要是给老师一个清晰的 demo expectation。

## Slide 7: Why this is an agent, not a dashboard

时间：35-40 秒

这一页很关键，建议慢一点讲：

- 用户给的是开放式任务，不是点选固定筛选器
- 系统会根据任务调用不同 skills
- 输出形式会变，不是永远一张固定页面
- 整个过程有 artifact 生成、数据 grounding 和动态 summary

这里的核心句：

“如果换一个问题，系统的分析路径和最终产物都会变，这就是 agent behavior，而不是 static dashboard behavior。”

## Slide 8: Close

时间：20-25 秒

最后一句建议这样收：

“这版已经具备稳定课堂 demo、公开部署和低成本评测的条件。下一步我们只需要把它部署成 public URL，就能满足课程 final project 的 product deliverable。”

## Live Demo Order

实际演示时建议顺序：

1. 先打开首页，停 5 秒，让老师看到课程声明、公开数据源和 demo mode
2. 跑 `AMD, NVDA`，因为最能体现 agent 和 artifact
3. 如果时间够，再补 `AAPL` 或 `SPY`

## Backup Lines

如果老师问“为什么不用 web search”：

“v1 先用结构化公开金融数据保证稳定性和可验证性，新闻检索可以作为下一步增强，而不是核心依赖。”

如果老师问“为什么叫 agent”：

“因为它接收开放式任务，选择技能路径，组织多步处理，并返回不同类型的 artifact，而不是固定模板输出。”
