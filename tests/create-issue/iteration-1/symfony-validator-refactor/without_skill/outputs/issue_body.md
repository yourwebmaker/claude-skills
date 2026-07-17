## Summary

`FlightController::search()` currently validates its three required query
parameters (`origin`, `destination`, `date`) by hand, with a separate
`if`/`return` block per field. This works, but it's repetitive and mixes
validation with control flow. We should replace it with `symfony/validator`
constraints so the controller only contains request-handling logic.

## Current code

`src/Controller/FlightController.php`:

```php
#[Route('/api/flights', name: 'flights_search', methods: ['GET'])]
public function search(Request $request): JsonResponse
{
    $originParam = $request->query->get('origin');
    if ($originParam === null) {
        return new JsonResponse(['error' => 'origin is required'], 400);
    }

    $origin = AirportCode::tryFrom(strtoupper($originParam));
    if ($origin === null) {
        return new JsonResponse(['error' => 'origin must be a known 3-letter airport code'], 400);
    }

    $destinationParam = $request->query->get('destination');
    if ($destinationParam === null) {
        return new JsonResponse(['error' => 'destination is required'], 400);
    }

    $destination = AirportCode::tryFrom(strtoupper($destinationParam));
    if ($destination === null) {
        return new JsonResponse(['error' => 'destination must be a known 3-letter airport code'], 400);
    }

    $dateParam = $request->query->get('date');
    if ($dateParam === null) {
        return new JsonResponse(['error' => 'date is required'], 400);
    }

    $date = DateTimeImmutable::createFromFormat('Y-m-d', $dateParam);
    if ($date === false) {
        return new JsonResponse(['error' => 'date must be in YYYY-MM-DD format'], 400);
    }

    $flights = $this->flightRepository->search($origin, $destination, $date);

    return JsonResponse::fromJsonString($this->serializer->serialize($flights, 'json'));
}
```

Six manual null/format checks before any actual search logic runs. Each new
required param (or new validation rule) means another copy-pasted `if`
block.

## Proposal

- Add `symfony/validator` to `composer.json` (not currently a dependency).
- Introduce a request DTO, e.g. `FlightSearchQuery`, with `#[Assert\NotBlank]`
  on `origin`/`destination`/`date`, plus either a custom constraint or
  `#[Assert\Choice]` (backed by `AirportCode` enum values) for the airport
  codes, and `#[Assert\Date]` (or a custom constraint) for `date`.
- Populate the DTO from `$request->query` and run it through
  `ValidatorInterface::validate()` in the controller (or a small trait/base
  method shared by controllers, if we end up with more than one).
- On violations, return the existing `400` shape
  (`{"error": "..."}`) — decide whether to keep a single first-error message
  or expose all violations. Given today's tests only assert
  `assertArrayHasKey('error', ...)`, either is compatible, but pick one
  intentionally rather than let it fall out of the serializer.
- Keep converting `origin`/`destination` into `AirportCode` enum instances
  and `date` into a `DateTimeImmutable` for the repository call — the
  validator only replaces the *checking*, not the parsing into value
  objects.

## Why

- Removes ~30 lines of repetitive manual validation from the controller,
  leaving it focused on orchestration (parse → search → serialize).
- Matches the project's stated direction of using Symfony's own components
  rather than reinventing them.
- Makes it a one-line change (add a constraint) to validate a new parameter
  in the future instead of another copy-pasted `if` block.

## Scope / out of scope

- In scope: `GET /api/flights` (the only endpoint with parameter validation
  today).
- `GET /api/flights/{id}/seats` has no query params to validate — its
  `FlightNotFoundException`-to-404 mapping is unrelated and out of scope.
- No change to response shapes/status codes expected by existing tests in
  `tests/Controller/FlightControllerTest.php` (`testSearchRequiresOrigin`,
  `testSearchRequiresDestination`, `testSearchRequiresDate`,
  `testSearchWithInvalidDateReturns400`,
  `testSearchWithUnknownAirportCodeReturns400`) — all five should keep
  passing unmodified, still asserting `400` + `error` key.

## Acceptance criteria

- [ ] `symfony/validator` added as a dependency.
- [ ] `FlightController::search()` no longer contains manual `if ($x ===
      null)` / `tryFrom(...) === null` / `createFromFormat(...) === false`
      checks — validation is expressed as constraints.
- [ ] All existing tests in `FlightControllerTest` still pass without
      modification (response codes/shapes unchanged).
- [ ] Missing/invalid `origin`, `destination`, or `date` still yield `400`
      with an `error` key in the JSON body.
