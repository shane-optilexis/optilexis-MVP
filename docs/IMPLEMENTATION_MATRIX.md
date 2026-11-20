# Optilexis requirement-to-code traceability

**Status as delivered:** 19 Nov 2026, Sprint 01 scaffold. `Verified` refers to automated backend tests in the authoring runtime; it does not imply a compiled mobile release.

| Requirement | Implementation location | Status / gap |
|---|---|---|
| Cross-platform iOS/Android app | `apps/mobile/lib/main.dart` | Source written; Flutter native runners/build validation needed |
| Premium navy/teal Optilexis theme | `apps/mobile/lib/src/design.dart` | Written; device visual QA pending |
| Destination and journey mode | `POST /v1/journeys`; setup screen | Backend verified; mobile not compiled |
| Language preferences (seven locales) | API models, UI dropdown | Backend verified; limited curated phrasebook only |
| Session lifecycle | API create/read/list/close | Verified, in-memory only, no auth |
| Context-based action recommendations | `predictor.py` | Verified with simulated events only |
| Deterministic driving safety gating | `predictor.py` | Verified moving/parked behavior |
| Consent choices | `Consent` model and UI switches | User preferences recorded locally in process; no OS permissions requested |
| Google Maps directions handoff | `main.dart::_handoff` | Implemented in source, device test pending; no live route events |
| Optilexis-owned navigation | `NavigationMode.OWN_ROUTE` contract | Not implemented: licensed HERE SDK required |
| Live ASR/translation/TTS | API `/v1/translation/freeform` returns 501 | Not implemented; demo phrase endpoint only |
| Meta glasses interactions | Device status list | Not implemented; device toolkit & hardware required |
| Vantrue E1 Pro S streaming | Capability explicitly unverified | Not implemented; seek official interface/terms |
| Local OCR and visual intelligence | Architecture spec only | Not implemented; future approved Drive Edge |
| CarPlay / Android Auto | Architecture spec only | Not implemented; platform approvals required |
| Secure accounts and persistence | Sprint 02 brief | Not implemented; no public deployment |
| Monitoring and analytics | Sprint 02/03 | Not implemented |
| Automated backend tests | `services/journey-api/tests` | 9 tests passing |
| Flutter build and widget tests | `apps/mobile/test` | Code provided; SDK unavailable in authoring runtime |

## Risk gates

- Handoff mode cannot and must not claim live navigation telemetry.
- Camera streaming depends on manufacturer-provided, permitted interfaces; no guessed RTSP endpoints.
- Driving UI must suppress non-navigation prompts while moving.
- Prototype backend must bind to `127.0.0.1` until authentication and transport security are in place.
- User location, microphone and video inputs are **not accessed** in this release.
