# PRD.md
# DeployMind — Product Requirements Document

## 1. Product Overview

DeployMind is a prototype for pre-deployment risk assessment in microservices applications. It aims to help developers understand code changes, estimate affected services, select relevant validations, and produce an explainable deployment recommendation.

## 2. Problem Statement

A small change in one microservice can affect dependent services. Without structured analysis, teams may overlook downstream impact or proceed without appropriate validation.

DeployMind aims to make this assessment more systematic by connecting change analysis, dependency analysis, risk scoring, validation recommendations, and decision logic.

## 3. Goals

- Identify code changes relevant to a proposed deployment.
- Map changes to application services.
- Estimate direct and indirect blast radius.
- Calculate a risk score and risk category.
- Recommend configured validation checks.
- Consider validation outcomes when generating a recommendation.
- Return a consolidated result with a human-readable reason.
- Demonstrate a sample microservices application in a local containerized environment.

## 4. Scope

### In scope
- Change-analysis module
- Dependency and blast-radius analysis
- Risk scoring
- Rule-based validation recommendations
- Validation components for API tests, health checks, and load tests
- Decision Engine and pipeline orchestration
- Gateway, Task Service, and Worker Service demo

### Out of scope unless implemented separately
- Guaranteeing that a deployment is safe
- Replacing code review or established CI/CD controls
- Automatic production deployment or rollback
- Claiming an LLM-powered agent when the implementation is rule-based

## 5. Target Users

| User | Need |
|---|---|
| Developer | Understand the risk associated with code changes |
| DevOps / Platform Engineer | Estimate impact across services |
| Reviewer / Evaluator | Understand how a recommendation is produced |
| Project Team | Demonstrate modular analysis and microservices |

## 6. User Stories

- As a developer, I want to identify changed files so I know what is being evaluated.
- As a platform engineer, I want to inspect dependencies to estimate downstream impact.
- As a reviewer, I want a risk score and level that are easy to interpret.
- As a developer, I want relevant validations recommended for the change.
- As a release owner, I want a final recommendation and explanation to support a decision.
- As a demonstrator, I want to run the sample services locally and show task processing.

## 7. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Analyze a set of code changes. | Must |
| FR-02 | Identify services associated with the changes. | Must |
| FR-03 | Estimate direct and indirect service impact. | Must |
| FR-04 | Calculate a numeric risk score and risk level. | Must |
| FR-05 | Recommend validations using configured rules. | Must |
| FR-06 | Capture or report validation outcomes. | Must |
| FR-07 | Generate a `SAFE`, `CANARY`, or `BLOCKED` recommendation. | Must |
| FR-08 | Return a consolidated result with an explanation. | Must |
| FR-09 | Demonstrate task creation and processing through the sample API. | Should |
| FR-10 | Provide repeatable local setup and test instructions. | Should |
| FR-11 | Run relevant checks in CI. | Future / verify |

## 8. Non-Functional Requirements

- **Modularity:** Each analysis stage has a clear responsibility and interface.
- **Explainability:** The result includes a reason and useful intermediate details.
- **Reproducibility:** Setup and test instructions can be followed consistently.
- **Reliability:** Missing or failed required validations are handled explicitly.
- **Maintainability:** Scoring rules and decision thresholds are inspectable.
- **Safety:** Prototype recommendations do not silently override release controls.
- **Performance:** Validation execution should use defined timeouts before CI/CD use.

Quantitative performance targets remain to be established.

## 9. Acceptance Criteria

- [x] A known, non-empty code change reaches the Change Analyzer.
- [x] Expected changed files appear in the result.
- [x] A known service change maps to the expected service.
- [x] Dependency analysis matches a documented dependency scenario.
- [x] Blast-radius results match expected test cases.
- [x] Risk scoring is deterministic for fixed inputs.
- [x] Agent recommendations follow configured rules.
- [x] Passing and failing validations produce expected decisions.
- [x] The pipeline returns a consolidated result and explanation.
- [x] The orchestrator has produced a sample consolidated result.
- [x] The sample microservices have demonstrated task creation and processing.
- [x] Full integration has been verified using a real, non-empty change set.

Checked items represent evidence reported during development. Remaining items are verification goals.

## 10. Success Metrics

Proposed measures:
- Correct identification of known changed files.
- Accuracy of service-impact mapping on test scenarios.
- Agreement between expected and actual risk scores.
- Correct decision outcomes for validation pass/fail cases.
- Pipeline runtime on a documented test repository.
- Usefulness of decision explanations.

Targets and baselines should be set after initial measurement.

## 11. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Empty or invalid change input | Test empty, valid, and invalid diff scenarios |
| Incomplete dependency map | Validate against documented service graphs |
| Validation reported as passed without execution | Record execution status and result provenance |
| Incompatible module interfaces | Add contract and integration tests |
| Hard-coded scoring assumptions | Document rules and test representative cases |
| Prototype used as sole release gate | Keep human review and established controls |

## 12. Roadmap

### Phase 1 — Core prototype
- Build analysis modules and decision logic.
- Demonstrate local microservices.
- Produce a consolidated pipeline result.

### Phase 2 — Integration and verification
- Test using real, non-empty code changes.
- Add end-to-end and contract tests.
- Verify validation execution and failure handling.
- Document scoring rules and decision thresholds.

### Phase 3 — CI/CD integration
- Connect analysis to pull requests or CI events.
- Publish decision summaries.
- Add logging, metrics, and execution timeouts.

### Phase 4 — Advanced capabilities
- Improve dependency discovery.
- Consider historical change or incident signals.
- Evaluate optional LLM-assisted explanations with deterministic safeguards.

## 13. Definition of Done

A feature is complete when its behavior is documented, relevant tests pass, integration behavior is verified where applicable, failure cases are considered, and documentation matches the implementation.
