## Context

Today `Flight` (`src/Entity/Flight.php`) models a single direct leg: one `origin`, one `destination`, one `departureTime`/`arrivalTime`, one `price`. `GET /api/flights` returns a flat list of these legs matching an origin/destination/date search — there's no domain concept above the individual flight.

That's fine for a single direct hop, but it can't represent:
- **Round trips** (outbound + return as one unit)
- **Multi-leg / connecting itineraries** (e.g. LHR → JFK via ORD as two `Flight`s that belong together)
- **A combined price/duration for the itinerary as a whole**, as opposed to per-leg price

A `Trip` class would be the aggregate that groups one or more ordered `Flight`s into a single bookable itinerary.

## Proposal

Introduce `AeroNuk\FlightSearch\Entity\Trip`:

- `id` (string, passed in by the caller — consistent with `Flight`/`Seat`, no in-constructor ID generation per the "Entity/VO IDs are always passed in from the caller" decision in `CLAUDE.md`)
- An ordered collection of `Flight` legs (e.g. `TripSegment` join entity carrying `Trip`, `Flight`, and a `sequence` int — or a simpler `ManyToMany` with an explicit order column, whichever keeps Doctrine mapping straightforward)
- Validation in the constructor: at least one leg, legs are chronologically ordered, and each leg's `destination` matches the next leg's `origin` (connection continuity)
- A derived/computed total price (sum of leg `Money` prices — same currency assumed, matching existing `Money` embeddable) and overall departure/arrival (first leg's departure, last leg's arrival)

Follow the existing conventions in this codebase (see `CLAUDE.md`):
- Public `readonly` properties, no getters — `symfony/serializer` reads directly
- No `repositoryClass` attribute; a plain `TripRepository` DI service (constructor-injected `EntityManagerInterface`), following the `FlightRepository`/`SeatRepository` pattern, with a `get(string $id): Trip` that throws a `TripNotFoundException` rather than returning `null`
- A Doctrine migration for the new `trip` table (and join table/column if a separate segment entity is used)

## Open questions (to resolve before implementation)

1. **Does this need a new endpoint**, e.g. `GET /api/trips` or a way to request connecting itineraries from `GET /api/flights`, or is this purely an internal domain model for now (no API surface change)?
2. **Single-currency assumption** — do we allow a `Trip` whose legs have mixed currencies, or reject/convert at construction time?
3. Should `Trip` support **connections only**, or also **round trips** (where leg 2's origin/destination reverse leg 1's, not necessarily forming a single continuous journey)?
4. Do seats need to be booked per-leg still (existing `GET /api/flights/{id}/seats` unchanged), or does booking move to the `Trip` level?

## Suggested scope for a first PR

- `Trip` entity + constructor validation
- `TripRepository` (`get()` only, no search yet)
- Migration
- Unit tests for validation rules (empty legs, non-contiguous legs, out-of-order legs)

No API/controller changes in the first pass — keep this to the domain model so the shape can be reviewed before it's wired into `/api`.
