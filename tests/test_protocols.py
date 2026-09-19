from protocols import SlidingWindow
from models import ACK, EventType, NetworkEvent
from network import NetworkSimulator
from simulator import SimulationEngine
from protocols import SlidingWindow, GoBackN, SelectiveRepeat


def test_gbn_initial_state():
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

    assert gbn.window.base == 0
    assert gbn.window.next_sequence == 0
    assert gbn.expected_sequence == 0


def test_gbn_start_sends_window():
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

    assert gbn.window.base == 0
    assert gbn.window.next_sequence == 3

    assert len(engine.event_queue) == 4


def test_initial_window():
    window = SlidingWindow(
        total_frames=7,
        window_size=4
    )

    assert window.base == 0
    assert window.next_sequence == 0

    frames = window.get_window()

    assert [f.sequence_number for f in frames] == [0, 1, 2, 3]


def test_send_frames_until_window_is_full():
    window = SlidingWindow(
        total_frames=7,
        window_size=4
    )

    sent = []

    for _ in range(4):
        frame = window.get_next_frame()
        sent.append(frame.sequence_number)

    assert sent == [0, 1, 2, 3]
    assert window.window_is_full() is True


def test_cumulative_ack_moves_window():
    window = SlidingWindow(
        total_frames=7,
        window_size=4
    )

    for _ in range(4):
        window.get_next_frame()

    window.acknowledge(0)

    assert window.base == 1

    frame = window.get_next_frame()

    assert frame.sequence_number == 4


def test_multiple_acknowledgements_move_window():
    window = SlidingWindow(
        total_frames=7,
        window_size=4
    )

    for _ in range(4):
        window.get_next_frame()

    window.acknowledge(2)

    assert window.base == 3

    frames = window.get_window()

    assert [f.sequence_number for f in frames] == [3, 4, 5, 6]


def test_cannot_ack_unsent_frame():
    window = SlidingWindow(
        total_frames=7,
        window_size=4
    )

    window.get_next_frame()

    window.acknowledge(5)

    assert window.base == 0


def test_simulation_completion():
    window = SlidingWindow(
        total_frames=3,
        window_size=4
    )

    for _ in range(3):
        window.get_next_frame()

    assert window.is_complete() is False

    window.acknowledge(2)

    assert window.is_complete() is True

def test_gbn_receiver_accepts_expected_frame():
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
        window_size=3,
        timeout=500,
    )

    frame = gbn.window.frames[0]

    gbn.handle_frame_arrival(frame)

    assert frame.status.name == "RECEIVED"
    assert gbn.expected_sequence == 1


def test_gbn_discards_out_of_order_frame():
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
        window_size=3,
        timeout=500,
    )

    frame = gbn.window.frames[2]

    gbn.handle_frame_arrival(frame)

    assert frame.status.name == "DISCARDED"
    assert gbn.expected_sequence == 0


def test_gbn_ignores_stale_timeout_after_window_moves():
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
        window_size=3,
        timeout=500,
    )

    gbn.start()
    gbn.handle_ack_arrival(ACK(0))
    gbn.handle_timeout(0)

    assert gbn.window.base == 1
    assert gbn.timeout_count == 0
    assert gbn.retransmission_count == 0

def test_sr_initial_state():
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

    assert sr.base == 0
    assert sr.next_sequence == 0
    assert sr.receiver_base == 0

def test_sr_start_sends_window():
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

    assert sr.base == 0
    assert sr.next_sequence == 3

def test_sr_buffers_out_of_order_frame():
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

    # F0 has not arrived yet.
    # F1 arrives first.
    frame = sr.frames[1]

    sr.handle_frame_arrival(frame)

    assert 1 in sr.receiver_buffer
    assert sr.receiver_base == 0

def test_sr_retransmits_only_timed_out_frame():
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

    # Simulate F1 timeout.
    sr.handle_timeout(1)

    assert sr.timeout_count == 1
    assert sr.retransmission_count == 1

    assert sr.frames[1].retransmission_count == 1
    assert sr.frames[0].retransmission_count == 0
    assert sr.frames[2].retransmission_count == 0

def test_sr_ack_moves_window():
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

    sr.handle_ack_arrival(ACK(0))

    assert sr.base == 1

    sr.handle_ack_arrival(ACK(1))

    assert sr.base == 2
