from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QHBoxLayout,
    QSizePolicy,
    QWidget,
)

from pygoban import Color, results
from pygoban.gui.boxes import Box


class DiagramCanvas(QWidget):

    def __init__(self, parent) -> None:
        self.diagram = parent
        self.last_turn: results.TurnDone | None = None
        self.results: list[dict] = []
        super().__init__(parent=parent)

    def paintEvent(self, _event) -> None:
        if not self.last_turn:
            return
        painter = QPainter()
        painter.begin(self)
        width = self.size().width()
        height = self.size().height()

        painter.setBackground(self.palette().window().color())

        node = self.last_turn.node
        num_turns = len(self.results)
        while node.children:
            num_turns += 1
            node = node.children[-1]

        block = width // (num_turns or 1) or 1
        onepc = height / 100
        painter.fillRect(0, 0, width, int(onepc * 50), QColor(255, 255, 255, 100))
        painter.fillRect(0, int(onepc * 50), width, int(onepc * 50), QColor(0, 0, 0, 100))
        painter.setBrush(self.palette().text().color())
        for index in range(10, 100, 10):
            text_pos = int(onepc * index)
            painter.drawText(QRect(0, text_pos - 5, 18, 10),
                             Qt.AlignmentFlag.AlignCenter, f"{100 - index}")

        last_percent: int | None = None
        for index, result in enumerate(self.results):
            percent = int(float(result["percent"]))
            if index % 2 == 1:
                percent = 100 - percent
            if last_percent:

                painter.drawLine(
                    QPoint(block * (index - 1), int(last_percent * onepc)),
                    QPoint(block * index, int(percent * onepc))
                )
            last_percent = percent


class DiagramBox(Box):
    name = "Diagram"

    def init(self, **kwargs):
        layout = QHBoxLayout()
        self.events = {results.AnnotationDone, results.TurnDone}
        self.canvas = DiagramCanvas(parent=self)

        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.canvas)

        self.setMaximumHeight(200)
        self.setLayout(layout)

    def received_annotated(self, result: results.AnnotationDone) -> None:
        last_turn = self.canvas.last_turn
        assert last_turn
        self.canvas.results.clear()
        for pathnode in last_turn.node._full_path():
            if not pathnode.annos.winrates:
                continue
            percent, num = list(pathnode.annos.winrates.values())[0][0:2]

            self.canvas.results.append({"percent": percent, "num": num})
        self.canvas.update()

    def received_turn(self, result: results.TurnDone) -> None:
        self.canvas.last_turn = result
