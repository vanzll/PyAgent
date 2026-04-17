# PyCallingAgent — English Speech Script (5–8 min, read aloud)

> Companion deck: `pycallingagent_technical_deck.pptx` (10 slides).
> Target length: ~7 minutes at a normal pace.
> Stage directions are in *italics*. Everything else is meant to be read out loud.

---

## Slide 1 — Title

*(Open on the title slide.)*

Hey everyone. So the thing I want to show you today is called **PyCallingAgent**.

In one line: it's a **financial research agent**, it runs on top of a live Python runtime, and we wrapped it up into a web app that anyone can actually click on.

Real quick before I start — I don't want to oversell this. PyCallingAgent is **not** a new agent framework. The runtime and the skills stuff underneath comes from the CaveAgent work. We just treat that as our engine. What we actually built is the product on top — the finance pipeline, the FastAPI web app, all the stuff that turns it into something you can point a browser at.

You can try it live at `pycallingagent.onrender.com`. And one disclaimer up front — this is a research demo, not financial advice. Please don't trade on it.

---

## Slide 2 — Problem and motivation

*(Advance to slide 2.)*

OK so, why not just use regular JSON function calling? It's everywhere, it works fine for chatbots.

Well, for finance-type tasks, it runs into three walls pretty fast.

First one — **you pay a serialization tax on everything**. Every DataFrame, every chart, every model, you have to flatten it into a string before the LLM can look at it again. That's a lot of tokens for nothing.

Second — **there's no memory between calls**. Every call starts from scratch. So if you loaded a dataset, or opened a connection, or trained a little model — too bad, it's gone on the next turn.

And third — **the model can't really compose things**. It can't just grab two objects in memory and chain them together with a couple lines of code. So instead, it ends up *describing* the data in text, over and over, instead of actually computing on it.

The takeaway here is pretty simple. For real research work, you want the LLM to **drive a live Python process**, not keep replaying text snapshots of one. That's basically the whole idea behind the project.

---

## Slide 3 — Design philosophy

*(Advance to slide 3.)*

So this slide is kind of our mental map. We think about tool calling as having gone through four generations.

Gen 0 is just plain chat — no tools at all. Gen 1 is JSON function calling, which is what most agents do today — stateless, strings in, strings out. Gen 2 is code-as-action, where the model writes code, you run it in a fresh sandbox every time, but it's still basically text going back and forth. And Gen 3 — the one we care about — is a **persistent runtime**. Same kernel, same namespace, objects actually stick around between turns.

PyCallingAgent sits on Gen 3. And to make Gen 3 actually work, you need three things.

You need a **twin-track loop** — one track for the LLM thinking, one track for the Python actually running. You need to be able to **inspect state deterministically** — because then you can check what happened, verify outputs, even score runs automatically. And you need **runtime-aware skills** — meaning skills don't just come in as text descriptions, they inject real callable objects into the kernel.

---

## Slide 4 — Core architecture

*(Advance to slide 4.)*

Alright, here's the architecture in one picture.

The top row is the **semantic track**. That's just the LLM history — `h_t` gets updated from the previous history plus the new input. Nothing fancy, pretty much what you'd expect.

The bottom row is the **runtime track**. That's a long-lived IPython kernel. Every step, a new code block runs, and the state `s_t` gets updated in place — same variables, same namespace as before.

Now the orange arrows in the middle — that's actually the key part. When code runs, we don't just dump all the output back into the prompt. We do **observation shaping** — which is a fancy way of saying we fold back only a short summary. A DataFrame with a thousand rows? The LLM just sees the shape, the column names, and the first few rows. The full object stays in the kernel.

The cool thing about this is that your **context stays tiny**, but your **workspace can be huge**. The context window stops being the thing you're fighting against.

---

## Slide 5 — Runtime and skills

*(Advance to slide 5.)*

OK so let's zoom in on how you actually use the runtime.

The code on the left shows the injection API. You spin up an IPython runtime, you hand it a real pandas DataFrame as a `Variable`, you hand it a Python function as a `Function`, and then you just give the runtime to the agent. No wrappers, no writing schemas by hand, nothing.

