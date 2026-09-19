from models import (
    Frame,
    ACK,
    NetworkEvent,
    EventType,
    FrameStatus,
    SimulationConfig,
)


def test_frame_creation():
    frame = Frame(sequence_number=5)

    assert frame.sequence_number == 5
    assert frame.status == FrameStatus.READY
    assert frame.sent_time is None
    assert frame.retransmission_count == 0


def test_ack_creation():
    ack = ACK(sequence_number=3)

    assert ack.sequence_number == 3


def test_network_event_creation():
    frame = Frame(sequence_number=2)

    event = NetworkEvent(
        time=500,
        event_type=EventType.FRAME_ARRIVAL,
        data=frame,
    )

    assert event.time == 500
    assert event.event_type == EventType.FRAME_ARRIVAL
    assert event.data == frame


def test_simulation_config():
    config = SimulationConfig()

    assert config.window_size == 4
    assert config.sequence_bits == 3
    assert config.sequence_space == 8