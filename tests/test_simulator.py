from models import ACK, EventType, Frame, FrameStatus, NetworkEvent
from simulator import SimulationEngine, SimulationController
from network import NetworkSimulator
from protocols import GoBackN


def test_gbn_engine_processes_events():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=100,
        frame_loss_probability=0.0,
        ack_loss_probability=0.0,
        random_seed=42,
    )

    gbn = GoBackN(
        engine=engine,
        network=network,
        total_frames=4,
        window_size=2,
        timeout=500,
    )

    gbn.start()

    assert engine.has_events()

    event = engine.run_next(gbn)

    assert event is not None
    assert event.event_type == EventType.FRAME_ARRIVAL
    assert engine.current_time == 100


def test_events_are_processed_in_time_order():
    engine = SimulationEngine()

    frame_0 = Frame(sequence_number=0)
    frame_1 = Frame(sequence_number=1)

    engine.schedule_event(
        NetworkEvent(
            time=700,
            event_type=EventType.FRAME_ARRIVAL,
            data=frame_1,
        )
    )

    engine.schedule_event(
        NetworkEvent(
            time=500,
            event_type=EventType.FRAME_ARRIVAL,
            data=frame_0,
        )
    )

    event = engine.next_event()

    assert event.time == 500
    assert event.data.sequence_number == 0
    assert engine.current_time == 500


def test_events_with_same_time_keep_schedule_order():
    engine = SimulationEngine()

    frame_0 = Frame(sequence_number=0)
    frame_1 = Frame(sequence_number=1)
    frame_2 = Frame(sequence_number=2)

    for frame in [frame_0, frame_1, frame_2]:
        engine.schedule_event(
            NetworkEvent(
                time=500,
                event_type=EventType.FRAME_ARRIVAL,
                data=frame,
            )
        )

    assert engine.next_event().data.sequence_number == 0
    assert engine.next_event().data.sequence_number == 1
    assert engine.next_event().data.sequence_number == 2


def test_next_event_updates_simulation_time():
    engine = SimulationEngine()

    engine.schedule_event(
        NetworkEvent(
            time=1000,
            event_type=EventType.TIMEOUT,
            data=None,
        )
    )

    engine.next_event()

    assert engine.current_time == 1000


def test_empty_engine():
    engine = SimulationEngine()

    assert engine.has_events() is False
    assert engine.next_event() is None


def test_reset():
    engine = SimulationEngine()

    engine.schedule_event(
        NetworkEvent(
            time=500,
            event_type=EventType.TIMEOUT,
            data=None,
        )
    )

    engine.next_event()
    engine.reset()

    assert engine.current_time == 0.0
    assert engine.has_events() is False

def test_gbn_complete_simulation_without_loss():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=100,
        frame_loss_probability=0.0,
        ack_loss_probability=0.0,
        random_seed=42,
    )

    gbn = GoBackN(
        engine=engine,
        network=network,
        total_frames=6,
        window_size=3,
        timeout=500,
    )

    gbn.start()

    safety_limit = 100

    for _ in range(safety_limit):
        if gbn.is_complete():
            break

        if not engine.has_events():
            break

        engine.run_next(gbn)

    assert gbn.is_complete()

from protocols import SelectiveRepeat


def test_sr_complete_simulation_without_loss():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=100,
        frame_loss_probability=0.0,
        ack_loss_probability=0.0,
        random_seed=42,
    )

    sr = SelectiveRepeat(
        engine=engine,
        network=network,
        total_frames=6,
        window_size=3,
        timeout=500,
    )

    sr.start()

    safety_limit = 100

    for _ in range(safety_limit):
        if sr.is_complete():
            break

        if not engine.has_events():
            break

        engine.run_next(sr)

    assert sr.is_complete()

def test_gbn_discards_out_of_order_frame_after_loss():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=100,
        frame_loss_probability=0.0,
        ack_loss_probability=0.0,
        random_seed=42,
    )

    gbn = GoBackN(
        engine=engine,
        network=network,
        total_frames=6,
        window_size=4,
        timeout=500,
    )

    gbn.start()

    # Simulate F0 and F1 arriving normally.
    gbn.handle_frame_arrival(gbn.window.frames[0])
    gbn.handle_frame_arrival(gbn.window.frames[1])

    assert gbn.expected_sequence == 2

    # F2 is considered lost.
    # F3 arrives before F2.
    gbn.handle_frame_arrival(gbn.window.frames[3])

    assert (
        gbn.window.frames[3].status
        == FrameStatus.DISCARDED
    )

    # Receiver is still waiting for F2.
    assert gbn.expected_sequence == 2

