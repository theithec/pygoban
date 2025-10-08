# pylint: disable=invalid-name  # bedause qt
from PyQt6.QtCore import QEvent, QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QIcon
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pygoban import results
from pygoban.gui import BASE_DIR
from pygoban.gui.boxes import Box


class DiagramCanvas(QWidget):
    def __init__(self, parent) -> None:
        self.diagram: "DiagramBox" = parent
        self.last_turn: results.TurnDone | None = None
        self.results: list[dict] = []
        self._hover: int | None = None
        self._block: int | None = None
        super().__init__(parent=parent)
        self._left = 20
        self.setMouseTracking(True)
        self.installEventFilter(self)

    def paintEvent(self, _event) -> None:
        if not self.last_turn:
            return
        painter = QPainter()
        painter.begin(self)
        width = self.size().width()
        height = self.size().height()
        fontsize = 10
        painter.setBackground(self.palette().window().color())

        node = self.last_turn.node
        num_turns = len(node.full_path_to_last())
        block = (width - self._left) // (num_turns or 1) or 1
        self._block = block
        onepc = height / 100
        painter.fillRect(0, 0, width, int(onepc * 50), QColor(255, 255, 255, 100))
        painter.fillRect(
            0, int(onepc * 50), width, int(onepc * 50), QColor(0, 0, 0, 100)
        )
        text_color = self.palette().text().color()
        painter.setBrush(text_color)
        last_num: int | None = None
        last_percent: int | None = None
        biggest = int(max([val["num"] for val in self.results] + [10]))
        painter.setPen(text_color)
        painter.drawText(
            QRect(0, 0, self._left, fontsize),
            Qt.AlignmentFlag.AlignCenter,
            f"{biggest}",
        )
        painter.drawText(
            QRect(0, int(onepc * 50) - fontsize // 2, self._left, fontsize),
            Qt.AlignmentFlag.AlignCenter,
            "0",
        )
        painter.drawText(
            QRect(0, height - fontsize, self._left, fontsize),
            Qt.AlignmentFlag.AlignCenter,
            f"{biggest}",
        )
        horheight = height / (biggest * 2 + 1)
        for index in range(num_turns):
            if not (
                result := self.results[index] if index < len(self.results) else None
            ):
                continue
            percent = int(float(result["percent"]))
            num = int(float(result["num"]))
            if index % 2 == 1:
                percent = 100 - percent
                num = num * -1
            if last_percent:
                pen = painter.pen()
                pen.setColor(QColor("green"))
                pen.setWidth(2)
                painter.setPen(pen)
                hor_pos1 = block * index + self._left
                hor_pos2 = block * (index + 1) + self._left
                vert_ppos1 = int(last_percent * onepc) + 1
                vert_ppos2 = int(percent * onepc) + 1
                painter.drawLine(
                    QPoint(hor_pos1, vert_ppos1),
                    QPoint(hor_pos2, vert_ppos2),
                )
                pen.setColor(QColor("blue"))
                painter.setPen(pen)

                vert_npos1 = int(last_num * horheight + 50 * onepc)
                vert_npos2 = int(num * horheight + 50 * onepc)
                # painter.drawLine(
                #     QPoint(
                #         # block * (index - 1) + self._left,
                #         hor_pos1,
                #         vert_npos1,
                #     ),
                #     QPoint(
                #         # block * index + self._left,
                #         hor_pos2,
                #         vert_npos2,
                #     ),
                # )
                # //print("%: ",last_percent,percent)
                print(
                    "%",
                    "\t".join(
                        (
                            str(x)
                            for x in (vert_ppos1, vert_ppos2, last_percent, percent)
                        )
                    ),
                )
            last_num = num
            last_percent = percent
            biggest = max(biggest, num)

        if self._hover is not None:
            painter.setPen(text_color)
            painter.drawLine(
                QPoint(self._hover, 0), QPoint(self._hover, int(onepc * 100))
            )

            # for index in range(-10, -10, -5):
            #    text_pos = int(onepc * index)
            #    painter.drawText(
            #        QRect(0, text_pos - 5, 18, 10), Qt.AlignmentFlag.AlignCenter, f"{100 - index}"
            #    )

    def mousePressEvent(self, event) -> None:
        x = event.position().x()
        index = int((x - self._left) / self._block)
        path = self.last_turn.node.full_path_to_last()
        print("i", index)
        if -1 < index < len(path):
            self.diagram.game_ui.controller.set_cursor(path[index])

    def eventFilter(self, _object, event):
        type_ = event.type()
        if type_ in (QEvent.Type.Enter, QEvent.Type.MouseMove):
            self._hover = int(event.position().x())
            self.update()
            return True
        if type_ == QEvent.Type.Leave:
            self._hover = None
            self.update()
            return True

        return False


class DiagramBox(Box):
    name = "Diagram"

    def init(self, **kwargs):
        layout = QVBoxLayout()
        self.events = {results.AnnotationDone, results.TurnDone}
        self.canvas = DiagramCanvas(parent=self)

        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.canvas)
        row = QWidget(self)
        rowlayout = QHBoxLayout()

        btn = QPushButton("ki")
        icon = QIcon(f"{BASE_DIR}/gui/imgs/led-green-black.svg")
        btn.setIcon(QIcon(f"{BASE_DIR}/gui/imgs/led-green-black.svg"))
        rowlayout.addWidget(btn)
        row.setLayout(rowlayout)
        layout.addWidget(row)
        self.setMaximumHeight(220)
        self.setLayout(layout)

    def received_annotated(self, result: results.AnnotationDone) -> None:
        last_turn = self.canvas.last_turn
        assert last_turn
        self.canvas.results.clear()
        for pathnode in last_turn.node.full_path_to_last():
            if pathnode.annos.winrates:
                percent, num = list(pathnode.annos.winrates.values())[0][0:2]
                self.canvas.results.append(
                    {"percent": float(percent), "num": float(num)}
                )
            else:
                break
        self.canvas.update()

    def received_turn(self, result: results.TurnDone) -> None:
        self.canvas.last_turn = result
        self.canvas.update()
