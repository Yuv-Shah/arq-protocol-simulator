from models import ACK, EventType, Frame
from network import NetworkSimulator
from simulator import SimulationEngine


def test_frame_is_delivered():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=500,
        frame_loss_probability=0.0,
        random_seed=42,
    )

    frame = Frame(sequence_number=0)

    delivered = network.send_frame(frame)

    assert delivered is True
    assert engine.has_events() is True

    event = engine.next_event()

    assert event.time == 500
    assert event.event_type == EventType.FRAME_ARRIVAL
    assert event.data == frame


def test_frame_is_always_lost():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=500,
        frame_loss_probability=1.0,
        random_seed=42,
    )

    frame = Frame(sequence_number=0)

    delivered = network.send_frame(frame)

    assert delivered is False
    assert engine.has_events() is False


def test_ack_is_delivered():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=500,
        ack_loss_probability=0.0,
        random_seed=42,
    )

    ack = ACK(sequence_number=0)

    delivered = network.send_ack(ack)

    assert delivered is True

    event = engine.next_event()

    assert event.time == 500
    assert event.event_type == EventType.ACK_ARRIVAL
    assert event.data == ack


def test_ack_is_always_lost():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=500,
        ack_loss_probability=1.0,
        random_seed=42,
    )

    ack = ACK(sequence_number=0)

    delivered = network.send_ack(ack)

    assert delivered is False
    assert engine.has_events() is False


def test_network_delay():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=750,
        frame_loss_probability=0.0,
    )

    frame = Frame(sequence_number=5)

    network.send_frame(frame)

    event = engine.next_event()

    assert event.time == 750