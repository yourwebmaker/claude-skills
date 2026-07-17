## Summary

`src/DataFixtures/FlightFixtures.php` currently seeds only **5 flights**, and they don't exercise much of the search space that `GET /api/flights` and `GET /api/flights/{id}/seats` need to support. This makes manual/exploratory testing against the dev environment (`docker compose up --build`) less useful than it could be, since most origin/destination/date combinations return an empty result.

## Current state

```php
$flights = [
    ['AN101', AirportCode::JFK, AirportCode::LAX, '2026-07-01 08:00:00', '2026-07-01 11:30:00', '299.99', 'USD'],
    ['AN102', AirportCode::LAX, AirportCode::JFK, '2026-07-01 13:00:00', '2026-07-01 21:15:00', '319.99', 'USD'],
    ['AN201', AirportCode::ORD, AirportCode::SFO, '2026-07-02 09:15:00', '2026-07-02 11:45:00', '249.50', 'USD'],
    ['AN305', AirportCode::JFK, AirportCode::LHR, '2026-07-03 19:00:00', '2026-07-04 07:00:00', '649.00', 'USD'],
    ['AN410', AirportCode::SFO, AirportCode::NRT, '2026-07-05 00:30:00', '2026-07-06 05:00:00', '899.00', 'USD'],
];
```

Observations:
- All 6 `AirportCode` values (`LHR`, `JFK`, `LAX`, `ORD`, `SFO`, `NRT`) appear at least once, but only as a handful of one-off routes — there's no round trip for most of them, and no route appears more than once.
- Every flight is on its own single date, spread across `2026-07-01` through `2026-07-06` — searching the same `origin`/`destination`/`date` never returns more than one flight, so the "list of results" case (as opposed to "single result") is never exercised via fixtures.
- Every flight gets the exact same 4-seat map (`01A` business, `12A`/`12B`/`12C` economy) — there's no fixture with a fully booked flight, a large seat map, or seat classes beyond business/economy (e.g. first, premium economy).
- No cancelled/past-dated flights to sanity-check that search stays scoped to what's expected.

## Proposal

Expand `FlightFixtures::load()` to include a richer, more realistic dataset, for example:
- At least one origin/destination/date combination with **multiple flights** (different times of day), so `GET /api/flights` fixture-based testing can show off list results, not just single-flight results.
- Round-trip coverage for more of the existing routes (currently only JFK↔LAX has both directions).
- A wider spread of seat maps — vary seat counts and class mix per flight, including at least one flight with a bigger cabin and one with only a couple of seats left.
- Keep using the zero-padded seat numbering convention (`'01A'`, not `'1A'`) and the existing per-flight persist/flush pattern — no changes needed to `FlightRepository`/`SeatRepository` sort behavior.

## Notes / non-goals

- This is fixture data only — no changes to entities, repositories, or controllers should be needed.
- Fixtures still only auto-load in `dev`/`test` and only when the `flight` table is empty (`LoadFixturesIfEmptyCommand`); that behavior is unaffected.
- Out of scope: pagination (explicitly not supported by design) and adding new airports (would require a new `AirportCode` enum case, which is a separate decision).

## Acceptance criteria

- [ ] `FlightFixtures` seeds a larger, more varied set of flights (more routes, at least one date/route with multiple flights, more seat map variety).
- [ ] Existing tests continue to pass against the expanded fixture set (or are updated if they assert on exact fixture counts/values).
- [ ] Seat numbers remain zero-padded per existing convention.
