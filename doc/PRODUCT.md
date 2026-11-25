# PRODUCT.md — Milo Product Definition

> Central reference for product design, domain modeling, architecture and AI engineering.
> Status: approved · 2026-11-25 · Source of decisions: `product/decisions-log.md`

---

## 1. Vision and purpose

**Milo is a personal assistant that keeps track of the user's practical life — money, commitments, tasks and notes — from what the user tells it in natural language. It learns how the user speaks and lives, and gives back reliable answers and reminders.**

Milo is not a general-knowledge assistant and not a flow-based chatbot. Its value lies in two things generic assistants don't offer: **knowing the user's life** and **never getting the user's numbers wrong**.

## 2. Problem

Organizing practical life takes too much effort. Most people don't track their spending, income or commitments — not for lack of will, but because spreadsheets and apps demand discipline, screens and categories, and almost nobody keeps it up for more than a few weeks. Decisions end up being made on gut feeling: *"Can I afford this?"*, *"Is my work worth it?"*, *"Where did my money go?"*

Milo makes recording **as easy as sending a message** and turns those records into answers that matter to the user.

**Milo's real competitor is not another app. It is not recording at all.**

## 3. Core principles

1. **AI interprets, the backend decides.** The model turns a sentence into structured data. Arithmetic, rules, totals and decisions are always deterministic.
2. **Never invent.** No field is filled by assumption. Every default is shown to the user with an option to change it.
3. **Never lose data.** Recording is never blocked by missing information; what is missing becomes a pending item.
4. **Ask little, and with purpose.** Milo asks only when the answer changes a future answer or when a mistake would be costly. One question at a time.
5. **Reliability over apparent intelligence.** Every number shown comes from the database. Every verdict shows the data it was based on.
6. **Learn explicitly.** Milo learns aliases and patterns, but only turns a pattern into a rule after the user says yes. Everything it learns can be inspected and corrected.
7. **Build the habit.** Milo doesn't wait to be asked; it shows the value of recording every day.
8. **Act only within the user's own records.** Milo records, informs, warns and suggests. It never acts in the world on the user's behalf.
9. **The product is defined by the questions it answers.** Data is collected to answer real questions — not the other way around.

## 4. Target user and usage context

- **Long-term audience:** anyone who wants to organize their practical life — from a salaried person who wants to know where their paycheck goes to someone with a very small income-generating activity (e.g., a manicurist recording services and expenses).
- **First user:** Maycon. Horizon 6–12 months: Maycon, at most family members as testers.
- **Starting point:** the first user currently tracks nothing.
- **Accounts:** one person per account; data strictly isolated between users.
- **Usage modes (anytime):**
  - **Quick capture** — on the move, short message (voice in the future), no conversation required.
  - **Review** — stationary: queries, corrections, resolving pending items.

## 5. Interaction model and expected behavior

### 5.1 Recording

The user sends a message ("filled up 50", "lunch 25", "got 300 for the freight job"). Milo interprets it, **records it immediately** and replies with a summary and an **Undo** option. It does not ask for confirmation before recording.

### 5.2 When Milo may assume

Only when (a) there is a **single possibility** (e.g., only one vehicle registered) or (b) the **user has defined a default**. A pattern observed in history never becomes an assumption on its own: Milo asks once whether it can turn it into a rule. Every assumption is shown with an option to change it ("Fox [change]").

### 5.3 Pending clarification

- An expense with a known amount is **recorded immediately**, even without a category. Status `pending_clarification`; it **counts in totals**, flagged as pending.
- Milo asks **once, immediately**.
- Follow-up happens **inside the daily closing** — never one reminder per item.
- Without an answer, the item becomes `unclassified`, but **only after it has appeared in at least one daily closing**. Items created after the day's closing go into the next day's closing.
- Clarification history is stored as structured data (asked at, reminders sent, closed at, reason). Human-readable notes are generated on display.
- **Recovery at any time:** replying to Milo's question, a direct answer when only one item is open, referencing amount and date ("that 50 from yesterday was the locksmith"), the pending list, or the weekly summary. With several open items, Milo asks which one instead of guessing.
- Reports show **"Uncategorized" as an explicit group**, never as a regular category.
- Every late classification keeps its history.

