# Conversation flow

How milo turns one incoming message into a reply. The LLM interprets; the backend decides.

```mermaid
flowchart TD
    A([Message received]) --> B{Duplicate?<br/>update_id already seen}
    B -- yes --> Z1([Ignore])
    B -- no --> C[Persist raw message<br/>immutable]
    C --> D{Open pending<br/>clarification?}

    D -- yes --> E{Expired?}
    E -- yes --> E1[Mark pending EXPIRED<br/>draft CANCELLED] --> F
    E -- no --> G{Answers the<br/>pending question?<br/>reply_to or resolver}
    G -- yes --> H[Fill pending field<br/>provenance = USER_STATED]
    H --> M
    G -- no --> F

    D -- no --> F[LLM interpretation<br/>structured output]
    F --> V{Pydantic valid?}
    V -- no --> V1[Retry once] --> V2{Valid?}
    V2 -- no --> U
    V2 -- yes --> I
    V -- yes --> I{Intent}

    I -- unknown --> U[Ask user to rephrase]
    I -- query --> Q[Run read-only query<br/>SQL computes totals] --> R1([Reply with answer])
    I -- correct / undo --> K[Load last committed<br/>operation] --> K1[Apply change<br/>keep audit trail] --> R2([Reply with new summary])
    I -- record --> L[Domain engine<br/>derive category<br/>apply user defaults]
    L --> M{Required fields<br/>missing?<br/>computed by backend}
    M -- yes --> N[Save DRAFT operation<br/>+ pending clarification<br/>with expires_at] --> R3([Ask ONE question])
    M -- no --> O[Commit operation<br/>status COMMITTED] --> R4([Reply summary<br/>with Undo button])

    classDef llm fill:#fdf2e9,stroke:#e67e22,color:#000
    classDef state fill:#eaf2f8,stroke:#2e86c1,color:#000
    classDef reply fill:#e9f7ef,stroke:#27ae60,color:#000
    class F,V1 llm
    class C,E1,N,O,K1 state
    class R1,R2,R3,R4,U reply
```

To edit in draw.io: Arrange → Insert → Advanced → Mermaid, then paste the block above.

## Intents

Domain-level intents (what the user wants), not CRUD verbs.

| Intent | Example | Writes? |
|---|---|---|
| `record_expense` | "combustivel entregas 30" | yes |
| `record_income` | "recebi 200 do frete" | yes |
| `record_deliveries` | "entregas realizadas 160" | yes |
| `create_reminder` | "me lembra de pagar o cartão dia 10" | yes |
| `query` | "quanto gastei de combustível esse mês?" | no |
| `correct_last` | "não, foi 130" | yes |
| `undo_last` | "apaga o último" | yes |
| `unknown` | anything else | no |

Answering a pending question is **not** an intent: it is resolved by routing (pending state) before interpretation.

## Entities

| Entity | Key fields | Notes |
|---|---|---|
| `Message` | id, user_id, channel, external_id, text, received_at | Immutable. `external_id` = Telegram update_id (dedup). |
| `Interpretation` | id, message_id, payload (JSONB), model, prompt_version, created_at | Raw LLM output, kept for evals. |
| `Operation` | id, user_id, kind, status, source_message_id, created_at | Status: `draft` → `committed` / `cancelled`. |
| `Transaction` | operation_id, type, amount (Decimal), description, category_id, asset_id?, purpose, tags[], occurred_at | `description` keeps the user's words ("chaveiro"). |
| `DeliveryRecord` | operation_id, quantity, amount?, occurred_at | |
| `Reminder` | operation_id, title, due_at, recurrence?, amount? | Fired by scheduler, not by the LLM. |
| `Category` | id, user_id?, parent_id?, name, slug | Data, not enum. `user_id` null = system default. Max 2 levels. |
| `Asset` | id, user_id, kind (vehicle/home), name, is_default | "Fox", "Yes 125", "Casa". |
| `PendingClarification` | id, conversation_id, operation_id, field, prompt_message_id, status, expires_at | One open per conversation (v1). |
| `FieldProvenance` | operation_id, field, source | `user_stated` / `user_confirmed` / `default` / `derived`. |

## Closed enums (code)

- `TransactionType`: expense, income
- `Purpose`: work, personal (drives delivery-profit reports)
- `OperationStatus`: draft, committed, cancelled
- `ProvenanceSource`: user_stated, user_confirmed, default, derived

## Business rules

1. **No invention.** A required field is filled only by the user, an explicit user default, or a deterministic derivation. Never by an LLM guess.
2. **Backend computes missing fields.** Required fields are defined per operation kind in code; the LLM never reports `missing_fields`.
3. **Ask one question at a time**, and only for required fields.
4. **Asset is required only when ambiguous**: if the user has one asset of the relevant kind, use it (`derived`); if a default exists, use it and show it with a change button (`default`).
5. **Category can depend on asset** (chaveiro + casa → Residencial > Manutenção; chaveiro + carro → Transporte > Manutenção de veículo). Derived by rule, not by the LLM.
6. **Money is `Decimal`**, never float.
7. **Totals come from SQL**, never from the LLM.
8. **Pending clarifications expire** (default 30 min); expired drafts are cancelled, not committed.
9. **A reply to the bot's question (Telegram `reply_to_message_id`) always targets that pending clarification.**
10. **A new, unrelated message while a question is pending** is processed as new; the pending stays open until it expires.
11. **Corrections never overwrite silently**: the change is recorded with its source message.
12. **Duplicates are ignored** by `(channel, external_id)` unique constraint.
