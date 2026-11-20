"""Deterministic journey advice and a driver-distraction policy gate.

In production a licensed navigation SDK emits verified route events. This module
currently accepts only explicitly simulated events; it does not use phone GPS.
"""
from uuid import uuid4
from .models import Journey, JourneyStage, RouteEvent, Suggestion, EventOutcome, MobilityMode


PLAYBOOK: dict[JourneyStage, tuple[str, str, str]] = {
    JourneyStage.AIRPORT: (
        "Terminal approach", "Check terminal and baggage-drop directions with airport staff.",
        "Prepare a short terminal-direction phrase",
    ),
    JourneyStage.STATION: (
        "Railway station", "Ask which platform serves your destination before boarding.",
        "Prepare the platform question",
    ),
    JourneyStage.HOTEL: (
        "Hotel arrival", "Prepare a short reservation and check-in request.",
        "Prepare the hotel check-in phrase",
    ),
    JourneyStage.PARKING: (
        "Parking information", "Ask staff to confirm any restrictions you cannot verify.",
        "Prepare a parking-permission question",
    ),
    JourneyStage.OFF_ROUTE: (
        "Route needs review", "Recalculate your route in a supported navigation application.",
        "Open the navigation app and review the route",
    ),
}


def assess_event(journey: Journey, route_event: RouteEvent) -> EventOutcome:
    """Apply source, safety, and relevance rules before producing any advice."""
    event = route_event.event
    if event not in PLAYBOOK:
        return EventOutcome(journey_id=journey.id, event=event,
                            suppressed=True, reason="No recommendation for this journey event", suggestion=None)
    # No non-critical interventions to someone driving a moving vehicle.
    if journey.mode == MobilityMode.DRIVE and not route_event.parked and event != JourneyStage.OFF_ROUTE:
        return EventOutcome(journey_id=journey.id, event=event,
                            suppressed=True, reason="Driving safety policy: context assistance waits until parked",
                            suggestion=None)

    title, message, action = PLAYBOOK[event]
    is_navigation = event == JourneyStage.OFF_ROUTE
    # Never synthesize turn instructions; off-route is only an action to review navigation.
    suggestion = Suggestion(
        id=str(uuid4()), title=title, message=message, action=action,
        priority="navigation" if is_navigation else "context",
        confidence=1.0,  # Confidence in rule match, NOT accuracy of road/parking facts.
        spoken_output_allowed=False,  # No TTS integrated in this starter.
    )
    return EventOutcome(journey_id=journey.id, event=event,
                        suppressed=False, reason=None, suggestion=suggestion)
