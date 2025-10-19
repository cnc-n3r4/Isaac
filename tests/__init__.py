# tests/__init__.py
"""
Isaac Test Suite

Comprehensive pytest tests for Isaac multi-platform shell assistant.

Test Modules:
- test_tier_validator.py - Tier classification (SAFETY-CRITICAL)
- test_cloud_client.py - Cloud sync API (MAIN FEATURE)
- test_integration.py - End-to-end workflows
- test_shell_adapters.py - Cross-platform execution
- test_session_manager.py - Session sync logic
- test_command_router.py - Routing decisions
- test_api_endpoints.py - PHP API validation

Run all tests:
    pytest tests/

Run specific test file:
    pytest tests/test_tier_validator.py

Run with coverage:
    pytest tests/ --cov=isaac --cov-report=html
"""
