# pylint: disable=invalid-name
# because qt
from PyQt5.QtWidgets import QWidget, QScrollArea, QLabel
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from pygoban.move import Move
from pygoban.status import BLACK


class MoveNode(QLabel):

    WIDTH = 30
    HEIGHT = 30

    def __init__(self, parent, move: Move):
        self.treex = 0
        self.treey = 0
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
        self.setMinimumSize(self.WIDTH, self.HEIGHT)
        self.setMaximumSize(self.WIDTH, self.HEIGHT)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        if self == self.parent().cursor:
            painter.setBrush(Qt.red)
            painter.drawEllipse(3, 3, 25, 25)
        painter.setBrush(Qt.black if self.move.color == BLACK else Qt.white)
        painter.drawEllipse(5, 5, 20, 20)
        painter.end()
        super().paintEvent(event)

    def mousePressEvent(self, _event):
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

        add(move)
        self.set_moves(move)

    def set_moves(self, move):
        # cnt = 0
        alreade_used = set()

        def _set(node, treex, treey):
            node.show()
            while (
                xpos := (MoveNode.WIDTH * treex),
                ypos := (MoveNode.HEIGHT * treey),
            ) in alreade_used:
                treex += 1
            alreade_used.add((xpos, ypos))
            node.treex = treex
            node.treey = treey
            # super(QLabel, node).move(xpos, ypos)
            node.setGeometry(xpos, ypos, node.WIDTH, node.HEIGHT)
            # nonlocal cnt
            # if cnt % 100 == 0:
            #     print("C2", cnt)
            # cnt += 1
            self.maxx = max(self.maxx, xpos)
            self.maxy = max(self.maxy, ypos)
            node.repaint()
            for index, child in enumerate(node.move.children.values()):
                node = self.nodes.get(id(child))
                if node:
                    _set(node, index + treex, treey + 1)

        if move.parent:
            parent = self.nodes[id(move.parent)]
            _set(parent, parent.treex, parent.treey)
        else:
            node = self.nodes[id(move)]
            _set(node, 1, 1)
        self.resize(self.maxx + 40, self.maxy + 40)
        self.repaint()

    def paintEvent(self, event):
        def centered(pos):
            return QPoint(pos.x() + 15, pos.y() + 15)

        def con(node):
            if node.child_index is not None:
                painter.drawLine(
                    centered(node.pos()),
                    centered(self.nodes[id(node.move.parent)].pos()),
                )
            for child in node.move.children.values():
                con(self.nodes[id(child)])

        super().paintEvent(event)
        painter = QPainter()
        painter.begin(self)
        painter.setBrush(Qt.black)

        if self.root:
            con(self.root)
        painter.end()

    def resizeEvent(self, _event):
        # print("CanvasRESIZEE", event)
        if self.root:
            self.set_moves(self.cursor.move)


class Tree(QScrollArea):

    moves_signal = pyqtSignal(Move)

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.canvas = TreeCanvas(parent=None, callback=callback)
        self.setMinimumSize(80, 80)
        self.setWidget(self.canvas)
        self.moves_signal.connect(self.update_moves)

    def add_move(self, move):
        print("TREE. Add move", move)
        return self.canvas.add_move(move)

    def set_cursor(self, move: Move):
        if node := self.canvas.nodes.get(id(move)):
            old = self.canvas.cursor
            self.canvas.cursor = node
            self.canvas.cursor.repaint()
            old.repaint()

    def update_moves(self, move: Move):
        self.add_move(move)
        self.canvas.set_moves(move)
