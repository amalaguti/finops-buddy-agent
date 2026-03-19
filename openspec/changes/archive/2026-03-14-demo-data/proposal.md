## Why

When demonstrating FinOps Buddy to potential users or in portfolio presentations, real AWS account names, profile names, and account IDs are exposed in the UI and chat responses. This leaks sensitive organizational information. A demo mode is needed to mask real identifiers with fake/placeholder names while preserving the application's functionality for demonstration purposes.

## What Changes

- Add a `/demo` URL path that enables demo mode for the web UI
- When demo mode is active, mask all account names, profile names, and account IDs in:
  - Profile selector dropdown
  - Account context panel
  - Costs panel
  - Chat responses from the agent
- Apply a configurable mapping: `payer-profile` → `Master_Account`, other accounts get generated fake names (e.g., `Account_001`, `Account_002`)
- Account IDs are replaced with fake 12-digit IDs (e.g., `123456789012`)
- Demo mode is UI-only visualization masking; underlying API calls use real credentials

## Capabilities

### New Capabilities

- `demo-mode`: Demo mode for masking sensitive account/profile information in UI and chat responses for presentation purposes

### Modified Capabilities

- `backend-api`: Adding demo mode flag propagation and response masking middleware
- `hosted-web-ui`: Adding `/demo` route and client-side masking in UI components

## Impact

- **Frontend**: New `/demo` route, masking logic in profile selector, context panel, costs panel
- **Backend API**: Response transformation middleware to mask identifiers when demo mode header is present
- **Chat agent**: System prompt modification to instruct agent to use masked names in responses
- **Settings**: New `demo.account_mapping` configuration for custom name mappings
- **No AWS API changes**: Real credentials still used; masking is display-only
