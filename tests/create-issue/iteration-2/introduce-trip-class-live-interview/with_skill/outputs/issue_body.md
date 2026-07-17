## Background

`Flight` currently has no rule preventing `origin` and `destination` from
being the same `AirportCode`. Nothing in the entity, the repository, or
`FlightController::search()` rejects a request or a fixture where both are
identical — a "flight" from JFK to JFK would construct and persist without
error.

The codebase already has a precedent for this kind of guard: `Flight`'s
constructor rejects `departureTime >= arrivalTime` with an
`InvalidArgumentException`, specifically to keep the domain from
representing a nonsensical state. Origin equaling destination is the same
category of problem — a route that can't exist in reality — and should be
rejected the same way, at construction time, rather than relying on callers
to remember to check.

This was originally scoped as introducing a `Trip` concept, but the actual
gap turned out to be narrower: no multi-leg/round-trip modeling is needed
here, just this single-flight invariant.

## User Story

As someone searching for or creating flights, I want the system to reject a
flight whose origin and destination are identical, so that the data can
never contain a nonsensical zero-distance route.

## Acceptance Criteria

- [ ] Constructing a `Flight` with `origin === destination` throws an
      `InvalidArgumentException`, mirroring the existing
      `departureTime >= arrivalTime` check.
- [ ] `GET /api/flights` returns `400` with a clear error message when
      `origin` and `destination` are the same airport code.
- [ ] Existing flights and tests are unaffected (no valid flight currently
      has identical origin/destination, so this is purely additive).

## Tasks

- [ ] Add an `origin !== destination` check to `Flight`'s constructor,
      throwing `InvalidArgumentException` in the same style as the existing
      `departureTime`/`arrivalTime` guard.
- [ ] Add the same check to `FlightController::search()` so a same-airport
      request returns `400` consistently with the other validation errors
      (missing param, invalid airport code, invalid date).
- [ ] Add a unit test asserting `Flight`'s constructor rejects identical
      origin/destination.
- [ ] Add a controller test asserting `GET /api/flights?origin=X&destination=X`
      returns `400`.

