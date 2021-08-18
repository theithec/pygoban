# pylint: disable=invalid-name
# because qt
from PyQt5.QtWidgets import QWidget, QScrollArea, QLabel
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from pygoban.move import Move
from pygoban.status import BLACK


class MoveNode(QLabel):

    WIDTH = 38

    def __init__(self, parent, move: Move):
        super().__init__(parent)
        self.move = move
        self.setStyleSheet(
            "QLabel { color: %s }" % ("white" if self.move.color == BLACK else "black")
        )
        self.setText(str(len(move.get_path())))
        self.setAlignment(Qt.AlignCenter)
        self.child_index = (
            list(move.parent.children.values()).index(move) if move.parent else None
        )
        self.setMinimumSize(self.WIDTH, self.WIDTH)
        self.setMaximumSize(self.WIDTH, self.WIDTH)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        if self == self.parent().cursor:
            painter.setBrush(Qt.red)
            painter.setPen(Qt.red)
            painter.drawEllipse(7, 7, 24, 24)
        painter.setBrush(Qt.black if self.move.color == BLACK else Qt.white)
        painter.setPen(Qt.black if self.move.color == BLACK else Qt.white)
        painter.drawEllipse(8, 8, 22, 22)
        painter.end()
        super().paintEvent(event)

    def mousePressEvent(self, _event):
        # import pudb; pudb.set_trace()
        self.parent().callback(self.move)


class TreeCanvas(QWidget):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.nodes = {}
        self.root = None
        self.cursor = None
        self.setMinimumSize(100, 200)
        self.callback = callback
        self.maxx = 0
        self.maxy = 0

    def add_move(self, move):
        def add(move):
            node = MoveNode(self, move)
            if not self.nodes:
                self.root = node
            self.nodes[id(move)] = node
            self.cursor = node
            for child in move.children.values():
                add(child)

        if not self.root:
            while move.parent:
                move = move.parent
            self.root = move
        if not (move.parent and move.parent.is_pass and move.is_pass):
            add(move)
            self.set_moves()

    def set_moves(self):
        alreade_used = set()

        def _set(node, treex, treey):
            node.show()
            while (
                xpos := (MoveNode.WIDTH * treex),
                ypos := (MoveNode.WIDTH * treey),
            ) in alreade_used:
                treex += 1
            alreade_used.add((xpos, ypos))
            node.treex = treex
            node.treey = treey
            node.setGeometry(xpos, ypos, node.WIDTH, node.WIDTH)
            self.maxx = max(self.maxx, xpos)
            self.maxy = max(self.maxy, ypos)
            for index, child in enumerate(node.move.children.values()):
                node = self.nodes[id(child)]
                if node:
                    _set(node, index + treex, treey + 1)

        _set(self.root, 1, 1)
        self.resize(self.maxx + 40, self.maxy + 40)

    def paintEvent(self, event):
        super().paintEvent(event)
        visible_rect = self.visibleRegion().rects()[0]

        def centered(pos):
            return QPoint(pos.x() + 19, pos.y() + 19)

        def conn(node):
            pos = node.pos()
            if visible_rect.contains(pos) and node.child_index is not None:
                painter.drawLine(
                    centered(pos),
                    centered(self.nodes[id(node.move.parent)].pos()),
                )

            if (
                pos.y() < visible_rect.y() + visible_rect.height()
                and pos.x() < visible_rect.x() + visible_rect.width()
            ):
                for child in node.move.children.values():
                    if child_node := self.nodes.get(id(child)):
                        conn(child_node)

        painter = QPainter()
        painter.begin(self)
        painter.setBrush(Qt.black)
        if self.root:
            conn(self.root)
        painter.end()


class Tree(QScrollArea):

    moves_signal = pyqtSignal(Move)

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.canvas = TreeCanvas(parent=None, callback=callback)
        self.setMinimumSize(80, 80)
        self.setWidget(self.canvas)
        self.moves_signal.connect(self.set_cursor)

    def set_cursor(self, move: Move):
        if node := self.canvas.nodes.get(id(move)):
            old = self.canvas.cursor
            self.canvas.cursor = node
            self.canvas.repaint()
            self.ensureWidgetVisible(self.canvas.cursor)
        else:
            self.canvas.add_move(move)

        self.ensureWidgetVisible(self.canvas.cursor)
