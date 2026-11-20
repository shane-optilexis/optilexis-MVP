# Agent operating instructions — Optilexis

This file applies to all coding agents and contributors working in this repository.

## Product intent

Optilexis is a walking-first, multilingual journey companion. Carry destination, language and journey context across phone, supported wearables and future vehicle interfaces. Tagline: **One journey. Every language.** The source requirements are `docs/Optilexis_Mobile_App_Technical_Architecture_and_Development_Plan.docx`.

## Code principles

1. Preserve the modular phone-first design. Physical camera connectivity must be an optional adapter.
2. Never claim maps handoff grants live Apple/Google Maps route information. A licensed Optilexis-owned navigation provider is required for accurate route progress.
3. Do not fabricate AI translations, GPS data, manufacturer SDK APIs, road-sign legal meaning, spoken audio or cloud integrations. Clearly label simulations and unavailable features.
4. Follow a deterministic safety and consent policy before any AI-generated recommendation. Moving-vehicle prompts must be restricted; no distracting UI.
5. Keep provider credentials and user secrets out of Git, logs, mobile clients, mock payloads and screenshots.
6. Prefer small, tested, reviewable changes. Follow existing code style, add focused tests for features and refusals/suppression rules.
7. No public deployment while the backend lacks authentication, authorization, durable storage, rate limits, TLS, abuse controls and privacy review.
8. Do not reverse-engineer proprietary device interfaces or claim the published Vantrue open-source materials constitute a camera SDK. Seek vendor documentation/license.
9. Retain the 26-week roadmap and stage-gates from the source document unless a product owner explicitly revises them.
10. Keep third-party hardware and vehicle SDKs behind interfaces and feature flags. Build phone-only fallbacks.

## Useful commands

```bash
cd services/journey-api && python -m pytest
cd apps/mobile && flutter analyze && flutter test
```

The Flutter SDK is not installed in the original authoring container. Run Flutter checks on a prepared machine; disclose any skipped checks.

## Before marking a PR ready

- [ ] API tests pass; Flutter analyze/test pass where SDK available.
- [ ] Feature status and limitations updated in `docs/IMPLEMENTATION_MATRIX.md`.
- [ ] Safety gate tests cover driving, uncertainties, consent and no-hardware modes.
- [ ] No third-party API credentials or privileged settings committed.
- [ ] All new user-visible functionality has meaningful failure/denial behavior.
