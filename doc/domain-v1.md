# Milo — v1 Domain Model

Domain modeling decisions for v1, derived from [`PRODUCT.md`](PRODUCT.md).
All decisions below were confirmed by Maycon (2026-11-25).

---

## M1. v1 intents

| Intent | Status | Notes |
|---|---|---|
| `record_expense` | Keep | v1 |
| `record_income` | Keep | v1. Delivery earnings ("got 300 from deliveries") are plain income until income activities exist. |
| `query` | Keep | v1 |
| `correct_last` | Keep | v1 |
| `undo_last` | Keep | v1 |
| `unknown` | Keep | Milo did not understand the message. |
| `record_deliveries` | **Removed** | Belongs to income activities (open: Q1–Q3, Q7–Q9 in `PRODUCT.md`). |
| `create_reminder` | **Recognized but unsupported** | Reply "I don't do reminders yet". These messages also seed the v2 eval set. |
| `out_of_scope` | **New** | Understood, but not Milo's job (D8). Different reply from `unknown`. |
| `small_talk` | **New** | Greetings and thanks: greeting → natural reply; thanks → emoji. |

Answering a pending item is **not** an intent: it is resolved by routing before interpretation.

`writes` is false for `query`, `unknown`, `out_of_scope`, `small_talk` and `create_reminder` (v1).

## M2. Interpreter contract

Replaces the `Classifier` port. The LLM returns a Pydantic-validated `Interpretation`:

```
Interpretation
├── intent
├── operations[]          one item per operation ("50 gas and 25 lunch" → 2 items)
│   ├── type              expense | income
│   ├── amount            raw text as written ("50", "30,50", "cinquentinha")
│   ├── description       the user's own words ("chaveiro")
│   ├── category_slug?    only among existing categories sent in the prompt; or empty
│   ├── asset_name?       only among existing assets; or empty
│   └── date_expression?  literal text ("ontem", "sexta", "dia 10"); or empty
├── query?                period, category, asset as structured data — never SQL
└── correction?           field and new value
```

**Deliberately excluded (D13):** missing fields (backend computes), model confidence, totals or any arithmetic.

**Deterministic parsers in the backend:**
- **Amount:** raw text → `Decimal` ("cinquentinha" → 50.00, "30,50" → 30.50). Unrecognized → the item becomes pending.
- **Dates:** the LLM only extracts the expression; a deterministic parser resolves it in `America/Sao_Paulo` (hoje, ontem, anteontem, dia N, weekday, semana passada…). Unrecognized → date pending, Milo asks. No date in the message → message `received_at` (provenance `derived`).

Rationale: date arithmetic by the model is forbidden by D13 and error-prone (month boundaries, timezone); the vocabulary of dates in expense messages is small enough for a parser.

## M3. Operation lifecycle, invariants, undo/correct

### Lifecycle

```
                 ┌──────────────→ committed ←───────────────┐
   (record) ─────┼──→ pending_clarification ──(answer)──────┤
                 │          │                                │
                 │          └─(after ≥1 closing)──→ unclassified ──(late answer)
                 │
                 └──→ possible_duplicate ──("two of them" or closing without answer, flagged)──→ committed
                            └──("same one")──→ cancelled

   any state ──(undo)──→ cancelled   (terminal, except Redo within its 15-min window — M4)
```

### Invariants

1. Every operation has an amount > 0. Without an amount, no operation exists (D16).
2. Totals include everything **except** `possible_duplicate` and `cancelled`.
3. Nothing is hard-deleted. Undo sets `cancelled` and keeps the record for audit (and enables "Redo").
4. Every transition records its source: the causing message, or the scheduler.
5. A correction keeps the status and stores history: old value, new value, source message.

### Undo / correct targeting (hybrid confirmation)

| How the user asked | Behavior |
|---|---|
| Tapped the **Undo** button, or replied directly to the specific message | Act immediately; offer **[Redo]** (undo) |
| Text without pointing to a message ("delete the last one", "delete the lunch") | **Confirm first**, showing exactly what will change, with **[Yes] [No]** buttons |
| Affects more than one operation ("delete all") | **Always confirm**, listing the items |
| No answer to a confirmation | Nothing happens (safe default; no data lost) |

- Without a reply target, "the last one" means the **last single operation recorded**, regardless of time — never all operations from the last message.
- The same rule applies to **corrections**: an inferred target requires confirmation ("Change lunch from R$25 to R$35? [Yes] [No]").
- Confirmations use inline buttons, not typed yes/no.

## M4. Action buttons expire; no restore in v1

- **Confirmation buttons ([Yes]/[No]) and [Redo] are valid for 15 minutes** — the same window as conversational context (D18).
- After that, tapping does nothing and Milo replies: "This confirmation has expired. If you still want to do it, ask me again."
- This does not contradict "pending items never expire": a pending item is **data** (must never be lost); a confirmation is a **momentary intent** (not yet authorized). Expiring it loses nothing.
- **No `restore` intent in v1.** After the Redo window, the user simply records the operation again. The cancelled record stays stored for audit. `restore` can be added later through the admission filter (D19) if real usage shows the need.

