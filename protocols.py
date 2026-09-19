from models import (
    Frame,
    FrameStatus,
    ACK,
    EventType,
    NetworkEvent,
)
from simulator import SimulationEngine
from network import NetworkSimulator


class SlidingWindow:
    """
    Basic sender-side sliding window.

    Used as a foundation for the ARQ protocols.
    """

    def __init__(self, total_frames: int, window_size: int):
        self.total_frames = total_frames
        self.window_size = window_size

        self.base = 0
        self.next_sequence = 0

        self.frames = [
            Frame(sequence_number=i)
            for i in range(total_frames)
        ]

    def window_is_full(self) -> bool:
        return self.next_sequence >= self.base + self.window_size

    def has_frames_to_send(self) -> bool:
        return self.next_sequence < self.total_frames

    def get_window(self) -> list[Frame]:
        end = min(
            self.base + self.window_size,
            self.total_frames
        )

        return self.frames[self.base:end]

    def get_next_frame(self) -> Frame | None:
        if self.window_is_full():
            return None

        if not self.has_frames_to_send():
            return None

        frame = self.frames[self.next_sequence]
        self.next_sequence += 1

        return frame

    def acknowledge(self, sequence_number: int) -> None:
        if sequence_number < self.base:
            return

        if sequence_number >= self.next_sequence:
            return

        self.base = sequence_number + 1

    def is_complete(self) -> bool:
        return self.base >= self.total_frames


class GoBackN:
    """
    Go-Back-N ARQ protocol.

    Handles:
    - Sender sliding window
    - Receiver expected sequence number
    - Cumulative ACKs
    - Timeout of oldest unacknowledged frame
    - Retransmission of all outstanding frames
    """

    def __init__(
        self,
        engine: SimulationEngine,
        network: NetworkSimulator,
        total_frames: int,
        window_size: int,
        timeout: float,
    ):
        self.engine = engine
        self.network = network

        self.window = SlidingWindow(
            total_frames=total_frames,
            window_size=window_size,
        )

        # Receiver expects this frame next.
        self.expected_sequence = 0

        self.timeout = timeout

        # Number of timeout events.
        self.timeout_count = 0

        # Number of retransmitted frames.
        self.retransmission_count = 0

    def start(self) -> None:
        """
        Start the GBN transmission by filling
        the sender window.
        """
        self.send_new_frames()

    def send_new_frames(self) -> None:
        """
        Send new frames while there is space
        in the sender window.
        """
        while True:
            frame = self.window.get_next_frame()

            if frame is None:
                break

            self.send_frame(frame)

        self.schedule_timeout()

    def send_frame(
        self,
        frame: Frame,
        retransmission: bool = False,
    ) -> None:
        """
        Send a frame through the simulated network.
        """

        frame.status = (
            FrameStatus.RETRANSMITTING
            if retransmission
            else FrameStatus.IN_FLIGHT
        )

        frame.sent_time = self.engine.current_time

        if retransmission:
            frame.retransmission_count += 1
            self.retransmission_count += 1

        self.network.send_frame(frame)

    def schedule_timeout(self) -> None:
        """
        Schedule a timeout for the oldest
        unacknowledged frame.
        """

        if self.window.base >= self.window.next_sequence:
            return

        timeout_event = NetworkEvent(
            time=self.engine.current_time + self.timeout,
            event_type=EventType.TIMEOUT,
            data=self.window.base,
        )

        self.engine.schedule_event(timeout_event)

    def process_event(self, event: NetworkEvent) -> None:
        """
        Process one simulation event.
        """

        if event.event_type == EventType.FRAME_ARRIVAL:
            self.handle_frame_arrival(event.data)

        elif event.event_type == EventType.ACK_ARRIVAL:
            self.handle_ack_arrival(event.data)

        elif event.event_type == EventType.TIMEOUT:
            self.handle_timeout(event.data)

    def handle_frame_arrival(self, frame: Frame) -> None:
        """
        Receiver-side GBN behavior.

        Accept the frame only if it is the frame
        currently expected.
        """

        if frame.sequence_number == self.expected_sequence:

            frame.status = FrameStatus.RECEIVED

            self.expected_sequence += 1

            # Cumulative ACK for the frame received.
            ack = ACK(
                sequence_number=frame.sequence_number
            )

            self.network.send_ack(ack)

        else:
            # Out-of-order frame is discarded.
            frame.status = FrameStatus.DISCARDED

            # Send duplicate cumulative ACK for the
            # last correctly received frame.
            if self.expected_sequence > 0:
                ack = ACK(
                    sequence_number=self.expected_sequence - 1
                )

                self.network.send_ack(ack)

    def handle_ack_arrival(self, ack: ACK) -> None:
        """
        Process a cumulative ACK.

        ACK N means that frames up to N
        have been received correctly.
        """

        if ack.sequence_number < self.window.base:
            # Duplicate/old ACK.
            return

        if ack.sequence_number >= self.window.next_sequence:
            # ACK for a frame that has not been sent.
            return

        # Move sender window.
        self.window.acknowledge(
            ack.sequence_number
        )

        # Send additional frames if the window has opened.
        self.send_new_frames()

    def handle_timeout(self, sequence_number: int) -> None:
        """
        Retransmit all outstanding frames when
        the oldest unacknowledged frame times out.
        """

        # Ignore stale timeout events.
        if sequence_number != self.window.base:
            return

        self.timeout_count += 1

        # Retransmit every outstanding frame.
        for sequence in range(
            self.window.base,
            self.window.next_sequence,
        ):
            frame = self.window.frames[sequence]

            self.send_frame(
                frame,
                retransmission=True,
            )

        # Start a new timer for the oldest frame.
        self.schedule_timeout()

    def is_complete(self) -> bool:
        """
        Return True when every frame has been
        cumulatively acknowledged.
        """
        return self.window.is_complete()