Three primitives to remember. **Variable** — literally any Python object, you can get it back by name. **Function** — a callable that shows up to the LLM along with its docstring. **Type** — schemas get pulled out automatically from Pydantic, dataclasses, Enums, whatever.

The skill stuff on the right is where the context savings really kick in. When you boot up, the LLM just sees the **metadata** for each skill — maybe 100 tokens each. The full instructions, the full callables, those only get pulled in when the model actually calls `activate_skill`. So the prompt is basically a table of contents, and the real library lives inside the runtime.

---

## Slide 6 — Financial research workflow

*(Advance to slide 6.)*

Alright, let's zoom out from the engine and look at the actual product. This is what happens after you press Send.

Five steps. **Step one, parse the prompt** — figure out whether it's a finance question or a regular one, and pull out any tickers or market proxies. **Step two, go grab the data** — SEC EDGAR for fundamentals, Alpha Vantage if we have a key, and a public-data fallback if everything else is down. **Step three, inject it into the runtime** — so the price frames, the fundamentals, the helper functions all become live variables. **Step four, run the agent loop** — now the LLM can actually call skills on real objects, instead of trying to remember numbers. And **step five, materialize outputs** — charts, tables, a markdown report, those little snapshot cards, all saved to the session.

Two quick things I want to flag. One — every single turn gives you both a language answer **and** a visible piece of work. That's why it feels more like an analyst than a dashboard. And two — if you just say "hello", it doesn't blow up. It just skips the finance pipeline and chats with you normally.

---

## Slide 7 — Application-layer adaptation

*(Advance to slide 7.)*

The agent part stays the same. The web layer is where we actually did product work.

Reading left to right: a **browser UI** — pretty minimal, just Jinja2 and vanilla JS; a **FastAPI service** that owns sessions, runs, streaming, artifact downloads; an **agent runner** that orchestrates one whole research pass; and a **data layer** that talks to SEC EDGAR and Alpha Vantage.

Below that there are three little product tricks worth calling out. **Session and run** — every prompt becomes a cancellable run, and the kernel gets reused across turns, which is what makes follow-up questions feel fast. **Live updates** — we push events over SSE, fall back to polling if the network's flaky, and the frontend just shows a sliding window of the latest events. And **artifact rendering** — tables and charts preview right in the page, full files are downloadable, and the markdown report gets rendered inline so you can actually read it without opening a file.

---

## Slide 8 — Deployment

*(Advance to slide 8.)*

Deployment is honestly pretty boring. That's on purpose — boring stuff doesn't break during a demo.

Three steps. **GitHub** is where the source lives. You push to `main`, Render picks it up and redeploys automatically. **Render** runs the web service — one `pip install`, one `uvicorn` command, and we get a public URL for free, no custom domain. And **config** is just a handful of environment variables — model credentials, a SEC user agent, and an optional Alpha Vantage key.

One thing I really want to flag here. The whole app can run in **public-data mode**, meaning it works even without the Alpha Vantage key. That sounds like a small thing, but honestly — that's the reason the demo still works when a free-tier API decides to rate-limit us ten minutes before a talk. It's saved us more than once.

The live URL, again — `pycallingagent.onrender.com`.

---

## Slide 9 — Demo 1

