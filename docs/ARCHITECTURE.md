# Optilexis mobile starter architecture

The Word specification under `docs/` is the authoritative product baseline. These code-oriented diagrams document the initial implementation and target interfaces.

## Sprint 01 interfaces

```mermaid
flowchart TB
    Mobile["Flutter phone app"] --> Client["OptilexisApi HTTP client"]
    Client --> API["FastAPI Journey API"]
    API --> Store["Ephemeral JourneyStore"]
    API --> Rules["Deterministic predictor + safety rules"]
    API --> Phrase["Curated 7-language demo phrasebook"]
    Mobile --> Maps["External Google Maps handoff"]
    Mobile -.->|Future license| HERE["HERE Navigate SDK"]
    Mobile -.->|Future supported device| Meta["Meta wearable adapter"]
    Mobile -.->|Vendor approval required| Vantrue["Vantrue camera adapter"]
```

## Vision inference target (not implemented)

```mermaid
flowchart LR
    Camera["Authorized video source"] --> Frame["Local sampled frame"]
    Frame --> OCR["On-device OCR"]
    OCR --> Lang["Language & classification"]
    Lang --> Context["Route-stage relevance"]
    Context --> Gate["Safety & uncertainty policy"]
    Gate --> Output["Minimal, approved assistance"]
```

## Scope boundaries

- Phone navigation state is independent of external Maps. Handoff never creates fake route progress.
- Prediction source in Sprint 01 is **simulation**, explicitly labeled by API and UI.
- No microphone, GPS or camera access is requested in the starter.
- `spoken_output_allowed` is always false until the TTS and safety stack is implemented.
