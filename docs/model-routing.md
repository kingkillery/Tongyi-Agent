# Model Routing Between Paid and Free Tongyi

## Overview
Tongyi Agent automatically alternates between the paid DeepResearch model and the free tier to balance capability and cost.

## Configuration
- `TONGYI_MODEL_NAME`: Primary paid model (default: `alibaba/tongyi-deepresearch-30b-a3b`)
- `TONGYI_FREE_MODEL_NAME`: Free tier model (default: `alibaba/tongyi-deepresearch-30b-a3b:free`)
- `TONGYI_FREE_CALL_INTERVAL`: Use free model every Nth call (default: `3`)

## Behavior
- Calls 1,2: Use paid model
- Call 3: Use free model
- Calls 4,5: Use paid model
- Call 6: Use free model
- ...and so on

## Where It Applies
- `TongyiOrchestrator.run()` – main reasoning loop
- `VerifierGate._validate_with_tongyi()` – claim verification
- `LocalOrchestrator` – legacy delegate handlers (if used)

## Customization
Override via environment variables:
```bash
TONGYI_FREE_CALL_INTERVAL=5  # Use free tier every 5th call
TONGYI_FREE_MODEL_NAME=custom/free-model
```

## Testing
The ModelRouter is fully unit-tested to guarantee correct alternation and edge-case handling.
