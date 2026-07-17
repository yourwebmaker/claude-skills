## Summary

As a developer working on flight search, I want the dev/test fixtures to seed a broader, more varied set of flights, so that I can exercise different origin/destination pairs, dates, and seat configurations without hand-rolling new database rows.

## Motivation

`src/DataFixtures/FlightFixtures.php` currently seeds only 5 flights (`AN101`, `AN102`, `AN201`, `AN305`, `AN410`), covering just four routes (JFK↔LAX, ORD→SFO, JFK→LHR, SFO→NRT) within a single 6-day window (2026-07-01 through 2026-07-06).

`AirportCode` supports six airports (`LHR`, `JFK`, `LAX`, `ORD`, `SFO`, `NRT`), so several origin/destination combinations — e.g. `LHR→ORD`, `NRT→SFO`, `LAX→SFO` — currently have no fixture data at all. Every flight also reuses the exact same four-seat map (`01A` business, `12A`/`12B`/`12C` economy), so there's no variation in cabin layout to exercise.

This thin fixture set makes it hard to manually exercise `GET /api/flights` and `GET /api/flights/{id}/seats` across a realistic range of routes, dates, and seat configurations, and it limits what fixture-backed tests can meaningfully assert.

## Proposed Solution

Expand the `$flights` array in `FlightFixtures::load()` to cover every `AirportCode` case as both an origin and a destination at least once, spread across a wider range of dates rather than a single 6-day window.

Include at least one route with multiple flights on different dates/times so date-filtered searches can return more than one result.

Introduce one or two alternate seat maps (different seat counts or class mixes) and apply them to a subset of flights instead of reusing the single hardcoded `$seatMap`, keeping the existing zero-padded seat-number convention (`'01A'`, not `'1A'`).

## Checklist
- [ ] `FlightFixtures` seeds flights covering every `AirportCode` case as both an origin and a destination at least once
- [ ] Fixtures include flights across multiple dates, not all within a single 6-day window
- [ ] At least one seeded route has multiple flights on different dates/times, to exercise multi-result search responses
- [ ] Not every flight uses an identical seat map — seat counts/classes vary across at least a couple of flights
- [ ] All new seat numbers follow the existing zero-padded convention (`'01A'`, not `'1A'`)
- [ ] Every new `Flight` constructor call satisfies `departureTime < arrivalTime`
- [ ] `docker compose exec aeronuk-flight-search php bin/phpunit` still passes with the expanded fixture set