class SelectiveRepeat:
    """
    Selective Repeat ARQ protocol.

    Supports:
    - Sender sliding window
    - Receiver sliding window
    - Individual ACKs
    - Out-of-order frame buffering
    - Individual frame timeouts
    - Individual retransmissions
    """

    def __init__(
        self,
        engine: SimulationEngine,
        network: NetworkSimulator,
        total_frames: int,
        window_size: int,
        timeout: float,
    ):
        self.engine = engine
        self.network = network

        self.total_frames = total_frames
        self.window_size = window_size
        self.timeout = timeout

        self.frames = [
            Frame(sequence_number=i)
            for i in range(total_frames)
        ]

        # Sender state
        self.base = 0
        self.next_sequence = 0

        # ACK status for every frame
        self.acknowledged = [
            False
            for _ in range(total_frames)
        ]

        # Receiver state
        self.receiver_base = 0

        self.receiver_buffer = {}

        # Statistics useful for protocol testing.
        self.timeout_count = 0
        self.retransmission_count = 0

    def start(self) -> None:
        """
        Start transmission by filling the sender window.
        """
        self.send_new_frames()

    def window_is_full(self) -> bool:
        return (
            self.next_sequence
            >= self.base + self.window_size
        )

    def send_new_frames(self) -> None:
        """
        Send new frames while space exists
        in the sender window.
        """

        while (
            self.next_sequence < self.total_frames
            and not self.window_is_full()
        ):
            frame = self.frames[self.next_sequence]

            self.send_frame(frame)

            self.next_sequence += 1

    def send_frame(
        self,
        frame: Frame,
        retransmission: bool = False,
    ) -> None:
        """
        Send one frame through the simulated network.
        """

        if retransmission:
            frame.status = FrameStatus.RETRANSMITTING
            frame.retransmission_count += 1
            self.retransmission_count += 1
        else:
            frame.status = FrameStatus.IN_FLIGHT

        frame.sent_time = self.engine.current_time

        self.network.send_frame(frame)

        # Each frame has its own timer.
        timeout_event = NetworkEvent(
            time=self.engine.current_time + self.timeout,
            event_type=EventType.TIMEOUT,
            data=frame.sequence_number,
        )

        self.engine.schedule_event(timeout_event)

    def process_event(self, event: NetworkEvent) -> None:
        """
        Process one simulation event.
        """

        if event.event_type == EventType.FRAME_ARRIVAL:
            self.handle_frame_arrival(event.data)

        elif event.event_type == EventType.ACK_ARRIVAL:
            self.handle_ack_arrival(event.data)

        elif event.event_type == EventType.TIMEOUT:
            self.handle_timeout(event.data)

    def handle_frame_arrival(self, frame: Frame) -> None:
        """
        Receiver-side Selective Repeat behavior.

        Frames inside the receiver window are accepted
        even when they arrive out of order.
        """

        sequence = frame.sequence_number

        # Frame is inside the current receiver window.
        if (
            self.receiver_base
            <= sequence
            < self.receiver_base + self.window_size
        ):

            # Accept and buffer the frame.
            if sequence not in self.receiver_buffer:
                self.receiver_buffer[sequence] = frame

                frame.status = FrameStatus.RECEIVED

            # ACK this individual frame.
            ack = ACK(sequence_number=sequence)
            self.network.send_ack(ack)

            self.deliver_buffered_frames()

        # Already received frame.
        elif sequence < self.receiver_base:

            # Send ACK again because the sender may have
            # missed the original ACK.
            ack = ACK(sequence_number=sequence)
            self.network.send_ack(ack)

        else:
            # Frame is outside the receiver window.
            frame.status = FrameStatus.DISCARDED

    def deliver_buffered_frames(self) -> None:
        """
        Deliver consecutive buffered frames starting
        from receiver_base.
        """

        while self.receiver_base in self.receiver_buffer:

            del self.receiver_buffer[
                self.receiver_base
            ]

            self.receiver_base += 1

    def handle_ack_arrival(self, ack: ACK) -> None:
        """
        Process an individual ACK.
        """

        sequence = ack.sequence_number

        if sequence < 0:
            return

        if sequence >= self.total_frames:
            return

        # Ignore duplicate ACKs.
        if self.acknowledged[sequence]:
            return

        self.acknowledged[sequence] = True

        self.frames[sequence].status = FrameStatus.ACKED

        # Slide sender window forward over
        # consecutively acknowledged frames.
        while (
            self.base < self.total_frames
            and self.acknowledged[self.base]
        ):
            self.base += 1

        # Send new frames after the window moves.
        self.send_new_frames()

    def handle_timeout(self, sequence_number: int) -> None:
        """
        Retransmit only the frame whose timer expired.
        """

        if sequence_number < 0:
            return

        if sequence_number >= self.total_frames:
            return

        # Ignore timeout for an already acknowledged frame.
        if self.acknowledged[sequence_number]:
            return

        # Ignore timeout for a frame that has not been sent.
        if sequence_number >= self.next_sequence:
            return

        self.timeout_count += 1

        frame = self.frames[sequence_number]

        self.send_frame(
            frame,
            retransmission=True,
        )

    def is_complete(self) -> bool:
        """
        Return True when all frames are acknowledged.
        """
        return self.base >= self.total_frames