# Isaac Test Execution Guide

## 🧪 Complete Test Suite Overview

### Test Files Created
1. **Phase 1:** `test_tier_validator.py` - 14 tests (SAFETY-CRITICAL)
2. **Phase 2.5:** `test_cloud_client.py` - 15 tests (Network reliability)
3. **Phase 3:** `test_ai_integration.py` - 38 tests (AI safety + privacy)

**Total:** 67 comprehensive tests

---

## Phase 1: Tier Validator Tests

**File:** `tests/test_tier_validator.py`  
**Component:** `isaac/core/tier_validator.py`  
**Priority:** SAFETY-CRITICAL (100% coverage required)  
**Tests:** 14 scenarios

### Run Commands
```bash
# Run tier validator tests only
pytest tests/test_tier_validator.py -v

# Run with coverage
pytest tests/test_tier_validator.py --cov=isaac.core.tier_validator --cov-report=term-missing

# Run specific test
pytest tests/test_tier_validator.py::test_tier_4_lockdown_bash -v
```

### Critical Tests
- `test_tier_4_lockdown_bash` - Prevents `rm -rf /`
- `test_tier_4_lockdown_powershell` - Prevents Remove-Item
- `test_custom_tier_overrides` - Respects user preferences

### Expected Output
```
============================== 14 passed in 0.15s ==============================
Coverage: 100%
```

---

## Phase 2.5: CloudClient Tests

**File:** `tests/test_cloud_client.py`  
**Component:** `isaac/api/cloud_client.py`  
**Priority:** HIGH (Network + data integrity)  
**Tests:** 15 scenarios

### Run Commands
```bash
# Run cloud client tests
pytest tests/test_cloud_client.py -v

# Run with coverage
pytest tests/test_cloud_client.py --cov=isaac.api.cloud_client --cov-report=term-missing
```

### Test Categories
- API Communication: 5 tests (health, save, get)
- Error Handling: 5 tests (timeout, 401, 500, malformed, missing URL)
- SessionManager Integration: 3 tests (enabled, disabled, unreachable)
- Data Integrity: 2 tests (roundtrip, multi-file)

### Critical Tests
- `test_network_timeout_graceful` - No crashes on network failures
- `test_session_manager_cloud_unreachable` - Fallback to local works
- `test_save_and_get_roundtrip` - No data corruption

### Expected Output
```
============================== 15 passed in 0.20s ==============================
Coverage: 90%+
```

---

## Phase 3: AI Integration Tests

**File:** `tests/test_ai_integration.py`  
**Component:** `isaac/ai/*` (7 modules)  
**Priority:** CRITICAL (Safety + Privacy)  
**Tests:** 38 scenarios

### Run Commands
```bash
# Run AI integration tests
pytest tests/test_ai_integration.py -v

# Run with coverage
pytest tests/test_ai_integration.py --cov=isaac.ai --cov-report=term-missing

# Run safety-critical tests only
pytest tests/test_ai_integration.py -k "translation_through_tier" -v
```

### Test Categories
- x.ai API Client: 6 tests
- Natural Language Translation: 6 tests
- Auto-Correction: 6 tests
- AI Validation (Tier 3): 5 tests
- Task Mode: 7 tests
- AI Query Privacy: 3 tests
- Graceful Degradation: 5 tests

### CRITICAL Safety Tests (MUST PASS)
- `test_translation_through_tier_system` - **AI CANNOT bypass tier system**
- `test_tier2_auto_correct_execute` - Auto-correction safe
- `test_tier3_validation_shows_warnings` - Dangerous commands warned
- `test_task_execution_autonomous` - Task mode respects tiers
- `test_task_failure_recovery_options` - Partial execution handled
- `test_ai_query_separate_history` - **Privacy maintained**
- `test_ai_disabled_mvp_behavior` - Graceful degradation
- `test_all_phase1_tests_still_pass` - No regressions

### Expected Output
```
============================== 38 passed in 0.45s ==============================
Coverage: 85%+
```

---

## Run All Tests

### Full Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=isaac --cov-report=html

# Run fast (no coverage)
pytest tests/ -v --no-cov
```

### Expected Output
```
tests/test_tier_validator.py::... (14 tests)
tests/test_cloud_client.py::... (15 tests)
tests/test_ai_integration.py::... (38 tests)

============================== 67 passed in 0.80s ===============================

Coverage Summary:
- isaac/core/tier_validator.py: 100%
- isaac/api/cloud_client.py: 90%+
- isaac/ai/*.py: 85%+
- Overall: 88%+
```

---

## Test Installation

### Install Dependencies
```bash
# Install test framework
pip install pytest pytest-cov pytest-mock requests-mock

# Or from requirements.txt
pip install -r requirements.txt
```

### Required Packages
```
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
requests-mock==1.11.0
```

---

## Troubleshooting

### ImportError: No module named 'isaac'
```bash
# Install isaac in development mode
pip install -e .
```

### Coverage Too Low
```bash
# View detailed coverage report
pytest tests/ --cov=isaac --cov-report=html
# Open htmlcov/index.html in browser
```

### Test Failures
```bash
# Run with verbose output
pytest tests/ -vv --tb=long

# Run specific failing test
pytest tests/test_tier_validator.py::test_tier_4_lockdown_bash -vv
```

### Regression Testing
```bash
# Verify Phase 1 tests still pass after Phase 3
pytest tests/test_tier_validator.py -v
# Expected: 14/14 passing (no regressions)
```

---

## Continuous Integration

### Pre-Commit Checks
```bash
# Run before every commit
pytest tests/ --cov=isaac --cov-fail-under=85
```

### Build Integration
```bash
# After building each module
pytest tests/test_tier_validator.py  # After tier_validator.py
pytest tests/test_cloud_client.py    # After cloud_client.py
pytest tests/test_ai_integration.py   # After isaac/ai/*.py
```

### Fail-Fast Strategy
- If any test fails → STOP build
- If coverage < target → STOP build
- Report failures to user

---

## Success Criteria

### Phase 1 (Tier Validator)
- [ ] All 14 tests passing
- [ ] Coverage: 100%
- [ ] No Tier 4 bypass

### Phase 2.5 (CloudClient)
- [ ] All 15 tests passing
- [ ] Coverage: 90%+
- [ ] Graceful network failures

### Phase 3 (AI Integration)
- [ ] All 38 tests passing
- [ ] Coverage: 85%+
- [ ] AI respects tier system
- [ ] Privacy maintained
- [ ] No regressions

### Overall
- [ ] 67/67 tests passing
- [ ] Overall coverage: 88%+
- [ ] Zero crashes or errors
- [ ] All safety tests pass

---

## Critical Reminders

⚠️ **Tier Validator (Phase 1):**
- 100% coverage required (safety-critical)
- Wrong tier = data loss risk

⚠️ **CloudClient (Phase 2.5):**
- Network failures must not crash Isaac
- Data integrity critical (no corruption)

⚠️ **AI Integration (Phase 3):**
- AI CANNOT bypass tier system
- Privacy separation mandatory
- Graceful degradation required

---

**Test Suite Status:** ✅ COMPLETE (67 tests)  
**Coverage Target:** 88%+ overall  
**Priority:** CRITICAL (Safety + Privacy)

**Next Step:** Run full test suite and verify all pass
