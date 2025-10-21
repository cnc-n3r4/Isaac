# ======================================================
# 📄 DOC: Execution & Logging
# PURPOSE
#   - Route based on classification.
#   - Auto-execute: Tier 1–2 and Direct exec.
#   - Validate: Tier ≥3 (defer to Validation module).
#   - Append chronological logs for EVERY step.
# ======================================================

# ASCII FLOW (ROUTING + LOGGING)
#                        ┌──────────────────────────┐
#                        │ Classification (upstream)│
#                        └───────────┬──────────────┘
#                                    │
#                 ┌──────────────────▼──────────────────┐
#                 │ kind=local → execute local          │
#                 │   → LOG(event=local_exec)           │
#                 └──────────────────┬──────────────────┘
#                                    │
#                      ┌─────────────▼─────────────┐
#                      │ kind=direct → execute now │
#                      │   → LOG(exec_start/result)│
#                      └─────────────┬─────────────┘
#                                    │
#                 ┌──────────────────▼──────────────────┐
#                 │ kind=regular → check tier           │
#                 │   - if tier ≤2 → execute now        │
#                 │       → LOG(exec_start/result)      │
#                 │   - if tier ≥3 → VALIDATION path    │
#                 │       → LOG(event=validation_start) │
#                 └──────────────────┬──────────────────┘
#                                    │
#                          ┌─────────▼─────────┐
#                          │ Defer to          │
#                          │ Validation module │
#                          └───────────────────┘

# LOGGING RULES
#   - Always append (append-only, chronological):
#       • exec_start (command, tier, origin, timestamp)
#       • exec_result (status, summaries, duration)
#       • validation_start / validation_decision (if applicable)
#   - No silent paths; every route yields at least one log.

# CONTRACT (I/O)
# INPUT:
#   - classification (from Module 1)
#   - executor adapter (effectful)
#   - logger adapter (append-only)
# OUTPUT:
#   - execution_result (success/failure + payload)
#   - persisted log entries (time-ordered)

# INVARIANTS
#   - Direct + Tier ≤2 never call validator.
#   - Log schema is stable and versioned (if evolved).
