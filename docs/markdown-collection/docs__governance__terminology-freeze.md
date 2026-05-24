# Terminology Freeze

## Purpose

Terminology can create capability drift before code does.

This freeze defines where dangerous terms are allowed and where they are blocked.

## Surface Classes

### Runtime And Product Surfaces

Restricted:

- API contracts
- API routes
- response objects
- draft package code
- manual export code
- public UI copy
- internal console UI copy
- operational helper code

These surfaces must avoid terms that imply public action, workflow execution, or growth optimization.

### Governance And Risk Documentation

Allowed to mention banned terms when documenting:

- risks
- forbidden capabilities
- negative examples
- escalation dangers
- terminology freezes
- audit findings
- irreversible boundaries
- red-team cases

Governance docs may name the danger directly because their purpose is to prevent it.

## Frozen Runtime Terms

Runtime/product surfaces must not introduce:

- publish
- deploy
- launch
- autopilot
- growth engine
- engagement optimization
- campaign execution
- readyToPost
- readyToPublish
- scheduled
- distributed
- deliverable
- uploaded
- queued

## Allowed Negative-Control Literals

These literals are allowed because they explicitly deny authority:

- `publishAuthority: false`
- `publishReady: false`
- `approvalAuthority: false`
- `automationAllowed: false`
- `externalDelivery: false`
- `distributionAuthority: false`

They must not be paired with action controls.

## Detector And Red-Team Exceptions

Detector fixtures may contain forbidden language only when the purpose is detection.

Examples:

- forbidden-energy detector terms
- calibration fixtures
- red-team regression cases

Such usage must not be presented as product copy or user-facing workflow language.

## Review Rule

Any new term that implies:

- external action
- public availability
- timed execution
- autonomous operation
- audience acquisition
- authority transfer

requires governance review before use.

## Conclusion

The system should use institutional inspection language.

It should not drift into platform, campaign, creator, or growth-product language.
