# DECISIONS.md — Investment Research Dashboard

---

## 1. Which Option Did You Choose and Why?

I built an **AI-powered financial research assistant** — a website where you type a question like *"How is Apple doing?"* and instead of getting a wall of text back, you get a proper visual dashboard: a price chart, a company summary card, recent news headlines, and a risk overview — all generated automatically.

Think of it like asking a research analyst a question and getting back a fully formatted report instead of a long email.

The key idea is that the AI never just writes a paragraph and calls it done. It is forced to go out and fetch real data first — live stock prices, actual news articles — and then package everything into a structured format that the website knows how to display as charts and cards.

I chose to build this with **one AI assistant** doing all the work rather than a team of AI agents handing tasks off to each other. The reason is simple: the job is naturally step-by-step — first get the stock data, then get the news, then write the summary. Adding multiple AI agents coordinating with each other would have been like hiring five project managers for a one-person job. More complexity, same output.

---

## 2. Why This Tech Stack? What Alternatives Did You Consider?

Think of the app as having four parts: the **website** you see, the **server** that handles requests behind the scenes, the **database** that stores your data, and the **AI brain** that does the research. Each part needed a tool to build it.

### Server — FastAPI (Python)

**Chosen**: The server is built in Python using a framework called FastAPI.

The main reason is that all the AI tools — the ones that fetch stock prices, search for news, and look through financial documents — are Python libraries. Building the server in Python too means everything runs in the same environment, like keeping all your kitchen appliances on the same countertop rather than in different rooms.

**What else was considered**:
- **Node.js**: A popular server technology, but it doesn't speak Python natively. Using it would have meant running a separate Python process just for the AI parts, like having a translator in every conversation.
- **Django**: Another Python option, but heavier and slower for this use case — like using a lorry to deliver one package.

### Website — Next.js (React)

**Chosen**: The front-end website is built with Next.js, which is a framework built on top of React (the tool most modern websites use).

The main advantage is that parts of the page can be checked on the server before being sent to your browser. This means you never see a flash of the login page when you are already signed in.

**What else was considered**:
- **Plain React (Vite)**: Simpler to set up, but the whole page loads in your browser first — meaning for a split second, a logged-in user could see the login screen before the app catches up.
- **Remix**: A newer option with good features, but a smaller community, so finding help and ready-made components would have taken longer.

### AI Brain — Groq (Llama 3.3)

**Chosen**: The AI that reads your question and decides what to do is a model called Llama 3.3, running on Groq's servers.

Groq is exceptionally fast — it can generate an answer in a few seconds where other providers take 20–30 seconds. For a dashboard where you are waiting for results, speed matters enormously. The model is also good enough to follow strict formatting rules, which is critical because the AI must output data in a very specific structure, not just write a free-form paragraph.

**What else was considered**:
- **Google Gemini**: Was actually used first, but it kept changing how its responses were formatted between software versions, causing unpredictable crashes. Switched to Groq for reliability.
- **OpenAI (ChatGPT)**: Excellent quality, but costs money per request. Not suitable for a portfolio project that should run for free.
- **Ollama (running AI on your own computer)**: Free and private, but without a dedicated graphics card, it takes 60–90 seconds to answer one question — far too slow for an interactive tool.

### Database — PostgreSQL

**Chosen**: User accounts, saved reports, and watchlists are stored in PostgreSQL — the most widely used open-source database in the world.

Saved research reports contain complex, flexible data (charts, tables, news sections all bundled together). PostgreSQL has a feature called JSONB that lets you store this kind of flexible data in one column, like having a filing cabinet that can hold both standard forms and free-form notes without needing a separate drawer for each.

**What else was considered**:
- **MongoDB**: Designed for flexible data, but adds a separate service to run and loses some of the reliability guarantees needed for storing user accounts and passwords safely.
- **SQLite**: Zero setup required, but not designed for multiple people using it at the same time — like a single-user spreadsheet rather than a shared database.

### Document Search — FAISS (local file)

**Chosen**: The AI can also search through financial documents (like earnings reports). This search is powered by FAISS — a tool that finds documents by meaning rather than exact keywords, and runs entirely on the local machine from a pre-built index file.

**What else was considered**:
- **Pinecone / Weaviate**: Cloud-hosted document search services. Great for production apps, but require an account and cost money — not appropriate for a portfolio demo.
- **pgvector**: Would have kept everything inside the same database, but requires a special database extension that isn't included in the standard setup.

---

## 3. How Did You Approach Multi-Tenancy?

**Multi-tenancy** just means: many different users storing their own private data in the same system, without ever seeing each other's data. Think of it like a block of flats — everyone shares the same building and the same plumbing, but each flat is completely private.

**The approach used here**: When you sign up, the system automatically creates a private workspace for you behind the scenes. You never see it or name it — it just exists. Every report you save and every company you add to your watchlist is silently tagged with your workspace ID.

