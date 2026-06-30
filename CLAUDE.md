# Brain News — Weekly Digest

Automated weekly pipeline that collects brain-related news, stores it in a CSV, and publishes a Notion page.

---

## Run on startup

Every time you are invoked in this project, start by running the gate check:

```bash
python check_news.py
```

Read the JSON output and do **both** of the following:

### A — Follow-up on past stories

If `pending_followups` is non-empty, each entry is a Notion page containing articles that had a `review_date` set — meaning Claude previously judged that those stories would have meaningful updates by now.

For each page in `pending_followups`:
1. For each article in `page.articles`, search the web for recent developments on that specific story (use the original title + URL as search context)
2. If new developments are found: append an **"## 🔁 Updates — {today}"** section to the existing Notion page, summarizing what changed
3. **Update the page title prefix** — fetch the *current* Notion page title first (the user may have removed the emoji after reading), then apply:
   - No prefix (user read it) → add `🔄`
   - Prefix is `❌` → replace with `🔄`
   - Prefix is already `🔄` → leave as-is
4. Update `notion_page_title` in brain_news.csv for **all rows sharing that `notion_page_id`** to match the new title

If no meaningful update is found for a story, skip it silently (do not append empty sections).

### B — Weekly processing

- If `should_process` is `false` → stop here (week is done).
- If `should_process` is `true` → run the full pipeline below.

---

## Full Weekly Pipeline

### Step 1 — Search for news

Search the web for articles published **in the past 7 days** (from `week_start` to `week_end` as given by the script).

Use multiple targeted searches covering these topics:

| Topic | Category tag | Page section emoji |
|---|---|---|
| Living neural networks & organoids | `organoids` | 🧬 |
| Neuromorphic computing | `neuromorphic` | ⚡ |
| Spiking neural networks & STDP | `snn-stdp` | 🔵 |
| Brain-computer interfaces | `bci` | 🦾 |
| Neuroscience discoveries | `neuroscience` | 🔬 |
| Neuroprosthetics | `neuroprosthetics` | 🩺 |
| Wetware / biocomputers | `wetware` | 🌊 |
| Memory & cognition | `cognition` | 💭 |
| Connectomics & brain mapping | `connectomics` | 🕸️ |

Example search queries per topic:
- `"DishBrain" OR "cortical organoid" news 2026`
- `"neuromorphic chip" 2026`, `"Intel Loihi" OR "IBM NorthPole" OR "SpiNNaker" 2026`
- `"spiking neural network" research 2026`, `"SNN" "STDP" 2026`
- `"Neuralink" OR "Synchron" OR "BrainGate" 2026`
- `"synaptic plasticity" discovery 2026`, `"BRAIN Initiative" 2026`
- `"connectomics" 2026`, `"FlyWire" OR "H01" 2026`
- `"neuroprosthetics" OR "neural prosthetic" 2026`
- `"wetware" OR "biocomputer" OR "bio-silicon" 2026`
- `"memory consolidation" neuroscience 2026`, `"hippocampus" discovery 2026`

**Collect at minimum 5 articles, aim for 10–15.**

**Strict exclusions — do NOT include:**
- Generative AI / LLMs (ChatGPT, GPT-x, Gemini, Claude, Llama, diffusion models)
- Standard deep learning or transformer architecture news
- AI chatbot or assistant product launches
- Cryptocurrency or unrelated tech

Each article must have: title, URL, publication date, 2–3 sentence plain-English summary, and a category from the table above.

---

### Step 2 — Deduplicate

Load the `existing_urls` array from the `check_news.py` JSON output.

Filter out any article whose URL already appears in that list.

If **all found articles are duplicates**:
- Do not create a Notion page
- Do not update the CSV
- Write: `[SKIP] No new articles this week.`
- Stop.

---

### Step 3 — Create a Notion subpage

