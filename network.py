import random

from models import ACK, Frame, EventType, NetworkEvent
from simulator import SimulationEngine


class NetworkSimulator:
    def __init__(
        self,
        engine: SimulationEngine,
        delay: float = 500.0,
        frame_loss_probability: float = 0.0,
        ack_loss_probability: float = 0.0,
        random_seed: int | None = None,
    ):
        self.engine = engine
        self.delay = delay
        self.frame_loss_probability = frame_loss_probability
        self.ack_loss_probability = ack_loss_probability

        self.random = random.Random(random_seed)

        # Transmission statistics.
        self.frames_sent = 0
        self.frames_lost = 0

        self.acks_sent = 0
        self.acks_lost = 0

    def send_frame(self, frame: Frame) -> bool:
        """Send a frame through the simulated network."""

        self.frames_sent += 1

        if self.random.random() < self.frame_loss_probability:
            self.frames_lost += 1
            return False

        event = NetworkEvent(
            time=self.engine.current_time + self.delay,
            event_type=EventType.FRAME_ARRIVAL,
            data=frame,
        )

        self.engine.schedule_event(event)
        return True

    def send_ack(self, ack: ACK) -> bool:
        """Send an ACK through the simulated network."""

        self.acks_sent += 1

        if self.random.random() < self.ack_loss_probability:
            self.acks_lost += 1
            return False

        event = NetworkEvent(
            time=self.engine.current_time + self.delay,
            event_type=EventType.ACK_ARRIVAL,
            data=ack,
        )

        self.engine.schedule_event(event)
        return True

    def reset_statistics(self) -> None:
        """Reset network counters."""

        self.frames_sent = 0
        self.frames_lost = 0
        self.acks_sent = 0
        self.acks_lost = 0