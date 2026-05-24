# Authority Leakage Rules

## Purpose

Authority leakage happens when inspection material starts to behave like permission.

The system must keep authority narrow and explicit.

## Sources Of Review Authority

Only these records may participate in review authority:

- `ReviewItem`
- append-only `ApprovalDecision`

Neither is enough alone for future execution.

## Non-Authority Records

These must not become approval or action authority:

- `EvaluationReport`
- `GenerationOutputEvaluation`
- `SignalScore`
- `GenerationRequest`
- `GenerationOutput`
- `ConstraintBundle`
- `PromptSection`
- `DraftPackage`
- `ExportPackage`
- `ReviewSnapshot`
- `EvaluationSnapshot`
- `AssetManifest`

## Required Boundary Flags

Inspection outputs must preserve the relevant negative-control flags:

- `reviewRequired: true`
- `approvalAuthority: false`
- `publishAuthority: false`
- `humanCommitRequired: true`
- `automationAllowed: false`
- `externalDelivery: false`
- `distributionAuthority: false`
- `usableWithoutReview: false`, where applicable

## Invalid Inferences

Invalid:

- evaluator PASS means approval
- high score means truth
- no findings means usable
- export package means public permission
- review snapshot means approved
- review status alone means action permission
- stored evaluation means current evaluator truth

## Required Future Gate

Any future action-capable workflow must require a compound gate:

- authenticated actor
- subject key match
- review item exists
- append-only decision record exists
- current review state allows next step
- no blocking evaluation finding
- artifact remains bound to review
- action is auditable
- kill path exists

No single field may satisfy this gate.

## Regression Rules

Tests must fail if:

- authority flags become positive
- evaluation text implies approval
- score text implies truth
- package/export language implies external action
- review snapshot language implies approval
- a new action route bypasses the compound gate

## Conclusion

Inspection can inform review.

Review can inform future action.

Inspection must never become authority.
