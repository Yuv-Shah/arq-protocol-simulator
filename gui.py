import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from animation import TimelineAnimationScene
from models import EventType, FrameStatus, SimulationConfig
from network import NetworkSimulator
from protocols import GoBackN, SelectiveRepeat
from simulator import SimulationController, SimulationEngine


class ARQSimulatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Go-Back-N & Selective Repeat ARQ Simulator")
        self.resize(1180, 780)

        self.engine = None
        self.network = None
        self.protocol = None
        self.controller = None
        self.config = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.run_simulation_step)

        self.build_ui()

    def build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        config_box = QGroupBox("Simulation Configuration")
        config_layout = QFormLayout()

        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["Go-Back-N", "Selective Repeat"])

        self.frames_spin = QSpinBox()
        self.frames_spin.setRange(1, 100)
        self.frames_spin.setValue(8)

        self.window_spin = QSpinBox()
        self.window_spin.setRange(1, 20)
        self.window_spin.setValue(4)

        self.sequence_bits_spin = QSpinBox()
        self.sequence_bits_spin.setRange(2, 8)
        self.sequence_bits_spin.setValue(3)

        self.frame_loss_spin = QDoubleSpinBox()
        self.frame_loss_spin.setRange(0, 100)
        self.frame_loss_spin.setValue(20)
        self.frame_loss_spin.setSuffix(" %")

        self.ack_loss_spin = QDoubleSpinBox()
        self.ack_loss_spin.setRange(0, 100)
        self.ack_loss_spin.setValue(0)
        self.ack_loss_spin.setSuffix(" %")

        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(10, 5000)
        self.delay_spin.setValue(500)
        self.delay_spin.setSuffix(" ms")

        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(50, 10000)
        self.timeout_spin.setValue(1000)
        self.timeout_spin.setSuffix(" ms")

        config_layout.addRow("Protocol:", self.protocol_combo)
        config_layout.addRow("Total Frames:", self.frames_spin)
        config_layout.addRow("Window Size:", self.window_spin)
        config_layout.addRow("Sequence Bits:", self.sequence_bits_spin)
        config_layout.addRow("Frame Loss:", self.frame_loss_spin)
        config_layout.addRow("ACK Loss:", self.ack_loss_spin)
        config_layout.addRow("Network Delay:", self.delay_spin)
        config_layout.addRow("Timeout:", self.timeout_spin)
        config_box.setLayout(config_layout)

        self.start_button = QPushButton("START")
        self.pause_button = QPushButton("PAUSE")
        self.resume_button = QPushButton("RESUME")
        self.step_button = QPushButton("STEP")
        self.reset_button = QPushButton("RESET")

        self.start_button.clicked.connect(self.start_simulation)
        self.pause_button.clicked.connect(self.pause_simulation)
        self.resume_button.clicked.connect(self.resume_simulation)
        self.step_button.clicked.connect(self.step_simulation)
        self.reset_button.clicked.connect(self.reset_simulation)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.resume_button)
        button_layout.addWidget(self.step_button)
        button_layout.addWidget(self.reset_button)

        status_box = QGroupBox("Simulation Status")
        status_layout = QVBoxLayout()

        self.time_label = QLabel("Simulation Time: 0 ms")
        self.status_label = QLabel("Status: Ready")
        self.sender_label = QLabel("Sender Window: []")
        self.receiver_label = QLabel("Receiver: Waiting")

        status_layout.addWidget(self.time_label)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.sender_label)
        status_layout.addWidget(self.receiver_label)
        status_box.setLayout(status_layout)

        visualization_box = QGroupBox("ARQ Timeline Animation")
        visualization_layout = QVBoxLayout()

        self.timeline_scene = TimelineAnimationScene()
        self.graphics_view = QGraphicsView(self.timeline_scene)
        self.graphics_view.setMinimumHeight(430)
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        visualization_layout.addWidget(self.graphics_view)
        visualization_box.setLayout(visualization_layout)

        top_layout = QHBoxLayout()
        top_layout.addWidget(config_box, 2)
        top_layout.addWidget(status_box, 3)

        main_layout.addLayout(top_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(visualization_box, 1)

    def create_simulation(self) -> None:
        self.config = SimulationConfig(
            total_frames=self.frames_spin.value(),
            window_size=self.window_spin.value(),
            sequence_bits=self.sequence_bits_spin.value(),
            frame_loss_probability=self.frame_loss_spin.value() / 100,
            ack_loss_probability=self.ack_loss_spin.value() / 100,
            network_delay=self.delay_spin.value(),
            timeout=self.timeout_spin.value(),
            random_seed=42,
        )

        self.engine = SimulationEngine()
        self.network = NetworkSimulator(
            engine=self.engine,
            delay=self.config.network_delay,
            frame_loss_probability=self.config.frame_loss_probability,
            ack_loss_probability=self.config.ack_loss_probability,
            random_seed=self.config.random_seed,
        )
        self.install_network_visual_hooks()

        if self.protocol_combo.currentText() == "Go-Back-N":
            self.protocol = GoBackN(
                engine=self.engine,
                network=self.network,
                total_frames=self.config.total_frames,
                window_size=self.config.window_size,
                timeout=self.config.timeout,
            )
        else:
            self.protocol = SelectiveRepeat(
                engine=self.engine,
                network=self.network,
                total_frames=self.config.total_frames,
                window_size=self.config.window_size,
                timeout=self.config.timeout,
            )

        self.controller = SimulationController(self.engine, self.protocol)

    def install_network_visual_hooks(self) -> None:
        original_send_frame = self.network.send_frame
        original_send_ack = self.network.send_ack

        def send_frame_with_visual(frame):
            retransmission = frame.retransmission_count > 0
            delivered = original_send_frame(frame)

            if delivered:
                self.timeline_scene.draw_frame(
                    frame.sequence_number,
                    retransmission=retransmission,
                )
            else:
                self.timeline_scene.draw_lost_frame(
                    frame.sequence_number,
                    retransmission=retransmission,
                )

            return delivered

        def send_ack_with_visual(ack):
            duplicate = self.is_duplicate_ack(ack.sequence_number)
            delivered = original_send_ack(ack)

            if delivered:
                self.timeline_scene.draw_ack(
                    ack.sequence_number,
                    duplicate=duplicate,
                )
            else:
                self.timeline_scene.draw_lost_ack(
                    ack.sequence_number,
                    duplicate=duplicate,
                )

            return delivered

        self.network.send_frame = send_frame_with_visual
        self.network.send_ack = send_ack_with_visual

    def is_duplicate_ack(self, sequence_number: int) -> bool:
        if isinstance(self.protocol, GoBackN):
            return sequence_number < self.protocol.expected_sequence - 1

        if isinstance(self.protocol, SelectiveRepeat):
            return sequence_number < self.protocol.receiver_base

        return False

    def start_simulation(self) -> None:
        self.timer.stop()
        self.create_simulation()
        self.timeline_scene.reset_timeline(
            protocol_name=self.protocol_combo.currentText(),
            total_frames=self.config.total_frames,
            window_size=self.config.window_size,
        )

        self.controller.start()
        self.controller.running = True
        self.controller.finished = False

        self.status_label.setText("Status: Running")
        self.timer.start(700)
        self.update_display()

    def pause_simulation(self) -> None:
        if self.controller:
            self.controller.pause()

        self.timer.stop()
        self.status_label.setText("Status: Paused")

    def resume_simulation(self) -> None:
        if not self.controller or self.controller.finished:
            return

        self.controller.resume()
        self.timer.start(700)
        self.status_label.setText("Status: Running")

    def step_simulation(self) -> None:
        if self.controller is None:
            self.create_simulation()
            self.timeline_scene.reset_timeline(
                protocol_name=self.protocol_combo.currentText(),
                total_frames=self.config.total_frames,
                window_size=self.config.window_size,
            )
            self.controller.start()
            self.controller.running = True
            self.controller.finished = False

        self.timer.stop()
        self.run_one_event()

    def run_simulation_step(self) -> None:
        if self.controller is None:
            return

        self.run_one_event()

    def run_one_event(self) -> None:
        if self.controller.finished:
            return

        event = self.engine.next_event()
        if event is None:
            self.finish_simulation()
            return

        timeout_count_before = getattr(self.protocol, "timeout_count", 0)
        self.protocol.process_event(event)
        self.describe_event_after_processing(event, timeout_count_before)

        if self.protocol.is_complete():
            self.finish_simulation()

        self.update_display()

    def describe_event_after_processing(self, event, timeout_count_before: int) -> None:
        if event.event_type == EventType.FRAME_ARRIVAL:
            self.describe_frame_arrival(event.data)
        elif event.event_type == EventType.ACK_ARRIVAL:
            self.describe_ack_arrival(event.data)
        elif event.event_type == EventType.TIMEOUT:
            self.describe_timeout(event.data, timeout_count_before)

    def describe_timeout(self, sequence_number: int, timeout_count_before: int) -> None:
        timeout_count_after = getattr(self.protocol, "timeout_count", 0)
        if timeout_count_after > timeout_count_before:
            self.timeline_scene.draw_timeout(sequence_number)

    def describe_frame_arrival(self, frame) -> None:
        sequence = frame.sequence_number

        if isinstance(self.protocol, GoBackN):
            if frame.status == FrameStatus.RECEIVED:
                self.timeline_scene.draw_delivered_frame(sequence)
            elif frame.status == FrameStatus.DISCARDED:
                self.timeline_scene.draw_discarded_frame(sequence)

        elif isinstance(self.protocol, SelectiveRepeat):
            if sequence in self.protocol.receiver_buffer:
                self.timeline_scene.draw_buffered_frame(sequence)
            elif frame.status == FrameStatus.RECEIVED:
                self.timeline_scene.draw_delivered_frame(sequence)
            elif frame.status == FrameStatus.DISCARDED:
                self.timeline_scene.draw_discarded_frame(sequence)

    def describe_ack_arrival(self, ack) -> None:
        sequence = ack.sequence_number

        if isinstance(self.protocol, GoBackN):
            if sequence < self.protocol.window.base - 1:
                self.timeline_scene.draw_duplicate_ack(sequence)
            else:
                self.timeline_scene.draw_sender_note(
                    f"rcv ack{sequence}, send next if window opens",
                    "#111827",
                )

        elif isinstance(self.protocol, SelectiveRepeat):
            self.timeline_scene.draw_sender_note(
                f"rcv ack{sequence}, mark pkt{sequence} complete",
                "#111827",
            )

    def finish_simulation(self) -> None:
        self.timer.stop()
        self.controller.running = False
        self.controller.finished = True
        self.status_label.setText("Status: Finished")

    def reset_simulation(self) -> None:
        self.timer.stop()

        if self.controller:
            self.controller.reset()

        self.engine = None
        self.network = None
        self.protocol = None
        self.controller = None
        self.config = None

        self.timeline_scene.reset_timeline(
            protocol_name=self.protocol_combo.currentText(),
            total_frames=self.frames_spin.value(),
            window_size=self.window_spin.value(),
        )

        self.time_label.setText("Simulation Time: 0 ms")
        self.status_label.setText("Status: Ready")
        self.sender_label.setText("Sender Window: []")
        self.receiver_label.setText("Receiver: Waiting")

    def update_display(self) -> None:
        if not self.protocol:
            return

        self.time_label.setText(
            f"Simulation Time: {self.engine.current_time:.0f} ms"
        )

        if isinstance(self.protocol, GoBackN):
            base = self.protocol.window.base
            next_sequence = self.protocol.window.next_sequence
            window = self.protocol.window.get_window()
            window_text = " ".join(
                f"[{frame.sequence_number}]"
                for frame in window
            )

            self.sender_label.setText(
                f"Sender Window: Base={base}, Next={next_sequence}    {window_text}"
            )
            self.receiver_label.setText(
                f"Receiver: Expected pkt{self.protocol.expected_sequence}"
            )
            self.timeline_scene.draw_sender_window(
                base,
                next_sequence,
                "window slides",
            )

        elif isinstance(self.protocol, SelectiveRepeat):
            base = self.protocol.base
            next_sequence = self.protocol.next_sequence
            window = self.protocol.frames[
                base:min(base + self.protocol.window_size, self.protocol.total_frames)
            ]
            window_text = " ".join(
                f"[{frame.sequence_number}]"
                for frame in window
            )
            buffered = sorted(self.protocol.receiver_buffer.keys())

            self.sender_label.setText(
                f"Sender Window: Base={base}, Next={next_sequence}    {window_text}"
            )
            self.receiver_label.setText(
                f"Receiver: Base={self.protocol.receiver_base}, Buffered={buffered}"
            )
            self.timeline_scene.draw_sender_window(
                base,
                next_sequence,
                "window slides",
            )


def run_gui() -> None:
    app = QApplication(sys.argv)
    window = ARQSimulatorWindow()
    window.show()
    sys.exit(app.exec())
