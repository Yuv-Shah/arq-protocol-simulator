from models import FrameStatus
from network import NetworkSimulator
from protocols import GoBackN
from simulator import SimulationEngine
import stats as stats_


def test_collect_statistics():
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

    # Process simulation.
    for _ in range(100):
        if gbn.is_complete():
            break

        if not engine.has_events():
            break

        engine.run_next(gbn)

    stats = stats_.collect_statistics(
        gbn,
        network,
    )

    assert stats.frames_generated == 4
    assert stats.frames_received == 4
    assert stats.frames_lost == 0
    assert stats.retransmissions == 0
    assert stats.throughput > 0
    assert stats.efficiency > 0