```
pending_clarification ──(answer)──────────────────────────→ committed
        │
        └──(after ≥1 daily closing, no answer)──→ unclassified ──(late answer)──→ committed
```

### 5.4 Daily closing (20:00, user's timezone)

One message with the day's summary, open pending items, suspected duplicates awaiting confirmation, and a *"forgot anything?"* prompt. It is the central mechanism for habit and for record completeness.

### 5.5 When something looks wrong

**When in doubt, Milo records and flags — it never blocks.**

| Signal | Behavior |
|---|---|
| Outlier amount ("fuel 5000") | Record and ask whether it is correct |
| Suspected duplicate | **Ask before counting it.** Kept as `possible_duplicate`, excluded from totals and shown as "+ R$50 awaiting confirmation". If unanswered: recorded, counted and flagged in the daily closing. This is the only status excluded from totals. |
| Several operations in one message | Record each separately |
| Contradiction with existing data (bill already paid) | Don't record again; point to the existing record |
| No identifiable amount | Record nothing; ask |

### 5.6 Categories

1. First, what Milo has already learned ("comb" = fuel) — no AI call.
2. Otherwise, AI picks **among existing categories** only.
3. If none fits, the record stays pending with a suggestion ("Create *Education*?"). **New categories and new assets only exist after the user's explicit yes.**

### 5.7 Verdicts

For questions such as *"Can I afford a R$2,000 phone?"*, Milo gives a verdict only when backend-defined sufficiency rules confirm there is enough data. Otherwise it gives facts and simulations and states what is missing. Every verdict shows the data it was based on.

### 5.8 Memory and conversational context

| Kind | Example | Lifetime |
|---|---|---|
| **Data** | Recorded expenses, pending items | Permanent |
| **Learned knowledge** | "comb" = fuel; fuel defaults to the Fox | Until the user changes it |
| **Conversational context** | "How much on fuel this month?" → "and last month?" | Expires after **15 minutes** without messages or when the topic changes |

After the context expires, an incomplete follow-up ("and the motorcycle?") makes Milo ask what is meant.

## 6. Responsibilities and limits

### 6.1 Milo does

Record, query, correct, warn, suggest, summarize and remind — always within the user's own data.

### 6.2 Milo does not

- Answer general-knowledge questions, generate content or research products.
- **Act in the world:** pay, transfer money, message third parties or book appointments with other people.
- Delete or alter records on its own initiative.

### 6.3 Autonomy levels

| Level | Description | Status |
|---|---|---|
| 1 | Records and informs | In scope |
| 2 | Warns and suggests | In scope (limit) |
| 3 | Acts on the user's behalf | Out of scope |

Reading external data (bank statements, balances) is **not** acting — it is a level-1 data source. Only moving money or committing the user to third parties is level 3.

Level 3 would be a **declared product change**, not just another capability: it would require explicit confirmation before every action, an action lifecycle with idempotency, stronger authentication than the chat channel, regulated integrations (in Brazil, payment initiation runs through Central Bank–authorized institutions) and identity rules for talking to third parties. The core — interpretation, domain, records, "AI interprets, backend decides" — would remain the same.

### 6.4 Never delegated to AI

| Decision | Owner |
|---|---|
| Any arithmetic: totals, averages, simulations | Backend (SQL) |
| Any number shown to the user | Backend — the LLM may phrase the sentence; numbers always come from the database |
| Which fields are required for a record | Domain rules |
| Whether data is sufficient for a verdict | Deterministic rules |
| When Milo sends a message on its own | Scheduler |
| Deleting or overwriting data | Explicit user command only |
| Filling a field by assumption | Forbidden; defaults only when a rule allows it, always shown |
| Whether something is a duplicate or an outlier | Deterministic rules |

