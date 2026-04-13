# CaveAgent 45-Minute Research Talk — 演讲提纲

---

## A. 开场 + 问题（Slides 1–5, ~7 min）

### Slide 1 — Title Slide
- 自我介绍，团队背景（HKGAI, 多校合作）
- 点明主题：把 LLM 从文本生成器变成有状态的运行时操作器

### Slide 2 — 背景与动机：JSON FC 的局限
- LLM Agent 已无处不在，JSON function calling 是主流范式
- 三个核心局限：序列化开销、无持久状态、可组合性差
- 结果：信息丢失 + 冗余计算 + context window 膨胀

### Slide 3 — 文本化瓶颈
- 左右对比：当前 text-bound 方法 vs CaveAgent runtime-native
- 核心信息：持久运行时消除了文本化瓶颈

### Slide 4 — 范式演进
- evolve.png 全图：Gen 0 → Gen 1 → Gen 2 → Gen 3
- 我们的定位：Gen 3 — stateful runtime operators

### Slide 5 — 愿景与贡献
- 核心研究问题
- 三大贡献：双流架构、可编程验证/RLVR、全面验证

---

## B. 核心架构（Slides 6–10, ~10 min）

### Slide 6 — Section Divider
- 过渡："核心架构"

### Slide 7 — 双流架构总览
- framework.png 全图
- Semantic Stream（推理）+ Runtime Stream（持久环境）

### Slide 8 — 形式化模型与核心洞察
- 两个公式：h_t = LLM(x_t, h_{t-1}) 和 S_t = Exec(c_t, S_{t-1})
- 核心洞察：解耦！runtime 才是主要工作空间
- CaveAgent.run() 核心循环

### Slide 9 — 运行时流与注入 API
- 代码示例：Variable、Function、Type 注入
- IPython 持久内核，对象跨 step 存活
- LLM 看元数据，代码操作真实对象

### Slide 10 — 上下文同步与安全模型
- 左：三个同步机制（State Summary / Observation Shaping / Progressive Disclosure）
- 右：AST-based 安全检查 + 自纠正流程

---

## C. 技能与能力（Slides 11–14, ~8 min）

### Slide 11 — Section Divider
- 过渡："技能与能力"

### Slide 12 — Skills 架构与对比
- skills.png + 兼容 agentskills.io 标准
- injection.py 中 __exports__ 导出 → 直接注入 runtime
- 对比表：Standard vs CaveAgent Skills（函数、状态、成本）

### Slide 13 — 下游应用与多 Agent 协作
- downstream_applications.png + town_simulation.png
- Agent 作为 runtime 对象，共享 runtime
- RLVR 基础：runtime state 可确定性访问 → 自动化评测

### Slide 14 — 智能家居演示
- smarthome.png
- 设备状态/场景/自动化跨多轮持久保存

---

## D. 实验验证（Slides 15–19, ~10 min）

### Slide 15 — Section Divider
- 过渡："实验验证"

### Slide 16 — 实验设置
- Benchmark：Tau²-bench、BFCL、自定义状态管理
- 6 个 SOTA LLM（3 开源 + 3 闭源），每个 3 次
- 同一模型/工具/任务，只换交互范式
- 预览三个大数字：11/12 胜出、+40.9%、-28.4%

### Slide 17 — Tau²-bench 结果
- 完整 12 行表格，11/12 CaveAgent 胜出
- 重点：Qwen3 Retail +13.5%、Kimi Retail +10.5%
- 唯一下降：Claude Airline -0.6%

### Slide 18 — BFCL 结果与 Token 效率
- 左：BFCL 表格，DeepSeek 无 prompt 53.1% → 94.0% (+40.9%)
- 右：-28.4% token、-38.6% 步骤 + token_consumption 图

### Slide 19 — 状态管理 Benchmark 与案例研究
- 左：type proficiency 雷达图 + multi-variable 热力图
- 右：数据密集任务三方对比（CaveAgent vs CodeAct vs JSON FC）
- 底部：geospatial + automl 领域应用

---

## E. 总结（Slides 20–23, ~5 min）

### Slide 20 — Section Divider
- 过渡："总结"

### Slide 21 — 定位与贡献总结
- 四代演进定位条（Gen 0 → Gen 3）
- 三大贡献卡片回顾
- 底部总结：从 text-bound → runtime-native 是根本性提升

### Slide 22 — 局限与未来方向
- 左：局限（Python-centric、内存增长、benchmark 不完善、多 agent 定性）
- 右：未来（定量多 agent、完善 benchmark、内存管理、跨语言）

### Slide 23 — 谢谢！问答与讨论
- Logo + 联系方式 + 链接
