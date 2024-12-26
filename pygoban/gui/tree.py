# pylint: disable=invalid-name
# because qt
from PyQt6.QtCore import QPoint, Qt, pyqtSignal  # pylint: disable=no-name-in-module
from PyQt6.QtGui import QColor, QPainter, QPen, QColorConstants  # pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QLabel,
    QScrollArea,
    QSizePolicy,
    QWidget,
)

from .. import Color, Node


class StoneNode(QLabel):
    WIDTH = 38
    tree: "TreeCanvas"
    child_index: int | None

    def __init__(self, parent, stone: Node):
        super().__init__(parent)
        self.bstone = stone
        self.tree = parent
        self.setStyleSheet(
            "QLabel { color: %s }" % ("white" if self.bstone.color == Color.BLACK else "black")
        )
        self.setText(str(len(self.bstone.path())))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if stone.parent:
            assert self.bstone.parent
            self.child_index = self.bstone.parent.children.index(self.bstone)
        else:
            self.child_index = None

        self.setMinimumSize(self.WIDTH, self.WIDTH)
        self.setMaximumSize(self.WIDTH, self.WIDTH)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        if self.bstone.color == Color.BLACK:
            qcol = QColorConstants.Black  # type: ignore
        elif self.bstone.color == Color.WHITE:
            qcol = QColorConstants.White  # type: ignore
        else:
            qcol = QColorConstants.Gray  # type: ignore

        pen = QPen()
        pen.setBrush(qcol)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(qcol)
        pen.setCosmetic(True)
        painter.drawEllipse(self.WIDTH // 4, self.WIDTH // 4, self.WIDTH // 2, self.WIDTH // 2)
        painter.end()
        painter = QPainter()
        painter.begin(self)
        painter.setPen(QColorConstants.Gray)  # type: ignore

        if self is self.tree.tree_cursor:
            pen = QPen()
            pen.setBrush(QColorConstants.Red)  # type: ignore
            pen.setCosmetic(True)
            painter.setPen(pen)
        painter.drawEllipse(self.WIDTH // 4, self.WIDTH // 4, self.WIDTH // 2, self.WIDTH // 2)
        super().paintEvent(event)

    def mousePressEvent(self, _event):
        self.tree.callback(self.bstone)


class TreeCanvas(QWidget):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.nodes = {}
        self.root = None
        self.tree_cursor = None
        self.setMinimumWidth(StoneNode.WIDTH * 5)
        self.callback = callback
        self.maxx = 0
        self.maxy = 0

    def add_stone(self, stone):
        def add(stone):
            node = StoneNode(self, stone)
            if not self.nodes:
                self.root = node
            self.nodes[id(stone)] = node
            self.tree_cursor = node
            for child in stone.children:
                add(child)

        if not self.root:
            while stone.parent:
                stone = stone.parent
            self.root = stone
        if not (stone.parent and stone.parent.is_pass and stone.is_pass):
            add(stone)
            self.set_stones()

    def set_stones(self):
        alreade_used = set()

        def _set(node, treex, treey):
            node.show()
            while (
                xpos := int((StoneNode.WIDTH * treex) - (StoneNode.WIDTH / 3)),
                ypos := (StoneNode.WIDTH * treey),
            ) in alreade_used:
                treex += 1
            alreade_used.add((xpos, ypos))
            node.treex = treex
            node.treey = treey
            node.setGeometry(xpos, ypos, node.WIDTH, node.WIDTH)
            self.maxx = max(self.maxx, xpos)
            self.maxy = max(self.maxy, ypos)
            for index, child in enumerate(node.bstone.children):
                node = self.nodes[id(child)]
                if node:
                    _set(node, index + treex, treey + 1)

        _set(self.root, 1, 1)
        self.resize(self.maxx + StoneNode.WIDTH, self.maxy + StoneNode.WIDTH)

    def paintEvent(self, event):
        super().paintEvent(event)
        # visible_rect = self.visibleRegion().rects()[0]
        visible_rect = self.visibleRegion().boundingRect()
        width = visible_rect.width()
        assert self.tree_cursor
        path = self.tree_cursor.bstone.path()

        def centered(pos):
            return QPoint(pos.x() + StoneNode.WIDTH // 2, pos.y() + StoneNode.WIDTH // 2)

        def conn(node):
            pos = node.pos()
            height = node.height()
            if visible_rect.contains(pos) and node.child_index is not None:
                if node.bstone in path:
                    if winrate := node.bstone.annos.winrates:
                        best = sorted([float(val[0]) for val in winrate.values()])[-1]
                        half = int((width / 100) * best)
                        if node.bstone.color == Color.BLACK:
                            half = width - half
                        painter.fillRect(0, pos.y(), half, height, Qt.darkGray)
                        painter.fillRect(half, pos.y(), width - half, height, Qt.lightGray)
                    painter.setBrush(QColorConstants.White)
                    painter.setPen(QColorConstants.White)
                else:
                    painter.setBrush(QColorConstants.Gray)
                    painter.setPen(QColorConstants.Gray)
                painter.drawLine(
                    centered(pos),
                    centered(self.nodes[id(node.bstone.parent)].pos()),
                )

            if (
                pos.y() < visible_rect.y() + visible_rect.height()
                and pos.x() < visible_rect.x() + visible_rect.width()
            ):
                for child in node.bstone.children:
                    if child_node := self.nodes.get(id(child)):
                        conn(child_node)

        painter = QPainter()
        painter.begin(self)
        if self.root:
            conn(self.root)
        painter.end()


class Tree(QScrollArea):
    stones_signal = pyqtSignal(Node)

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.canvas = TreeCanvas(parent=None, callback=callback)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setWidget(self.canvas)
        self.stones_signal.connect(self.set_cursor)
        self.setMinimumWidth(int(StoneNode.WIDTH * 1.5))
        self.horizontalScrollBar().valueChanged.connect(self.moved)

    def moved(self, *args, **kwargs):
        pass  # print("Moved", args, kwargs)

    def set_cursor(self, stone: Node):
        if node := self.canvas.nodes.get(id(stone)):
            self.canvas.tree_cursor = node
            # self.canvas.repaint()
            # TODO check auto
            # self.ensureWidgetVisible(self.canvas.tree_cursor)
        else:
            self.canvas.add_stone(stone)
        self.ensureWidgetVisible(self.canvas.tree_cursor)
        if self.canvas.tree_cursor.bstone != stone:
            self.set_cursor(stone)
        self.canvas.repaint()