**AI may:** turn the user's message into structured data, understand questions, phrase answers from already-computed facts, and **suggest** classifications.

## 7. Capabilities

### v1

1. Record expenses and income via text.
2. Query totals by period and category.
3. Correct and undo.
4. Pending clarification flow.
5. Daily closing at 20:00.

Out of v1: historical data import (no prior history exists for the first user).

### v2

- Reminders (one-off and recurring, e.g., bills).

### Afterwards, in this order

| # | Capability | Rationale |
|---|---|---|
| 1 | Voice input | Biggest reduction of capture effort on the move. May move up to v2. |
| 2 | Income-generating activities (units by service type) | Required to answer "was my work worth it?" |
| 3 | Weekly summary | Cheap (reuses the daily closing); shows trends |
| 4 | Credit card and bills | Complex (installments, double counting); needs a stable base |
| 5 | Tasks | New domain, little overlap with finances |
| 6 | Notes | Depends on Q10 |
| 7 | Appointments and calendar integration | External integration; builds on v2 reminders |

### Future scope (recorded, not planned)

- Full financial picture: account balances, savings, investments.
- Reconciliation with bank statements and card bills.
- Historical data import for users who already have a tracking habit.

## 8. Real-world examples

**Expense without context**
> User: spent 50
> Milo: Recorded R$50, but I couldn't tell what it was for. Can you explain?
> *(No answer → listed in the 20:00 closing → still no answer → "Uncategorized".)*

**Locksmith**
> User: paid 50 at the locksmith
> Milo: Recorded R$50 for locksmith. Was it for the house, the Fox or the motorcycle?
> User: the motorcycle
> Milo: Done, linked to the motorcycle.

Milo asks because the answer changes a future answer ("how much did the motorcycle cost me this year?").

**Fuel with two vehicles**
> User: filled up 50
> Milo: Recorded R$50 for fuel. Fox or motorcycle?

After several times on the Fox:
> Milo: I noticed fuel is always the Fox. Can I assume that from now on?
> User: yes

From then on: *"Recorded R$50 for fuel on the Fox [change]."*

**Suspected duplicate**
> User: fuel 50 *(10 minutes after an identical one)*
> Milo: Another R$50 for fuel, same as 10 minutes ago. Were there two?

**Question about the user's own life**
> User: can I afford a 2k phone?
> Milo *(sufficient data)*: Yes, paying upfront. Based on: balance of R$3,200 reported on the 20th, average surplus of R$600 over the last 3 months, R$450 in bills until the end of the month.
> Milo *(insufficient data)*: Over the last 3 months you had an average surplus of R$600. Ten installments of R$200 would take 33% of that. I don't know your current balance, so I can't say whether you can pay upfront.

**Out of scope**
> User: what's the best phone under 2k?
> Milo: I don't research products — but I can tell you whether it fits your budget.

**Income-generating activity (future)**
> Manicurist: today I did 10 hands-and-feet and 10 feet only
> Milo records units by service type and derives revenue from registered prices *(rules open: Q7–Q9)*.

**Daily closing**
> **Today:** R$87 across 4 expenses (fuel R$50, lunch R$25, other R$12).
> **Pending:** R$12 without a category (1 p.m.). What was it?
> **Forgot anything?** Just send it.

## 9. Evolution

### 9.1 Capability admission filter

Every new capability must answer all five questions before entering the roadmap:

| # | Question |
|---|---|
| 1 | Is it about the **user's own practical life**, not general knowledge? |
| 2 | Does it stay within level 2 — **no acting in the world**? |
| 3 | Which **real user question** does it make answerable? |
| 4 | Does it respect what is never delegated to AI? |
| 5 | How does it show up in the **daily closing** and the pending flow, instead of as an isolated flow? |