When you later ask to see your reports, the system only ever looks for reports tagged with *your* workspace ID. Even if someone else somehow guessed the ID of one of your reports, the system would check whether that report belongs to their workspace — and since it doesn't, it would respond as if it doesn't exist at all. This prevents people from even confirming whether something exists in someone else's account.

**Why this design?** It keeps the sign-up experience dead simple (just email and password), while giving the database the full structure needed to support teams sharing a workspace in the future — without changing anything in the database.

**Why not use a database-level lock instead?** There is a stronger version of this isolation that happens inside the database itself. It was not used here because it is significantly harder to set up with the async database library being used, and a misconfiguration would be invisible until data leaked. The approach taken is simpler and every rule is written in plain code that can be read and reviewed easily.

---

## 4. How Did You Design the AI Integration?

The AI does not just answer questions from memory — it is designed to behave like a researcher who is required to go look things up before writing a report.

Here is how it works in plain terms: you ask a question, the AI reads it, decides which tools to use (stock price fetcher, news searcher, document search), calls those tools one by one, reads the results, and then writes a structured answer. The whole process is like a checklist a journalist follows before publishing a story.

**Key decisions made to make this work reliably**:

1. **Forced tool usage**: Left to its own devices, the AI would sometimes skip fetching real data and just write plausible-sounding numbers from memory — like a student making up statistics rather than citing sources. To prevent this, the instructions explicitly say: *"For any question about a company, you must always call the stock data tool AND the news tool — no exceptions."* This trades a small amount of unnecessary lookups for a guarantee of zero made-up data.

2. **Strict answer format**: The AI is told it must write its answer in a very specific structure — like filling in a form rather than writing a free-form essay. This is essential because the website needs to know exactly where to find the stock price, where to find the news articles, and where to find the chart data so it can display them correctly. Without this rule, the AI would sometimes add extra sentences before the data, which would break the display.

3. **Allowed section types**: The AI is given a fixed list of "section types" it can use (for example: company overview, price chart, news, risk analysis). If it tries to invent a new type that the website doesn't know how to display, the system strips it out. This keeps the display predictable.

4. **Partial results on failure**: If something goes wrong mid-way — for example the news API times out — the system doesn't show you a blank error screen. Instead, it uses whatever data it successfully collected and shows a partial report. Think of it like a restaurant that's run out of one dish: they serve you the rest of the meal rather than cancelling the whole order.

5. **Source labels on every section**: Every section of the report is labelled with where the data came from (e.g. "Yahoo Finance", "NewsAPI"). This powers the "Explainability" panel in the dashboard — so you can see exactly which tool produced which part of the answer.

---

## 5. What Trade-offs Did You Make Given the 5-Day Timeline?

Every project has a limited amount of time. Here are the corners that were deliberately cut, with an honest explanation of what was given up:

| What Was Built | Why | What Was Skipped |
|---|---|---|
| Document search uses a fixed, pre-loaded file | No extra service to set up or maintain | Users cannot upload their own documents to search |
| Each user gets their own private workspace automatically | Sign-up is just email + password, no complexity | Cannot invite teammates to share a workspace |
| Database tables are created fresh on every startup | Zero configuration needed | If the database structure changes, existing data is lost |
| Research queries run in the same process as everything else | No separate background worker needed | While a research query runs, other requests have to wait |
| News results are never cached | You always get the freshest news | The news API rate limit can be hit more quickly during demos |
| The server accepts requests from any website | Works instantly in any development setup | Not safe to leave this way in a real production deployment |
| Login tokens last 24 hours and cannot be silently renewed | Much simpler to build | Users get logged out once a day with no automatic re-login |

---

## 6. What Would You Improve With 2 More Weeks?

**Show results as they arrive, not all at once**: Right now, you submit a question and stare at a loading spinner for 5–15 seconds until the entire report is ready. With more time, the page would update section by section as each piece of data comes in — like watching a document print line by line rather than waiting for the whole page.

**Move heavy work to a background queue**: Currently the AI research runs inside the main web server. That means while one person's research is running, everyone else's requests are queued behind it. The fix is to hand the work off to a separate background worker — like a restaurant having a dedicated kitchen rather than the waiter cooking at the table.

**Proper database version history**: Right now, if the database structure needs to change, the easiest option is to wipe it and rebuild from scratch. With more time, a proper migration system would be added so changes can be applied gradually — like editing a document rather than rewriting it from scratch.

**Keep login sessions alive automatically**: Currently your login expires after 24 hours and you have to sign in again. The fix is a "silent refresh" — the app quietly gets a new login token in the background before the old one expires, so you are never interrupted.

**Also store login tokens more securely**: Currently the login token is stored in the browser in a way that JavaScript can read it — which is a known security risk. With more time it would be stored in a way that JavaScript cannot access, making it much harder to steal.