*(Advance to slide 9. Open the browser if you haven't already.)*

OK let me just show you what one turn actually looks like, instead of talking about it.

I'm gonna paste in: **"Summarize Apple and show the recent price trend."**

*(Submit the prompt.)*

So watch the Live Status panel on the side — you can see it going through the steps in real time. And when it finishes, you get a written summary, a price trend chart, a data table, and a downloadable report — all from that one prompt.

The thing I really want you to notice is — it's not reciting Apple facts from memory. It's actually computing them on real data inside the runtime while we watch. That's the whole difference.

---

## Slide 10 — Demo 2

*(Advance to slide 10.)*

One more, let's do a comparison this time.

Prompt: **"Compare AMD and Nvidia on valuation and performance."**

*(Submit the prompt.)*

This one's a bit meatier. You get a side-by-side comparison table, a chart with both tickers overlaid, and a markdown report you can download as a little research brief.

And that's basically the whole pitch. One prompt in, a small research report out. The runtime does the heavy lifting, the web layer makes it feel like a real product.

Thanks. Happy to take any questions.

---

## Anticipated Q&A

Four questions I think are pretty likely, with answers you can just read.

### Q1 — "How is PyCallingAgent different from CaveAgent? Is it just a rename?"

**Short answer:** No, it's a **product** built on CaveAgent.

**Longer answer:** So CaveAgent is the engine — it gives us the persistent Python runtime, the injection API, the skills system, the lazy loading, all of that. We treat it as a library. What PyCallingAgent adds is everything that makes it a **product** — the FastAPI service, the sessions and runs, the data layer pulling from SEC EDGAR, the runner that glues a research pass together, the artifact rendering on the frontend, the Render deployment. So when I'm talking about the runtime and the skills, that's the engine we use. When I'm talking about the finance pipeline and the web app — that's actually the work we did.

### Q2 — "You're letting an LLM generate and run Python code. Isn't that kind of dangerous?"

**Short answer:** Yeah, which is why no code hits the runtime without getting checked first.

**Longer answer:** It's not a raw `exec`. Before any generated code runs, it goes through an AST-level check. We've got rules for imports — so you can allow-list or block-list modules; rules for function calls — to block dangerous ones; rules for attribute access, and regex-based pattern scans for the weird stuff. If something fails, the agent gets a structured error back and can try again — the bad code never actually reaches the kernel. On top of that, for the deployed version, the runtime only sees stuff we injected — the price frames, the SEC data, the helper functions — it doesn't have access to arbitrary credentials or the host filesystem. So the usual layered approach — restrict what's possible first, then validate what's attempted.

### Q3 — "How do you know the outputs are actually grounded, not hallucinated?"

**Short answer:** The numbers come from real data that gets loaded **before** the LLM ever touches anything.

**Longer answer:** This is pretty much the whole reason we went injection-heavy. The agent doesn't read Apple's revenue as a sentence in its prompt — it sees a pandas DataFrame called `prices` or `fundamentals` that we populated from SEC EDGAR and the market data provider. When it spits out a chart or a table, that's computed over the DataFrame in the runtime, not pulled from memory. The LLM's job is to orchestrate — pick the right skill, slice the right columns, write the summary using the numbers it just computed — not to make the numbers up. That's why we call it "grounded". Now to be fully honest — the **summary prose** is still written by an LLM, so we're careful to frame the whole thing as research help, not as a certified financial report.

### Q4 — "What was the hardest thing you ran into, and what did you learn from it?"

**Short answer:** Honestly? Stuffing a **stateful** agent loop into a **stateless** web request model. Way harder than I thought it'd be. And the lesson was — spend time on the contract between the two worlds **before** you start writing product code.

**Longer answer:** OK so the thing is, CaveAgent underneath is really stateful. One long-lived Python kernel, variables that stick around, skills that accumulate. That's great. But a web server is basically the opposite — every HTTP request is short, users expect to cancel stuff, the network drops, the browser reconnects. Getting those two worlds to talk was actually the biggest source of pain for us.

More concretely, we kept getting stuck on three things. **How do you represent a "run"** so you can cancel it without killing the whole kernel? **How do you stream progress** in a way that survives someone's WiFi dropping? And **how do you handle errors** so one bad turn doesn't poison the whole session? Our first attempts tried to be clever — full bidirectional sockets, fancy lifecycle objects, all of that — and honestly everything just got fragile.

What ended up working was picking a really simple contract: **a session owns the kernel, a run owns one unit of work, and events are append-only.** Once we actually drew that line, everything else got easier. SSE with polling as a fallback just clicked into place. Cancellation is just marking the run as stopped. The UI can treat the event log as the source of truth, full stop.

So if I had to give a single takeaway for anyone doing similar stuff — when you wrap a stateful engine in a web product, the hard part is actually **not** the engine and **not** the UI. It's the small, boring contract in the middle. Get that right first. The rest is mostly plumbing.
