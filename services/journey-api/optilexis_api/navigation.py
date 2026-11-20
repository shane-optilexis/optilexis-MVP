"""Provider-independent navigation contract; no device location is captured here."""
from dataclasses import dataclass
from enum import Enum
from typing import AsyncIterator, Protocol
from uuid import UUID


class NavigationSource(str, Enum):
    SIMULATION = "simulation"
    HERE_NATIVE = "here_native"


@dataclass(frozen=True)
class NavigationEvent:
    journey_id: UUID
    kind: str
    source: NavigationSource
    simulated: bool
    # No traffic/turn/position supplied for simulated contexts.


class NavigationUnavailable(RuntimeError):
    pass


class LocationPermissionDenied(NavigationUnavailable):
    pass


class NavigationProvider(Protocol):
    async def start_route(self, journey_id: UUID, *, location_permission_granted: bool) -> None: ...
    def subscribe(self, journey_id: UUID) -> AsyncIterator[NavigationEvent]: ...
    async def stop_route(self, journey_id: UUID) -> None: ...


class SimulatedNavigationProvider:
    """Explicitly scripted source for tests; never reports itself as a real SDK."""
    def __init__(self, event_kinds: list[str] | None = None) -> None:
        self._events = event_kinds or []
        self._running: set[UUID] = set()

    async def start_route(self, journey_id: UUID, *, location_permission_granted: bool) -> None:
        # This simulator does not read device location; deny attempts to imply a real GPS route.
        self._running.add(journey_id)

    async def subscribe(self, journey_id: UUID) -> AsyncIterator[NavigationEvent]:
        if journey_id not in self._running:
            raise NavigationUnavailable("Simulation route not started")
        for kind in self._events:
            if journey_id not in self._running:
                break
            yield NavigationEvent(journey_id, kind, NavigationSource.SIMULATION, simulated=True)

    async def stop_route(self, journey_id: UUID) -> None:
        self._running.discard(journey_id)


class HereNavigateBoundary:
    """Explicit feature-flagged boundary until licensed native HERE SDK is integrated."""
    def __init__(self, *, enabled: bool = False):
        self.enabled = enabled

    async def start_route(self, journey_id: UUID, *, location_permission_granted: bool) -> None:
        if not self.enabled:
            raise NavigationUnavailable("HERE Navigate feature flag is disabled")
        if not location_permission_granted:
            raise LocationPermissionDenied("Location permission required for device navigation")
        raise NavigationUnavailable("HERE Navigate SDK not integrated")

    async def subscribe(self, journey_id: UUID) -> AsyncIterator[NavigationEvent]:
        raise NavigationUnavailable("HERE Navigate SDK not integrated")
        if False:  # pragma: no cover - preserves AsyncIterator function signature
            yield

    async def stop_route(self, journey_id: UUID) -> None:
        raise NavigationUnavailable("HERE Navigate SDK not integrated")


class MapsHandoffBoundary:
    """External Maps launch is not an event stream and must not promise maneuvers."""
    async def start_route(self, journey_id: UUID, *, location_permission_granted: bool) -> None:
        raise NavigationUnavailable("Launch external Maps app on device; no owned navigation session")

    async def subscribe(self, journey_id: UUID) -> AsyncIterator[NavigationEvent]:
        raise NavigationUnavailable("Google/Apple Maps do not expose route events to this app")
        if False:  # pragma: no cover
            yield

    async def stop_route(self, journey_id: UUID) -> None:
        return