Create a new page **inside** the Brain Knowledge page:
- **Parent page ID:** `38fdecc0c4b780ae8a5df4df850c29fb`
- **Page icon emoji:** 🧠 (always — this is the topic icon, separate from the title prefix)
- **Page title:** `❌ 🧠 Brain News — Week of {week_start}`
  - `❌` = unread status prefix (user will delete this when they've read the page)
  - `🧠` = topic emoji (part of the permanent title)
  - These two emojis serve different purposes and must both be present

Page content structure:

```
# 🧠 Brain News — Week of {week_start} to {week_end}

## Summary
[2–3 sentence overview of the week's themes]

---

## {section_emoji} {Category Name}

### [Article Title]
**Source:** [Article Title]({url})
**Date:** {publication_date}

{2–3 sentence summary in plain English, no jargon}

---
[group articles by category, one section per category that has articles]
```

Use the section emoji from the topic table above for each category heading.

Save the Notion page ID and full URL of the created page.

**If updating an existing page** (adding articles to a page already created this week):
- Fetch the current Notion page title first, then apply the same prefix logic:
  - No prefix → add `🔄`
  - `❌` → replace with `🔄`
  - `🔄` → leave as-is
- Append new article sections to the page content
- Update `notion_page_title` in the CSV for all rows with that `notion_page_id`

---

### Step 4 — Update the CSV

Append one row per new article to `brain_news.csv`:

| Column | Value |
|---|---|
| `week_start` | from check_news.py output |
| `title` | article title |
| `url` | article URL |
| `summary` | 2–3 sentence plain-English summary |
| `category` | one of the category tags above |
| `notion_page_id` | Notion page ID returned after creation |
| `notion_page_title` | full page title including emoji prefix, e.g. `❌ 🧠 Brain News — Week of 2026-06-29` |
| `notion_page_url` | full URL of the Notion page |
| `review_date` | **set by Claude based on article content** (see rules below) |
| `added_date` | today's date (YYYY-MM-DD) |

**Rules for setting `review_date`:**

Claude reads each article and decides whether a follow-up will be meaningful:

- **Set a specific date** when the article describes something time-bound:
  - Clinical trial with results expected in N weeks/months → `added_date + N weeks`
  - Animal study moving to human trials → 3–6 months out
  - A chip or technology entering production → 3 months out
  - A paper announcing upcoming experiments → 4–8 weeks out
  - A conference presentation with follow-up study planned → 2–3 months out

- **Leave empty (null)** when:
  - The article is a general discovery or retrospective finding
  - No concrete future milestone is mentioned
  - The story is self-contained (a published result, not an ongoing trial)

The `review_date` tells Claude to come back and search for updates on that story. Set it only when there's a real reason to expect new developments.

Use `csv.DictWriter` with `extrasaction='ignore'` and append mode so existing rows are not touched.

---

### Step 5 — Git push

Always commit and push directly to `main`. Never create feature branches or sub-branches for this pipeline.

```bash
git add brain_news.csv
git commit -m "feat: brain news week of {week_start}"
git push origin main
```

If the push fails because the remote is ahead, do `git pull --rebase origin main` first, then push again.

If the session has checked out a non-main branch, switch back to main before committing:

```bash
git checkout main
git add brain_news.csv
git commit -m "feat: brain news week of {week_start}"
git push origin main
```

---

## Topic Reference

The project tracks **brain science and neuromorphic engineering**, both biological and silicon-based. It explicitly excludes generative AI / large language models.

**In scope:**
- Organoids, living neural networks, DishBrain, Cortical Labs
- Neuromorphic chips: Intel Loihi, IBM NorthPole, SpiNNaker, BrainScaleS
- Spiking neural networks (SNN), STDP learning rules, event-driven computing
- Brain-computer interfaces (BCIs): Neuralink, Synchron, BrainGate, Blackrock Neurotech
- Neuroscience discoveries: plasticity, memory, sleep, consciousness
- Connectomics: mapping neural circuits (FlyWire, H01, BRAIN Initiative)
- Neuroprosthetics: sensory restoration, motor control
- Wetware, bio-silicon hybrid systems, biocomputers
- Cognitive neuroscience, psychedelics research on brain function

**Out of scope:**
- Generative AI, LLMs, image/video generation, chatbots
- Standard backpropagation deep learning (unless explicitly compared to biological learning)
- Robotics without neural/brain angle
- General health/medicine not related to brain function

---

## CSV Schema

```
week_start,title,url,summary,category,notion_page_id,notion_page_title,notion_page_url,review_date,added_date
```

Categories: `organoids`, `neuromorphic`, `snn-stdp`, `bci`, `neuroscience`, `neuroprosthetics`, `wetware`, `cognition`, `connectomics`

## Emoji Reference

| Use | Emoji | Meaning |
|---|---|---|
| Page icon (Notion) | 🧠 | Always — the topic icon |
| Title prefix — unread | ❌ | User hasn't read this page yet |
| Title prefix — updated | 🔄 | Page was updated after first publish |
| Title prefix — read | *(none)* | User removed the emoji |
| Section: organoids | 🧬 | |
| Section: neuromorphic | ⚡ | |
| Section: snn-stdp | 🔵 | |
| Section: bci | 🦾 | |
| Section: neuroscience | 🔬 | |
| Section: neuroprosthetics | 🩺 | |
| Section: wetware | 🌊 | |
| Section: cognition | 💭 | |
| Section: connectomics | 🕸️ | |
