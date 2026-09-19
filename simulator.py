import heapq

from models import EventType, NetworkEvent


class SimulationEngine:
    def __init__(self):
        self.current_time = 0.0
        self.event_queue: list[tuple[float, int, int, NetworkEvent]] = []
        self._event_counter = 0

    def schedule_event(self, event: NetworkEvent) -> None:
        """Add an event to the simulation queue."""
        heapq.heappush(
            self.event_queue,
            (
                event.time,
                self.event_priority(event),
                self._event_counter,
                event,
            ),
        )
        self._event_counter += 1

    def event_priority(self, event: NetworkEvent) -> int:
        """Order simultaneous events in protocol-friendly order."""
        priorities = {
            EventType.ACK_ARRIVAL: 0,
            EventType.FRAME_ARRIVAL: 1,
            EventType.TIMEOUT: 2,
        }
        return priorities[event.event_type]

    def has_events(self) -> bool:
        """Return True if there are pending events."""
        return bool(self.event_queue)

    def next_event(self) -> NetworkEvent | None:
        """Remove and return the next event."""
        if not self.event_queue:
            return None

        _, _, _, event = heapq.heappop(self.event_queue)
        self.current_time = event.time

        return event

    def run_next(self, protocol):
        """
        Process the next simulation event
        using the supplied protocol.
        """
        event = self.next_event()

        if event is None:
            return None

        protocol.process_event(event)

        return event

    def reset(self) -> None:
        """Reset the simulation."""
        self.current_time = 0.0
        self.event_queue.clear()
        self._event_counter = 0


class SimulationController:
    """
    Controls one complete simulation run.

    The GUI will use this class later for:
    START, STEP, RESET, etc.
    """

    def __init__(self, engine, protocol):
        self.engine = engine
        self.protocol = protocol

        self.running = False
        self.finished = False

    def start(self) -> None:
        """Start the protocol."""

        self.protocol.start()

        self.running = True
        self.finished = False

    def step(self):
        """
        Process exactly one simulation event.

        Returns the processed event.
        """

        if self.finished:
            return None

        event = self.engine.run_next(
            self.protocol
        )

        if event is None:
            self.running = False
            self.finished = True
            return None

        if self.protocol.is_complete():
            self.running = False
            self.finished = True

        return event

    def run(self, max_steps: int = 10000) -> None:
        """
        Run the simulation until completion.
        """

        if not self.running:
            self.start()

        for _ in range(max_steps):
            if self.finished:
                break

            self.step()

    def pause(self) -> None:
        """Pause automatic execution."""
        self.running = False

    def resume(self) -> None:
        """Resume automatic execution."""
        if not self.finished:
            self.running = True

    def reset(self) -> None:
        """Reset the simulation engine."""

        self.engine.reset()

        self.running = False
        self.finished = False
