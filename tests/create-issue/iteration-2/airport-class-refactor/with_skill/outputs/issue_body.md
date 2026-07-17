## Background

`AirportCode` is a closed, string-backed enum (`JFK`/`LAX`/`ORD`/`SFO`/`LHR`/`NRT`) meant to be the single source of truth for what a valid airport looks like in this service. In practice, though, the logic for turning a raw query-string value into an `AirportCode` — normalizing case with `strtoupper()` and then resolving it with `AirportCode::tryFrom()` — lives in `FlightController::search()`, duplicated once for `origin` and once for `destination`.

That's an implementation leak: callers of `AirportCode` have to know it's a string-backed enum, that it's uppercase, and that `tryFrom()` returns `null` on a miss, then re-derive the same two-line parsing dance themselves. The value object should own that knowledge instead of exposing it for every call site to reconstruct. Today there's only one call site duplicating the logic (twice, for the two params), but any future endpoint that accepts an airport code from user input would have to copy the same pattern again.

The fix is to give `AirportCode` a named constructor — something like `AirportCode::fromInput(string $value): ?self` — that owns the normalization and lookup, so `FlightController` just calls it and handles the `null` case, without knowing anything about how the enum backs or matches its values.

## User Story

As a developer working on `aeronuk-flight-search`, I want the parsing/normalization of user-supplied airport codes encapsulated in `AirportCode` itself, so that controllers (and any future call sites) don't need to know or duplicate how a raw string becomes a valid `AirportCode`.

## Acceptance Criteria

- [ ] `AirportCode` exposes a single named constructor (e.g. `fromInput(string $value): ?self`) that performs case normalization and validation, returning `null` for an unknown code
- [ ] `FlightController::search()` no longer calls `strtoupper()` or `AirportCode::tryFrom()` directly; it delegates to the new `AirportCode` method for both `origin` and `destination`
- [ ] Existing behavior is unchanged: a valid code in any case (e.g. `lhr`, `Lhr`, `LHR`) still resolves correctly, and an unknown code still results in a `400` response with the existing error message
- [ ] All existing tests (`tests/Controller/FlightControllerTest.php`, `tests/Repository/FlightRepositoryTest.php`, `tests/Repository/SeatRepositoryTest.php`) continue to pass without modification to their assertions
- [ ] A new unit test covers `AirportCode::fromInput()` directly, including a valid lowercase code, a valid uppercase code, and an unknown code

## Tasks

- [ ] Add a `fromInput(string $value): ?self` static method to `src/ValueObject/AirportCode.php` that applies `strtoupper()` and delegates to `self::tryFrom()`
- [ ] Update `src/Controller/FlightController.php` to call `AirportCode::fromInput($originParam)` and `AirportCode::fromInput($destinationParam)` in place of the inline `strtoupper()` + `tryFrom()` calls
- [ ] Remove the now-unused `strtoupper` import from `FlightController.php` if nothing else in the file needs it
- [ ] Add unit tests for `AirportCode::fromInput()` covering case-insensitivity and the unknown-code `null` case
- [ ] Run the full test suite (`docker compose exec aeronuk-flight-search php bin/phpunit`) to confirm no regressions
