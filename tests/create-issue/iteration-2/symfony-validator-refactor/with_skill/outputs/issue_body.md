## Background

`FlightController::search()` currently validates its three required query parameters (`origin`, `destination`, `date`) by hand. Each parameter goes through its own `if ($x === null) { return new JsonResponse(['error' => ...], 400); }` check, and the two that need further parsing get a second check on top: `AirportCode::tryFrom(strtoupper(...))` for `origin`/`destination`, and `DateTimeImmutable::createFromFormat('Y-m-d', ...)` for `date`. That's five near-identical validation branches, each with its own hand-written error message, before the method ever reaches its actual job of calling `FlightRepository::search()`.

This works today, but it doesn't scale. Every new endpoint that needs input validation has to repeat the same missing/invalid pattern, the validation logic is entangled with request handling instead of being declarative, and there's no single place to see what's actually required of the request. `symfony/validator` (not currently a dependency of this project — it's absent from `composer.json`) exists specifically to replace this kind of hand-rolled checking with declarative constraints and a `ConstraintViolationList`.

The proposed direction is to introduce a small validated DTO for the search query (`origin`, `destination`, `date`), annotate it with Symfony constraints, and have `FlightController::search()` validate against that DTO instead of its current chain of manual checks. The externally observable behavior — which combinations of missing/invalid input return `400`, and with what shape of error body — should not change; this is an internal refactor of how that behavior is produced, not a change to the API contract.

## User Story

As a developer maintaining `aeronuk-flight-search`, I want `FlightController` to validate its inputs via Symfony Validator instead of hand-rolled `if`/`tryFrom`/`createFromFormat` checks, so that validation logic is declarative, consistent across endpoints, and easier to extend when new parameters or endpoints are added.

## Acceptance Criteria

- [ ] `GET /api/flights` still returns `400` with a clear error body when `origin`, `destination`, or `date` is missing.
- [ ] `GET /api/flights` still returns `400` when `origin`/`destination` is not one of the `AirportCode` enum values (LHR, JFK, LAX, ORD, SFO, NRT).
- [ ] `GET /api/flights` still returns `400` when `date` is not a valid `YYYY-MM-DD` date.
- [ ] All manual `if (... === null)` / `tryFrom(...) === null` / `createFromFormat(...) === false` validation branches are removed from `FlightController::search()` and replaced by `symfony/validator` constraints.
- [ ] Existing behavior for `GET /api/flights/{id}/seats` (404 on unknown flight ID via `FlightNotFound`) is unchanged.
- [ ] Existing test suite (`docker compose exec aeronuk-flight-search php bin/phpunit`) passes without weakening any existing assertions on error responses.

## Tasks

- [ ] Add `symfony/validator` as a Composer dependency (it is not currently required by this project).
- [ ] Introduce a small DTO (e.g. `FlightSearchQuery`) with `origin`, `destination`, and `date` properties, using `#[Assert\NotBlank]` plus a constraint that checks membership in the `AirportCode` enum for the airport fields, and `#[Assert\Date]` (or equivalent) for `date`.
- [ ] Map the incoming `Request` query parameters onto the DTO before validation (manual hydration or Symfony's request-to-DTO mapping).
- [ ] Inject `ValidatorInterface` into `FlightController` and run validation against the DTO at the top of `search()`.
- [ ] Convert the resulting `ConstraintViolationList` into the existing `400` JSON error shape (`{"error": "..."}`) so API consumers see no breaking change in response format.
- [ ] Remove the now-redundant manual `if`/`tryFrom`/`createFromFormat` checks from `FlightController::search()`.
- [ ] Update/add controller tests to cover: missing param, invalid airport code, invalid date format, and the happy path, asserting on the validator-driven error responses.