## M5. Numeric rules

### Suspected duplicate

Two operations are suspected duplicates when they share: **same user, same type (expense/income), same amount, same category** — and **same asset when the asset is known** — and were recorded **less than 30 minutes apart**.

- Including the asset avoids false positives such as fueling the Fox and the motorcycle back to back (R$50 each).
- 30 minutes catches resends and accidental repeats without flagging legitimate repeated spending later in the day.

### Outlier amount

- **With history** (≥ 5 operations in that category in the last 90 days): outlier when amount **> 5 × the category median**.
- **Without history:** outlier when amount **≥ R$1,000** (catches "5000" typed for "50,00").
- An outlier is **recorded normally** and flagged ("Correct? [Fix]") — D16. False positives cost one unnecessary question.

All thresholds are configuration values, not hard-coded literals, so they can be tuned from real usage.

## M6. Initial structure

### Assets — created on demand

- No onboarding questionnaire. The first contact already delivers value ("recorded").
- When the user mentions something Milo doesn't know as an asset, Milo records the operation and offers to register it (D14):
  > User: changed the motorcycle oil, 80
  > Milo: Recorded R$80 for vehicle maintenance. I don't know "motorcycle". Register it as one of your vehicles? **[Yes] [No]**
- "No" keeps the operation recorded, just not linked to an asset.
- Users without vehicles never see vehicle questions.

### Default categories (system-wide, `user_id` null; max 2 levels)

Slugs in English (code); display names in pt-BR.

**Expenses**

| Parent (slug — display) | Children (slug — display) |
|---|---|
| `food` — Alimentação | `groceries` — Mercado · `eating_out` — Restaurante e lanche |
| `transport` — Transporte | `fuel` — Combustível · `vehicle_maintenance` — Manutenção de veículo · `parking_tolls` — Estacionamento e pedágio · `transit_rides` — Transporte público e app |
| `housing` — Moradia | `rent` — Aluguel · `utilities` — Contas da casa · `home_maintenance` — Manutenção da casa |
| `health` — Saúde | `pharmacy` — Farmácia · `appointments` — Consultas e exames |
| `education` — Educação | — |
| `leisure` — Lazer | — |
| `shopping` — Compras | — |
| `subscriptions_services` — Assinaturas e serviços | — |
| `taxes_fees` — Impostos e taxas | — |

**Income**

| Slug — display | Notes |
|---|---|
| `salary` — Salário | |
| `self_employment` — Trabalho autônomo | Delivery earnings go here until income activities exist |
| `sales` — Vendas | |
| `refunds_transfers` — Reembolsos e transferências recebidas | |

**No "Other" category, by design.** Anything that fits nowhere goes to **"Uncategorized"**, which is explicit in reports and followed up in the daily closing. An "Other" bucket would hide exactly what the pending flow is meant to surface.

## M7. Daily closing

- **Content:** day's summary (total and breakdown), open pending items, suspected duplicates awaiting confirmation, and "forgot anything?".
- **Time:** 20:00 in the user's timezone (configurability in v1 still open).
- **Days without records — back-off:**
  - Send a short nudge ("No records today. Any expenses?").
  - After **3 consecutive days without any user message**, stop sending until the user writes again. The first new message restores normal behavior.
  - A day **with open pending items or suspected duplicates always gets the closing**, even during the back-off.
- **Side effects run by the closing:** pending items that already appeared in a previous closing move to `unclassified`; unanswered suspected duplicates move to `committed` + flagged (M3).
- **Idempotency:** the closing is recorded per user per date; a restart never sends it twice.

## M8. Persistence (Postgres)

### Tables

| Table | Holds | Source |
|---|---|---|
| `users` | User, timezone, closing time | D4 |
| `messages` | Every incoming message; immutable; unique `(channel, external_id)` | Existing domain |
| `interpretations` | Raw LLM output, model, prompt version | Evals dataset (D20) |
| `operations` | Each expense or income with its **current** state | M3 |
| `operation_events` | Append-only history of everything that happened to each operation | Invariants 4 and 5 |
| `pending_clarifications` | Pending items and their structured history | `PRODUCT.md` §5.3 |
| `confirmations` | [Yes]/[No] and [Redo] buttons, 15-min validity | M4 |
| `categories` | System defaults and user-created categories | M6 |
| `assets` | The user's assets | M6 |
| `learned_rules` | Aliases ("comb" → fuel) and user-confirmed defaults ("fuel → Fox") | D7, D14, D15 |
| `daily_closings` | Closing sent per user per date | M7 |

### Conventions

- Money: `numeric(12,2)`, never `float`.
- Timestamps: `timestamptz` everywhere.
- No hard deletes.

### History model — current state + event log (option A)

- `operations` holds the current state (amount, category, asset, status), so totals are a plain `SELECT`.
- Every change also appends a row to `operation_events` (e.g., "amount changed from 25 to 35, by message 812"; "status pending_clarification → unclassified, by scheduler").
- Pure event sourcing (state rebuilt from events) was rejected: it solves problems Milo doesn't have (rebuilding past states, multiple projections) at a much higher complexity cost.