If (1) or (2) is "no", the capability does not enter without a declared product change. Question (5) is what keeps Milo from becoming a flow-based chatbot: new capabilities reuse the existing mechanisms (record, pending, closing, undo) instead of creating their own rigid Q&A flows.

### 9.2 Architectural guarantees required by the product

| Guarantee | Why |
|---|---|
| Shared core: interpretation, records, pending flow, daily closing, learned knowledge | New capabilities plug into it |
| Channels as adapters (Telegram now; WhatsApp and voice later) | Adding or swapping a channel doesn't touch the domain |
| AI model behind an interface | Swap model or rules without touching the rest |
| Every action is an explicit domain command with an audit trail | Enables undo, history and, someday, level 3 |
| **Evaluation set per capability** | No capability goes live without a set of real user messages (starting at 20–30) with the expected interpretation for each. Every prompt or model change re-runs all sets. This is also Milo's evals dataset. |

## 10. Decisions

| ID | Decision |
|---|---|
| D1 | Domains: finances, schedule/reminders, tasks, notes. Not a general-purpose assistant. |
| D2 | Ask only when the missing information changes a future answer or when recording it wrong is costly. |
| D3 | The product is defined by the questions it answers; required fields derive from them. |
| D4 | Single-user accounts with strict per-user isolation. |
| D5 | *(Proposed)* Small income-generating activities in scope: units by service type plus expenses. No inventory, customer records, credit sales, invoices or multiple users. |
| D6 | Capture never blocks and never discards data. |
| D7 | Learning is explicit, inspectable and correctable. |
| D8 | Scope: the user's own practical life. General knowledge, content generation and product research are out. |
| D9 | Verdicts only when deterministic sufficiency rules are met; otherwise facts and simulations. Every verdict shows its basis. |
| D10 | Milo builds the habit proactively. |
| D11 | Autonomy limit: level 2. Never acts in the world on the user's behalf. |
| D12 | Reading external data is not acting. |
| D13 | Decisions never delegated to AI (§6.4). |
| D14 | Category assignment in layers; creating structure requires the user's yes. |
| D15 | Assumptions only from a single possibility or a user-defined default; history patterns need confirmation. |
| D16 | When in doubt, record and flag — never block. |
| D17 | Suspected duplicates: ask before counting; if unanswered, record, count and flag in the daily closing. |
| D18 | Conversational context expires after 15 minutes or on topic change. |
| D19 | Capability admission filter (§9.1). |
| D20 | Evaluation gate per capability (§9.2). |

**Superseded:** the 30-minute `PendingClarification` expiry in `doc/`; the delivery-driver persona; the purpose centered on "is delivery work worth it?"; the earlier phase plan (fuel & deliveries → reminders → voice → calendar → weekly summary → WhatsApp).

## 11. Open questions

| ID | Question | Resolve before |
|---|---|---|
| Q1 | How are shared-asset costs (work and personal use) split? Proposal: `purpose` = work / personal / mixed per record, default per asset, no percentage split. | Income activities |
| Q2 | Does Milo track time worked? How is it captured? | Income activities |
| Q3 | What is the baseline for "was it worth it?" | Income activities |
| Q4 | How to mitigate incomplete records beyond "forgot anything?" | Ongoing |
| Q5 | Does voice input move up to v2? | v2 planning |
| Q7 | Income activities: price per service registered, stated, or both? | Income activities |
| Q8 | Income activities: confirm no customer records. | Income activities |
| Q9 | Can a user have more than one income-generating activity? | Income activities |
| Q10 | Notes: generic, or only linked to known things (assets, expenses, commitments)? | Notes |
| Q12 | Duplicate window and outlier thresholds. | Domain modeling |
| — | Confirm D5. | Income activities |
| — | Is the daily closing time user-configurable in v1? | v1 planning |
