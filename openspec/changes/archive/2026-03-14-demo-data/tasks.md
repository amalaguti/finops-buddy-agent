## 1. Backend Settings

- [x] 1.1 Add `demo.account_mapping` and `demo.account_id_mapping` configuration support in `settings.py`
- [x] 1.2 Add `get_demo_account_mapping()` and `get_demo_account_id_mapping()` functions
- [x] 1.3 Update `config/settings.yaml` template with demo configuration section

## 2. Backend Demo Masking

- [x] 2.1 Create `src/finops_buddy/api/demo.py` module with masking utility functions
- [x] 2.2 Implement `mask_account_name(name: str, mapping: dict) -> str` function
- [x] 2.3 Implement `mask_account_id(account_id: str, mapping: dict) -> str` function
- [x] 2.4 Implement `mask_response_data(data: dict, name_mapping: dict, id_mapping: dict) -> dict` function

## 3. Backend Middleware

- [x] 3.1 Add demo mode middleware to `app.py` that detects `X-Demo-Mode: true` header
- [x] 3.2 Apply response transformation for `/profiles` endpoint when demo mode active
- [x] 3.3 Apply response transformation for `/context` endpoint when demo mode active
- [x] 3.4 Apply response transformation for `/costs` endpoint when demo mode active

## 4. Chat Agent Demo Mode

- [x] 4.1 Modify `build_agent_and_tools()` in `chat.py` to accept demo mode flag
- [x] 4.2 Append demo masking instructions to agent system prompt when demo mode active
- [x] 4.3 Pass demo mode flag from `/chat` endpoint based on `X-Demo-Mode` header

## 5. Frontend Demo Route

- [x] 5.1 Add `/demo` route to React router that sets demo mode context
- [x] 5.2 Create `DemoModeContext` provider to track demo mode state
- [x] 5.3 Update API client to include `X-Demo-Mode: true` header when demo mode active

## 6. Frontend UI Updates

- [x] 6.1 Add "DEMO" badge component to header when demo mode is active
- [x] 6.2 Ensure profile selector displays masked names from API response
- [x] 6.3 Ensure context panel displays masked account info from API response
- [x] 6.4 Ensure costs panel displays masked data from API response

## 7. Quality Checks

- [x] 7.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues
- [x] 7.2 Run `poetry run bandit -c pyproject.toml -r src/`; fix any findings
- [x] 7.3 Add pytest tests for demo masking functions in `tests/test_demo.py`
- [x] 7.4 Add pytest tests for demo middleware behavior
- [x] 7.5 Run `poetry run pip-audit`; address any vulnerabilities

## 8. Documentation

- [x] 8.1 Update README.md with demo mode documentation (how to access, configuration)
- [x] 8.2 Add `demo.account_mapping` section to Configuration documentation
