from dataclasses import dataclass


@dataclass
class SimulationStatistics:
    frames_generated: int = 0
    frames_sent: int = 0
    frames_received: int = 0
    frames_lost: int = 0
    frames_discarded: int = 0

    acks_sent: int = 0
    acks_received: int = 0
    acks_lost: int = 0

    retransmissions: int = 0
    timeouts: int = 0

    simulation_time: float = 0.0
    throughput: float = 0.0
    efficiency: float = 0.0

    def calculate(
        self,
        total_frames: int,
        simulation_time: float,
    ) -> None:
        """
        Calculate throughput and efficiency.

        simulation_time is in milliseconds.
        """

        self.frames_generated = total_frames
        self.simulation_time = simulation_time

        # Convert milliseconds to seconds.
        seconds = simulation_time / 1000.0

        if seconds > 0:
            self.throughput = (
                self.frames_received / seconds
            )
        else:
            self.throughput = 0.0

        if self.frames_sent > 0:
            self.efficiency = (
                self.frames_received
                / self.frames_sent
            )
        else:
            self.efficiency = 0.0

def collect_statistics(protocol, network) -> SimulationStatistics:
        """
        Build a statistics object from the
        current protocol and network state.
        """

        stats = SimulationStatistics()

        if hasattr(protocol, "total_frames"):
            total_frames = protocol.total_frames
        else:
            total_frames = protocol.window.total_frames

        stats.frames_generated = total_frames

        stats.frames_sent = network.frames_sent
        stats.frames_lost = network.frames_lost

        stats.acks_sent = network.acks_sent
        stats.acks_lost = network.acks_lost

        stats.retransmissions = (
            protocol.retransmission_count
        )

        stats.timeouts = protocol.timeout_count

        # Count actual receiver results.
        if hasattr(protocol, "frames"):
            frames = protocol.frames
        else:
            frames = protocol.window.frames

        stats.frames_received = sum(
            1
            for frame in frames
            if frame.status.name in ("RECEIVED", "ACKED")
        )

        stats.frames_discarded = sum(
            1
            for frame in frames
            if frame.status.name == "DISCARDED"
        )

        stats.acks_received = (
            stats.acks_sent - stats.acks_lost
        )

        stats.calculate(
            total_frames=total_frames,
            simulation_time=protocol.engine.current_time,
        )

        return stats
