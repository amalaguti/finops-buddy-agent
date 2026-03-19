## Context

The web UI displays real AWS account names, profile names, and account IDs throughout the interface:
- Profile selector dropdown
- Account context panel (showing current account info)
- Costs panel (showing costs by account)
- Chat responses (agent mentions account names when discussing costs)

For demos and portfolio presentations, these real identifiers should be masked with fake names while the application continues to function normally with real AWS credentials.

## Goals / Non-Goals

**Goals:**
- Enable demo mode via `/demo` URL path
- Mask account names, profile names, and account IDs in UI components
- Mask identifiers in chat agent responses
- Support configurable name mappings (e.g., `payer-profile` → `Master_Account`)
- Keep demo mode as a thin visualization layer; real AWS operations unchanged

**Non-Goals:**
- CLI demo mode (web UI only for now)
- Masking in exported files (PDF, Excel) — can be added later
- Persisting demo mode across sessions (URL-based activation only)
- Masking AWS service names or cost amounts (only account/profile identifiers)

## Decisions

### Decision 1: Activation via URL path `/demo`

**Choice**: Demo mode is activated by navigating to `/demo` instead of `/`

**Rationale**: 
- Simple, shareable URL for demos
- No need for login/session management
- Easy to switch between demo and real mode
- URL clearly indicates demo context

**Alternatives considered**:
- Query parameter (`/?demo=true`): Less clean URLs, could be accidentally shared
- Environment variable: Requires restart, can't switch easily
- UI toggle: Could be accidentally clicked during real usage

### Decision 2: Backend masking middleware

**Choice**: Add a response transformation middleware that masks identifiers when `X-Demo-Mode: true` header is present

**Rationale**:
- Centralized masking logic in one place
- Frontend just sets a header; doesn't need to know masking rules
- Works for all API responses consistently
- Can be extended to mask additional fields later

**Implementation**:
```python
@app.middleware("http")
async def demo_mode_middleware(request: Request, call_next):
    response = await call_next(request)
    if request.headers.get("X-Demo-Mode") == "true":
        # Transform response body to mask identifiers
        ...
    return response
```

**Alternatives considered**:
- Frontend-only masking: Would miss chat responses from agent
- Per-endpoint masking: Duplicated logic, easy to miss endpoints

### Decision 3: Account mapping configuration

**Choice**: Store mapping in settings YAML under `demo.account_mapping`

```yaml
demo:
  account_mapping:
    payer-profile: Master_Account
    # Other accounts get auto-generated names: Account_001, Account_002, etc.
  account_id_mapping:
    "123456789012": "000000000001"
    # Other IDs get auto-generated: 000000000002, etc.
```

**Rationale**:
- Explicit control over important account names (master account)
- Auto-generation for other accounts keeps config minimal
- Consistent with existing settings pattern

### Decision 4: Chat agent masking via system prompt

**Choice**: When demo mode is active, append to the agent's system prompt:

```
DEMO MODE ACTIVE: Replace all AWS account names and IDs in your responses with these mappings:
- "payer-profile" → "Master_Account"  
- Account IDs should be shown as "***" or "000000000001"
- Other account names should use generic names like "Production", "Staging", "Development"
```

**Rationale**:
- Agent naturally incorporates masking into its responses
- No post-processing of agent output needed
- Agent can choose contextually appropriate fake names

**Alternatives considered**:
- Post-process agent responses: Complex regex, might break formatting
- Separate agent instance for demo: Overhead, harder to maintain

### Decision 5: Frontend state management

**Choice**: Detect `/demo` route and set `demoMode: true` in React context, propagate to all API calls via header

**Implementation**:
```typescript
// In App.tsx or router
const isDemoMode = window.location.pathname.startsWith('/demo');

// In API client
const headers = isDemoMode ? { 'X-Demo-Mode': 'true' } : {};
```

**Rationale**:
- Single source of truth from URL
- All components can check context for demo mode
- API client automatically includes header

## Risks / Trade-offs

**[Risk] Agent may not consistently mask names** → Mitigation: Strong system prompt instructions; accept some leakage as the agent is instructed, not deterministic. Could add post-processing as fallback.

**[Risk] New accounts appear without mapping** → Mitigation: Auto-generate fake names for unmapped accounts (`Account_001`, etc.). Only explicitly named accounts (like master) need manual mapping.

**[Risk] Masking breaks functionality** → Mitigation: Masking is display-only; underlying API calls use real data. Functionally equivalent to normal mode.

**[Trade-off] Demo mode in URL vs hidden**: Chose visible `/demo` path for transparency and easy sharing, even though it's less "magic".

**[Trade-off] Backend vs frontend masking**: Chose backend to catch all responses including streaming chat, at the cost of slightly more complexity.

## Open Questions

1. Should demo mode mask cost amounts as well, or just identifiers?
   - Current decision: Only identifiers; costs add to the demo value
   
2. Should the UI show a visual indicator that demo mode is active?
   - Suggestion: Yes, a small "DEMO" badge in the header to avoid confusion
