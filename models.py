from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class FrameStatus(Enum):
    READY = auto()
    IN_FLIGHT = auto()
    RECEIVED = auto()
    LOST = auto()
    DISCARDED = auto()
    ACKED = auto()
    RETRANSMITTING = auto()


class EventType(Enum):
    FRAME_ARRIVAL = auto()
    ACK_ARRIVAL = auto()
    TIMEOUT = auto()


@dataclass
class Frame:
    sequence_number: int
    status: FrameStatus = FrameStatus.READY
    sent_time: float | None = None
    retransmission_count: int = 0


@dataclass
class ACK:
    sequence_number: int


@dataclass(order=True)
class NetworkEvent:
    time: float
    event_type: EventType = field(compare=False)
    data: Any = field(compare=False)


@dataclass
class SimulationConfig:
    total_frames: int = 20
    window_size: int = 4
    sequence_bits: int = 3

    frame_loss_probability: float = 0.2
    ack_loss_probability: float = 0.1

    network_delay: float = 500.0
    timeout: float = 1000.0

    random_seed: int | None = 42

    @property
    def sequence_space(self) -> int:
        return 2 ** self.sequence_bits