**Let users upload their own documents**: The document search currently only searches a fixed set of sample financial reports. With more time, users could upload their own PDFs — earnings reports, filings, articles — and the AI would be able to search through them too.

**Protect against overuse**: Nothing currently stops someone from hammering the "Research" button hundreds of times, burning through the free API quotas. A simple limit (e.g. 10 research requests per minute per user) would prevent this.

**More tests**: The project has end-to-end tests that check the full research flow. But individual unit tests for each small piece of logic are missing — making it harder to pinpoint exactly where something breaks if a bug appears.

---

## 7. What Was the Hardest Part and How Did You Solve It?

**The hardest part was getting the AI to write its answer in a reliable, consistent format — every single time.**

Imagine hiring a research assistant and giving them a report template to fill in. Most of the time they fill it in correctly. But occasionally they write a three-paragraph essay instead, or leave a field blank, or make up a number rather than looking it up. That was the problem here — except the "assistant" is an AI, and when it breaks the format, the website crashes or shows nothing.

Three specific problems kept appearing:

1. **The AI would sometimes write a half-finished answer** — like starting to fill in the form and stopping midway. This produced broken data that the system couldn't display.

2. **The AI would sometimes skip looking things up** — instead of fetching the real stock price, it would write a number it "remembered" from its training data. This is dangerous because that number could be months out of date or simply wrong.

3. **If one tool failed mid-way through, everything was lost** — if the news tool hit an error on step 3 of a 5-step process, the system would crash and throw away all the data it had already collected in steps 1 and 2.

**How each problem was solved**:

- **For the broken format**: The AI was switched to a mode where every single thing it outputs — whether it is asking for data or writing a final answer — must be written as a strict machine-readable structure. Think of it like telling the assistant they must always communicate via a specific form, never via free-text messages. This eliminated the broken-format problem entirely.

- **For the skipped lookups**: The instructions given to the AI were made extremely explicit — *"For any question about a company, you must look up the stock price AND search for news. Always. No exceptions."* This was tested repeatedly until the AI stopped skipping lookups.

- **For the lost data**: A "progress recorder" was added that runs silently alongside the AI. Every time the AI successfully fetches a piece of data, the recorder saves a copy of it independently. If the AI crashes at step 3, the recorder still has steps 1 and 2, and the system uses those to build a partial report — rather than showing you a blank screen.

---

## 8. How Did You Handle the LLM Token Budget Constraint?

**What is a "token budget"?** AI models don't read words — they read small chunks of text called tokens (roughly one token per word). Every AI provider sets a limit on how many tokens you can use per minute on a free account. Think of it like a phone plan with a monthly data cap — once you hit the limit, things slow down or stop working.

**The problem**: Each research query involves a back-and-forth conversation between the system and the AI. The system asks a question, the AI calls a tool, the tool sends back data, the AI reads that data, calls another tool, and so on. Each step adds more text to the conversation. By the end of a complex query — like "Compare four companies" — the total conversation had grown so large that the AI was hitting the token limit before it could finish writing the answer.

Three things went wrong when this happened:

1. **The AI stopped writing mid-answer** — like a typewriter running out of ribbon halfway through a sentence — leaving broken data the website couldn't display.

2. **The AI forgot earlier data** — on big comparison queries, by the time the AI was ready to write the final answer, the conversation was so long it had "forgotten" the first company's data it fetched, like trying to recite a long list you memorised an hour ago.

3. **The API refused to respond** — during back-to-back demo sessions, the per-minute token limit was completely exhausted and the API started returning errors mid-query.

**How each problem was solved**:

- **Slimmed down the data the AI receives back from each tool**: Each tool was tuned to send back only the essential numbers — for example, stock prices rounded to 2 decimal places and zero-data entries removed. This cut the size of a typical tool response by about 70%, leaving much more room in the budget for the actual answer.

- **Made the instructions shorter**: The instructions given to the AI were rewritten to be as concise as possible — like converting a three-page briefing document into a one-page checklist. This saved approximately 300 tokens on every single request.

- **Set a maximum number of steps**: The AI was told it can use at most 8 tool calls per query. This acts as a hard ceiling on how long the conversation can grow, ensuring the AI always has enough budget left to write its final answer.

- **The progress recorder as a safety net**: As explained in Section 7, a silent recorder saves every piece of data the AI successfully fetches. When a token-limit error cuts the query short, the system uses the saved data to produce a partial report rather than a blank error screen.

- **Tools report errors gracefully**: Each tool was updated to return a friendly error message (e.g. "News service temporarily unavailable") rather than crashing the entire system when it hits a rate limit. The AI reads this message, notes the tool didn't work, and continues building the best answer it can with the data it does have.

**What would be done with more time**: Rather than the AI doing everything in one long conversation, each tool call would be a separate background task that can be retried independently if it fails. This would be like having a team of researchers each working on one section of a report, rather than one person doing everything in one sitting.
