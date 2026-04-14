# PyCallingAgent Design And Deployment

## Slide 1
PyCallingAgent is our CS5260 final project. The product goal is simple: make a financial research tool feel like an agent, not a dashboard. One prompt goes in, and the system returns a chat answer plus visible outputs such as charts, tables, and downloadable artifacts.

## Slide 2
The design starts from four principles. First, prompt-first interaction: the user should not need to fill a complicated form. Second, artifact-oriented behavior: a useful agent should produce work products, not only text. Third, public-data grounding: the response should rely on real financial context. Fourth, resilience: the product must still look good even when free APIs become unreliable.

## Slide 3
The architecture is intentionally thin. The browser talks to a FastAPI service. The service manages sessions, runs, SSE events, and artifact downloads. The core runner prepares market data, injects structured variables into the CaveAgent runtime, and lets the model use skills. The data layer is separate, so we can swap live data, public-data mode, and stable fallbacks without changing the product UI.

## Slide 4
The execution flow is what makes this feel like an agent. After the user sends a prompt, the system infers the target ticker or market proxy, loads public data, runs the agent on normalized runtime objects, materializes outputs, and streams status back to the page. This keeps the interaction close to Manus-style products while staying simple enough for a class project.

## Slide 5
The deployment path is deliberately minimal. We push to GitHub, Render redeploys the service, and Render gives us a public URL. The required runtime configuration is small: the model ID, OpenAI API key, base URL, and SEC user agent. Alpha Vantage is optional now, because we removed the hard dependency on that key for a stable public demo.

## Slide 6
Why is this a good final project? Because it shows the full loop: LLM interaction, tool use, structured outputs, public deployment, and a usable product boundary. The live demo prompts are simple but representative: Apple for a single-stock brief, AMD versus Nvidia for comparison, and SPY for a market snapshot.
