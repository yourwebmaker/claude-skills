## Background

`AeroNuk\FlightSearch\ValueObject\AirportCode` is a closed, string-backed enum
(`JFK`, `LAX`, `ORD`, `SFO`, `LHR`, `NRT`). The only place user input is
turned into an `AirportCode` is `FlightController::search()`
(`src/Controller/FlightController.php`), which does this twice, once for
`origin` and once for `destination`:

```php
$origin = AirportCode::tryFrom(strtoupper($originParam));
if ($origin === null) {
    return new JsonResponse(['error' => 'origin must be a known 3-letter airport code'], 400);
}
```

Two implementation details of `AirportCode` have leaked out of the value
object and into the controller:

1. **Case normalization.** The fact that `AirportCode`'s backing values are
   uppercase strings — and therefore that raw input must be uppercased
   before `tryFrom()` will match it — is knowledge the controller has to
   carry. Any other future caller (another controller, a console command,
   an import job) would have to rediscover and re-implement the same
   `strtoupper()` call, or silently reject valid lowercase input like `lhr`.
2. **Format assumptions in error messages.** Both branches hardcode the
   string `"3-letter airport code"` in the client-facing error message. That
   string encodes an assumption about `AirportCode`'s representation that
   belongs to the enum, not to the controller — and it's duplicated across
   the `origin` and `destination` branches instead of defined once.

This is exactly the kind of leak the value object should absorb: parsing and
validating a raw string into a domain type is `AirportCode`'s job, not
`FlightController`'s.

## User Story

As a developer maintaining `aeronuk-flight-search`, I want `AirportCode` to
own the rules for turning a raw string into a valid airport code, so that
`FlightController` (and any future caller) doesn't need to duplicate
knowledge of the enum's case sensitivity or string format.

## Acceptance Criteria

- [ ] `AirportCode` exposes a single factory method (e.g. `fromInput(string $value): ?self`) that performs case-insensitive parsing internally — callers no longer call `strtoupper()` themselves before parsing.
- [ ] `FlightController::search()` no longer contains a `strtoupper()` call or any hardcoded description of the enum's format (e.g. "3-letter"); it delegates entirely to `AirportCode`.
- [ ] The duplicated origin/destination "missing param" + "invalid param" 400-response logic in `FlightController::search()` is consolidated into one helper instead of being repeated twice.
- [ ] `GET /api/flights` behavior is unchanged from the outside: lowercase, uppercase, and mixed-case valid codes still resolve correctly; unknown codes still return `400`.
- [ ] `tests/Controller/FlightControllerTest.php`, including `testSearchWithUnknownAirportCodeReturns400`, passes without modification to its assertions.

## Tasks

- [ ] Add a factory method to `src/ValueObject/AirportCode.php` (e.g. `public static function fromInput(string $value): ?self`) that normalizes case and delegates to `self::tryFrom()`.
- [ ] Update `src/Controller/FlightController.php` to call the new `AirportCode::fromInput()` for both `origin` and `destination` instead of `AirportCode::tryFrom(strtoupper(...))`.
- [ ] Remove the now-unused `strtoupper` import/usage from `FlightController.php`.
- [ ] Extract the repeated "required" + "must be a known airport code" 400-response branches into a small private helper in `FlightController` shared by `origin` and `destination`.
- [ ] Add unit test coverage for `AirportCode::fromInput()` directly (valid uppercase, valid lowercase/mixed-case, unknown code returns `null`).
- [ ] Run `docker compose exec aeronuk-flight-search php bin/phpunit` and confirm the full suite, especially `FlightControllerTest`, still passes.
