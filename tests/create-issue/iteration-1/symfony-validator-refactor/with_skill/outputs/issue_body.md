## Background

`FlightController::search()` currently validates its three required query
parameters (`origin`, `destination`, `date`) by hand: a chain of `if ($x ===
null) { return new JsonResponse(['error' => ...], 400); }` checks, followed by
`AirportCode::tryFrom(strtoupper(...))` for the airport codes and
`DateTimeImmutable::createFromFormat('Y-m-d', ...)` for the date, each with
its own null/false check and bespoke error message. This works, but it mixes
input validation with request handling in the controller, repeats the same
"missing" / "invalid" pattern five times, and gives every endpoint that needs
validation going forward the same copy-paste job. Symfony ships
`symfony/validator` for exactly this — declarative constraints plus a
`ConstraintViolationList` — which would let the controller focus on
orchestration (call the repository, serialize the result) instead of manual
parameter checking.

## User Story

As a developer maintaining `aeronuk-flight-search`, I want `FlightController`
to validate its inputs via Symfony Validator instead of hand-rolled
`if`/`tryFrom`/`createFromFormat` checks, so that validation logic is
declarative, consistent across endpoints, and easier to extend when new
parameters or endpoints are added.

## Acceptance Criteria

- [ ] `GET /api/flights` still returns `400` with a clear error body when
      `origin`, `destination`, or `date` is missing.
- [ ] `GET /api/flights` still returns `400` when `origin`/`destination` is
      not one of the `AirportCode` enum values (LHR, JFK, LAX, ORD, SFO, NRT).
- [ ] `GET /api/flights` still returns `400` when `date` is not a valid
      `YYYY-MM-DD` date.
- [ ] All manual `if (... === null)` / `tryFrom(...) === null` /
      `createFromFormat(...) === false` validation branches are removed from
      `FlightController::search()` and replaced by `symfony/validator`
      constraints.
- [ ] Existing behavior for `GET /api/flights/{id}/seats` (404 on unknown
      flight ID) is unchanged.
- [ ] Existing test suite (`docker compose exec aeronuk-flight-search php
      bin/phpunit`) passes without weakening any existing assertions on error
      responses.

## Tasks

- [ ] Add `symfony/validator` as a dependency if not already present (check
      `composer.json`).
- [ ] Introduce a small DTO (e.g. `FlightSearchQuery`) with `origin`,
      `destination`, and `date` properties, annotated with
      `#[Assert\NotBlank]` and a custom or built-in constraint that checks
      membership in the `AirportCode` enum for the airport fields, and
      `#[Assert\Date]` (or equivalent) for `date`.
- [ ] Map the incoming `Request` query parameters onto the DTO (e.g. via
      `RequestPayload`/`MapQueryString` mapping or manual hydration) before
      validation.
- [ ] Inject `ValidatorInterface` into `FlightController` and run validation
      against the DTO at the top of `search()`.
- [ ] Convert the resulting `ConstraintViolationList` into the existing `400`
      JSON error shape (`{"error": "..."}`) so API consumers see no breaking
      change in response format.
- [ ] Remove the now-redundant manual `if`/`tryFrom`/`createFromFormat`
      checks from `FlightController::search()`.
- [ ] Update/add controller tests to cover: missing param, invalid airport
      code, invalid date format, and the happy path, asserting on the
      validator-driven error responses.