def test_sr_buffers_out_of_order_frame_after_loss():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=100,
        frame_loss_probability=0.0,
        ack_loss_probability=0.0,
        random_seed=42,
    )

    sr = SelectiveRepeat(
        engine=engine,
        network=network,
        total_frames=6,
        window_size=4,
        timeout=500,
    )

    sr.start()

    sr.handle_frame_arrival(sr.frames[0])
    sr.handle_frame_arrival(sr.frames[1])

    assert sr.receiver_base == 2

    # F2 is lost.
    # F3 arrives first.
    sr.handle_frame_arrival(sr.frames[3])

    assert 3 in sr.receiver_buffer

    # Receiver is waiting for F2.
    assert sr.receiver_base == 2

    assert sr.frames[3].status == FrameStatus.RECEIVED

def test_gbn_retransmits_entire_window_after_timeout():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=100,
        frame_loss_probability=0.0,
        ack_loss_probability=0.0,
        random_seed=42,
    )

    gbn = GoBackN(
        engine=engine,
        network=network,
        total_frames=6,
        window_size=4,
        timeout=500,
    )

    gbn.start()

    gbn.handle_timeout(0)

    assert gbn.retransmission_count == 4

    for sequence in range(4):
        assert (
            gbn.window.frames[sequence]
            .retransmission_count == 1
        )

def test_sr_retransmits_only_lost_frame():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=100,
        frame_loss_probability=0.0,
        ack_loss_probability=0.0,
        random_seed=42,
    )

    sr = SelectiveRepeat(
        engine=engine,
        network=network,
        total_frames=6,
        window_size=4,
        timeout=500,
    )

    sr.start()

    # F2 is the lost frame.
    sr.handle_timeout(2)

    assert sr.retransmission_count == 1

    assert sr.frames[2].retransmission_count == 1

    assert sr.frames[0].retransmission_count == 0
    assert sr.frames[1].retransmission_count == 0
    assert sr.frames[3].retransmission_count == 0

def test_ack_loss_causes_no_ack_event():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=100,
        frame_loss_probability=0.0,
        ack_loss_probability=1.0,
        random_seed=42,
    )

    ack = ACK(sequence_number=0)

    delivered = network.send_ack(ack)

    assert delivered is False

    # No ACK arrival should have been scheduled.
    assert not engine.has_events()

def test_gbn_completes_with_frame_loss():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=100,
        frame_loss_probability=0.2,
        ack_loss_probability=0.0,
        random_seed=42,
    )

    gbn = GoBackN(
        engine=engine,
        network=network,
        total_frames=8,
        window_size=3,
        timeout=500,
    )

    gbn.start()

    safety_limit = 500

    for _ in range(safety_limit):
        if gbn.is_complete():
            break

        if not engine.has_events():
            break

        engine.run_next(gbn)

    assert gbn.is_complete()

def test_sr_completes_with_frame_loss():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=100,
        frame_loss_probability=0.2,
        ack_loss_probability=0.0,
        random_seed=42,
    )

    sr = SelectiveRepeat(
        engine=engine,
        network=network,
        total_frames=8,
        window_size=3,
        timeout=500,
    )

    sr.start()

    safety_limit = 500

    for _ in range(safety_limit):
        if sr.is_complete():
            break

        if not engine.has_events():
            break

        engine.run_next(sr)

    assert sr.is_complete()

def test_controller_step_processes_one_event():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=100,
        frame_loss_probability=0.0,
        ack_loss_probability=0.0,
        random_seed=42,
    )

    gbn = GoBackN(
        engine=engine,
        network=network,
        total_frames=4,
        window_size=2,
        timeout=500,
    )

    controller = SimulationController(
        engine,
        gbn,
    )

    controller.start()

    assert controller.running is True

    event = controller.step()

    assert event is not None
    assert engine.current_time == 100

def test_controller_runs_to_completion():
    engine = SimulationEngine()

    network = NetworkSimulator(
        engine=engine,
        delay=100,
        frame_loss_probability=0.0,
        ack_loss_probability=0.0,
        random_seed=42,
    )

    gbn = GoBackN(
        engine=engine,
        network=network,
        total_frames=5,
        window_size=2,
        timeout=500,
    )

    controller = SimulationController(
        engine,
        gbn,
    )

    controller.run()

    assert gbn.is_complete()
    assert controller.finished is True
