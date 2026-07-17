## Background

The domain model in `aeronuk-flight-search` currently revolves entirely around a single `Flight` (`src/Entity/Flight.php`): one origin, one destination, one departure/arrival pair, and a `Money` price. `Seat` (`src/Entity/Seat.php`) belongs to exactly one `Flight` via an eager `ManyToOne`, and there is no existing `Trip`-like concept anywhere in the codebase.

There is currently no way to represent an itinerary made up of more than one flight leg. `GET /api/flights` only searches single, direct, point-to-point flights, and `AirportCode` is a closed enum (`LHR`/`JFK`/`LAX`/`ORD`/`SFO`/`NRT`), so not every origin/destination pair in that set necessarily has a direct flight between them.

To support connecting itineraries (e.g. `LHR` -> `JFK` -> `LAX`), we should introduce a `Trip` class that represents an ordered sequence of one or more `Flight` legs as a single bookable unit. This is greenfield work — it should follow the existing conventions already established in this codebase: public readonly properties with no getters, IDs supplied by the caller rather than generated in the constructor, and a plain DI-service repository (not a `ServiceEntityRepository` subclass).

## Assumptions

Since this is a one-line request ("Introduce Trip class") and clarifying questions are out of scope for this run, the following assumptions are used to draft the issue below. These should be confirmed with the team before implementation starts:

- `Trip` is a new entity (not a rename or refactor of `Flight`), living at `src/Entity/Trip.php`, mirroring `Flight`'s conventions.
- A `Trip` models an ordered, non-empty sequence of one or more existing `Flight` legs (a single-leg `Trip` is valid, representing a direct itinerary uniformly with multi-leg ones).
- Consecutive legs must connect: each leg's `origin` equals the previous leg's `destination`, and each leg's `departureTime` is strictly after the previous leg's `arrivalTime` — mirroring the existing `departureTime >= arrivalTime` guard in `Flight::__construct`.
- `Trip` derives its overall `origin`, `destination`, `departureTime`, `arrivalTime`, and total `price` from its constituent legs rather than storing them redundantly.
- This issue covers the domain model, persistence, and fixtures/tests for `Trip`. Whether `Trip` gets its own public endpoint (e.g. `GET /api/trips`) is left as an open decision for implementation, not assumed here.
- No changes to the existing `GET /api/flights` or `GET /api/flights/{id}/seats` endpoints are in scope.

## User Story

As a traveler searching for flights, I want to search for and view multi-leg trips made up of connecting flights, so that I can travel between airports that don't have a direct flight available.

## Acceptance Criteria

- [ ] A `Trip` entity exists representing an ordered, non-empty sequence of `Flight` legs.
- [ ] `Trip` construction rejects legs that don't connect properly: each leg's `origin` must equal the previous leg's `destination`, and each leg's `departureTime` must be after the previous leg's `arrivalTime`.
- [ ] `Trip` exposes a derived overall `origin` (first leg's origin), overall `destination` (last leg's destination), overall `departureTime`/`arrivalTime`, and a total `price` computed from its legs.
- [ ] A single-leg `Trip` (exactly one `Flight`) is valid, so `Trip` can represent both direct and connecting itineraries uniformly.
- [ ] Existing single-flight behavior (`GET /api/flights`, `GET /api/flights/{id}/seats`) is unchanged by this addition.

## Tasks

- [ ] Add `src/Entity/Trip.php` following existing entity conventions: `public readonly` properties, ID passed in by the caller, no getters, constructor-level validation (see `Flight::__construct`'s `departureTime >= arrivalTime` check for the pattern to follow).
- [ ] Model the `Trip` <-> `Flight` ordered association (e.g. a `trip_flight` join table carrying leg order) and add the corresponding Doctrine mapping, respecting the `Money`/embeddable and `dir: %kernel.project_dir%/src` conventions already established in `config/packages/doctrine.yaml`.
- [ ] Write a Doctrine migration for the new `trip` table (and join table, if used).
- [ ] Add `TripRepository` as a plain DI service taking `EntityManagerInterface` via constructor injection (not `ServiceEntityRepository`), matching `FlightRepository`/`SeatRepository`.
- [ ] Extend `src/DataFixtures/FlightFixtures.php` (or add a new `TripFixtures.php`) with sample multi-leg trips built from existing fixture flights.
- [ ] Add unit tests covering: valid multi-leg trip construction, valid single-leg trip construction, and rejection of a trip whose legs don't connect (origin/destination mismatch or non-increasing times).
- [ ] Decide and document whether `Trip` is exposed via a new endpoint (e.g. `GET /api/trips`) or is purely an internal building block for now.
