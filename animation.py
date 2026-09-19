from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainterPath, QPen, QBrush, QPolygonF
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsPolygonItem,
    QGraphicsRectItem,
    QGraphicsScene,
)


class TimelineAnimationScene(QGraphicsScene):
    """Textbook-style ARQ timeline scene."""

    WINDOW_X = 55
    SENDER_X = 360
    RECEIVER_X = 730
    NOTE_X = 780
    START_Y = 100
    ROW_HEIGHT = 34
    SCENE_WIDTH = 1080
    SCENE_HEIGHT = 1600

    def __init__(self):
        super().__init__(0, 0, self.SCENE_WIDTH, self.SCENE_HEIGHT)
        self.current_row = 0
        self.protocol_name = "Go-Back-N"
        self.total_frames = 8
        self.window_size = 4
        self.draw_static_layout()

    def reset_timeline(
        self,
        protocol_name: str = "Go-Back-N",
        total_frames: int = 8,
        window_size: int = 4,
    ) -> None:
        self.protocol_name = protocol_name
        self.total_frames = total_frames
        self.window_size = window_size
        self.draw_static_layout()

    def draw_static_layout(self) -> None:
        self.clear()
        self.current_row = 0
        self.setBackgroundBrush(QBrush(QColor("#FFFFFF")))

        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)

        title = self.addText(f"{self.protocol_name} in action", title_font)
        title.setDefaultTextColor(QColor("#1D4ED8"))
        title.setPos(20, 12)

        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setItalic(True)

        sender_window = self.addText(
            f"sender window (N={self.window_size})",
            header_font,
        )
        sender_window.setDefaultTextColor(QColor("#3730A3"))
        sender_window.setPos(self.WINDOW_X, 60)

        sender = self.addText("sender", header_font)
        sender.setDefaultTextColor(QColor("#1E3A8A"))
        sender.setPos(self.SENDER_X - 35, 60)

        receiver = self.addText("receiver", header_font)
        receiver.setDefaultTextColor(QColor("#15803D"))
        receiver.setPos(self.RECEIVER_X - 35, 60)

        lane_pen = QPen(QColor("#9CA3AF"))
        lane_pen.setWidth(2)

        self.addLine(
            self.SENDER_X,
            self.START_Y - 15,
            self.SENDER_X,
            self.SCENE_HEIGHT - 40,
            lane_pen,
        )
        self.addLine(
            self.RECEIVER_X,
            self.START_Y - 15,
            self.RECEIVER_X,
            self.SCENE_HEIGHT - 40,
            lane_pen,
        )

        self.draw_sender_window(0, 0, "initial window")

    def next_y(self) -> int:
        y = self.START_Y + self.current_row * self.ROW_HEIGHT
        self.current_row += 1
        if y > self.sceneRect().height() - 80:
            self.setSceneRect(
                0,
                0,
                self.SCENE_WIDTH,
                self.sceneRect().height() + 600,
            )
        return y

    def text(self, value, x, y, color="#111827", size=9, bold=False):
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)

        item = self.addText(str(value), font)
        item.setDefaultTextColor(QColor(color))
        item.setPos(x, y)
        return item

    def add_arrow_head(self, x, y, direction="right", color="#1D4ED8") -> None:
        polygon = QPolygonF()

        if direction == "right":
            polygon.append(QPointF(x, y))
            polygon.append(QPointF(x - 11, y - 6))
            polygon.append(QPointF(x - 11, y + 6))
        else:
            polygon.append(QPointF(x, y))
            polygon.append(QPointF(x + 11, y - 6))
            polygon.append(QPointF(x + 11, y + 6))

        head = QGraphicsPolygonItem(polygon)
        head.setBrush(QBrush(QColor(color)))
        head.setPen(QPen(QColor(color)))
        self.addItem(head)

    def draw_sender_window(self, base: int, next_sequence: int, note: str = "") -> None:
        y = self.START_Y + self.current_row * self.ROW_HEIGHT - 22
        box_size = 18
        max_frames = min(self.total_frames, 12)

        self.text(f"{base}", self.WINDOW_X - 18, y - 1, "#6B7280", 8)

        for index in range(max_frames):
            x = self.WINDOW_X + index * box_size
            in_window = base <= index < min(base + self.window_size, self.total_frames)
            sent = index < next_sequence

            rect = QGraphicsRectItem(x, y, box_size - 1, 17)
            if in_window:
                rect.setBrush(QBrush(QColor("#1D4ED8")))
                rect.setPen(QPen(QColor("#1E40AF")))
                color = "#FFFFFF"
            elif sent:
                rect.setBrush(QBrush(QColor("#DBEAFE")))
                rect.setPen(QPen(QColor("#93C5FD")))
                color = "#1E3A8A"
            else:
                rect.setBrush(QBrush(QColor("#FFFFFF")))
                rect.setPen(QPen(QColor("#D1D5DB")))
                color = "#111827"

            self.addItem(rect)
            self.text(index, x + 5, y - 3, color, 8, in_window)

        if self.total_frames > max_frames:
            self.text("...", self.WINDOW_X + max_frames * box_size + 4, y - 2)

        if note:
            self.text(note, self.WINDOW_X, y + 16, "#4B5563", 8)

    def draw_line_arrow(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        color: str,
        dashed: bool = False,
    ) -> None:
        pen = QPen(QColor(color))
        pen.setWidth(2)
        if dashed:
            pen.setStyle(Qt.DashLine)

        path = QPainterPath(QPointF(start_x, start_y))
        path.lineTo(end_x, end_y)
        self.addPath(path, pen)
        direction = "right" if end_x > start_x else "left"
        self.add_arrow_head(end_x, end_y, direction, color)

    def draw_frame(self, sequence_number: int, retransmission: bool = False) -> None:
        y = self.next_y()
        color = "#7C3AED" if retransmission else "#1D4ED8"
        label = "resend" if retransmission else "send"

        self.text(f"{label} pkt{sequence_number}", self.SENDER_X - 105, y - 17)
        self.draw_line_arrow(
            self.SENDER_X,
            y,
            self.RECEIVER_X,
            y + 22,
            color,
        )
        self.text(f"pkt{sequence_number}", self.SENDER_X + 16, y - 18, color, 9, True)

    def draw_lost_frame(self, sequence_number: int, retransmission: bool = False) -> None:
        y = self.next_y()
        color = "#DC2626"
        label = "resend" if retransmission else "send"
        mid_x = (self.SENDER_X + self.RECEIVER_X) // 2

        self.text(f"{label} pkt{sequence_number}", self.SENDER_X - 105, y - 17)
        self.draw_line_arrow(
            self.SENDER_X,
            y,
            mid_x,
            y + 11,
            color,
            dashed=True,
        )

        x_pen = QPen(QColor(color))
        x_pen.setWidth(3)
        self.addLine(mid_x + 8, y + 2, mid_x + 24, y + 18, x_pen)
        self.addLine(mid_x + 8, y + 18, mid_x + 24, y + 2, x_pen)
        self.text("loss", mid_x + 28, y - 14, color, 9, True)

    def draw_ack(self, sequence_number: int, duplicate: bool = False) -> None:
        y = self.next_y()
        color = "#16A34A"
        label = f"send ack{sequence_number}"
        if duplicate:
            label = f"(re)send ack{sequence_number}"

        self.text(label, self.NOTE_X, y - 17, color)
        self.draw_line_arrow(
            self.RECEIVER_X,
            y,
            self.SENDER_X,
            y + 22,
            color,
            dashed=duplicate,
        )
        self.text(f"ack{sequence_number}", self.RECEIVER_X - 85, y - 18, color, 9, True)

    def draw_lost_ack(self, sequence_number: int, duplicate: bool = False) -> None:
        y = self.next_y()
        color = "#EA580C"
        mid_x = (self.SENDER_X + self.RECEIVER_X) // 2
        label = f"send ack{sequence_number}"
        if duplicate:
            label = f"(re)send ack{sequence_number}"

        self.text(label, self.NOTE_X, y - 17, color)
        self.draw_line_arrow(
            self.RECEIVER_X,
            y,
            mid_x,
            y + 11,
            color,
            dashed=True,
        )

        x_pen = QPen(QColor(color))
        x_pen.setWidth(3)
        self.addLine(mid_x - 22, y + 2, mid_x - 6, y + 18, x_pen)
        self.addLine(mid_x - 22, y + 18, mid_x - 6, y + 2, x_pen)
        self.text("ack loss", mid_x - 78, y - 14, color, 9, True)

    def draw_timeout(self, sequence_number: int) -> None:
        y = self.next_y()
        color = "#DC2626"

        clock = QGraphicsEllipseItem(self.SENDER_X - 135, y - 14, 24, 24)
        clock.setBrush(QBrush(QColor("#FEE2E2")))
        clock.setPen(QPen(QColor(color), 2))
        self.addItem(clock)
        self.text("!", self.SENDER_X - 127, y - 16, color, 11, True)
        self.text(f"pkt {sequence_number} timeout", self.SENDER_X - 105, y - 18, color, 10, True)

    def draw_receiver_note(self, text: str, color: str = "#111827") -> None:
        y = self.next_y()
        self.text(text, self.NOTE_X, y - 18, color, 9)

    def draw_sender_note(self, text: str, color: str = "#111827") -> None:
        y = self.next_y()
        self.text(text, self.SENDER_X - 170, y - 18, color, 9)

    def draw_discarded_frame(self, sequence_number: int) -> None:
        self.draw_receiver_note(
            f"receive pkt{sequence_number}, discard",
            "#6B7280",
        )

    def draw_buffered_frame(self, sequence_number: int) -> None:
        self.draw_receiver_note(
            f"receive pkt{sequence_number}, buffer",
            "#D97706",
        )

    def draw_delivered_frame(self, sequence_number: int) -> None:
        self.draw_receiver_note(
            f"receive pkt{sequence_number}, deliver",
            "#15803D",
        )

    def draw_duplicate_ack(self, sequence_number: int) -> None:
        self.draw_sender_note(
            f"ignore duplicate ack{sequence_number}",
            "#6B7280",
        )
