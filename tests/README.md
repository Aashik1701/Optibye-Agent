# EMS Agent Tests

This directory contains the test suite for the EMS Agent project.

## Test Structure

- `unit/` - Unit tests for individual components
- `integration/` - Integration tests for services
- `e2e/` - End-to-end tests (to be added)

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run unit tests only
python -m pytest tests/unit/

# Run integration tests only
python -m pytest tests/integration/

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Test Configuration

Tests use pytest with the following plugins:
- pytest-asyncio for async test support
- pytest-cov for coverage reporting
- pytest-mock for mocking capabilities

## Environment Setup

Before running tests, ensure:
1. MongoDB test database is available
2. Redis is running (for integration tests)
3. Environment variables are set in `.env` file
