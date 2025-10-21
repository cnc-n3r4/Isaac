# ======================================================
# 📄 DOC: User Confirmation
# PURPOSE
#   Handle confirmable outcomes from Validation (Tier ≥3).
#   Capture explicit Yes/No, log the decision, and proceed.
# ======================================================

# ASCII FLOW (CONFIRMATION STATE)
# ┌──────────────────────────────┐
# │ Validation Decision (upstream│
# │  SAFE | NEEDS_CONFIRM | DENY │
# └───────────────┬──────────────┘
#                 │
#    SAFE ────────┼──► Execute → LOG(exec_start/result) → Done
#                 │
#    DENY ────────┼──► LOG(deny_reason) → Done
#                 │
# NEEDS_CONFIRM ──▼
#     ┌──────────────────────────────────────┐
#     │ Prompt user (Yes/No)                 │
#     └───────────┬───────────────┬─────────┘
#                 │Yes            │No
#                 ▼               ▼
#         Execute command     Cancel operation
#         → LOG(exec_*)       → LOG(cancel_reason)
#                 ▼               ▼
#                Done            Done

# CONTRACT (I/O)
# INPUT:
#   - validation_decision:
#       status: SAFE | NEEDS_CONFIRM | DENY
#       rationale: string
#       suggested_remediations?: []
#   - user_response interface
#   - executor + logger

# OUTPUT:
#   - final outcome: executed | canceled | denied
#   - logs:
#       • validation_decision
#       • user_confirmation (choice + timestamp)
#       • exec_* or cancel_reason

# INVARIANTS
#   - Never execute on NEEDS_CONFIRM without explicit Yes.
#   - Persist the user’s choice before acting.
#   - Present a concise risk summary and preview of the command.
