# pylint: disable=invalid-name
# because qt
from PyQt6.QtCore import QPoint, Qt, pyqtSignal  # pylint: disable=no-name-in-module
from PyQt6.QtGui import (  # pylint: disable=no-name-in-module
    QColor,
    QColorConstants,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QLabel,
    QScrollArea,
    QSizePolicy,
    QWidget,
)
from . import GameUI, GUIMode
from .. import BaseReceiver, Color, Node, results


class TreeNode(QLabel):
    WIDTH = 38
    tree: "TreeCanvas"
    child_index: int | None

    def __init__(self, parent, node: Node):
        super().__init__(parent)
        self.node = node
        self.tree = parent
        self.setStyleSheet(
            "QLabel { font-size: 7pt; color: %s }"
            % ("white" if self.node.color == Color.BLACK else "black")
        )
        self.setText(str(len(self.node.path())))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if node.parent:
            assert self.node.parent
            self.child_index = self.node.parent.children.index(self.node)
        else:
            self.child_index = None

        self.setMinimumSize(self.WIDTH, self.WIDTH)
        self.setMaximumSize(self.WIDTH, self.WIDTH)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        if self.node.color == Color.BLACK:
            qcol = QColorConstants.Black  # type: ignore
        elif self.node.color == Color.WHITE:
            qcol = QColorConstants.White  # type: ignore
        else:
            qcol = QColorConstants.Gray  # type: ignore

        pen = QPen()
        pen.setBrush(qcol)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(qcol)
        pen.setCosmetic(True)
        painter.drawEllipse(
            self.WIDTH // 4, self.WIDTH // 4, self.WIDTH // 2, self.WIDTH // 2
        )
        painter.end()
        painter = QPainter()
        painter.begin(self)
        painter.setPen(QColorConstants.Gray)  # type: ignore

        if self is self.tree.tree_cursor:
            pen = QPen()
            pen.setBrush(QColorConstants.Red)  # type: ignore
            pen.setCosmetic(True)
            painter.setPen(pen)
        painter.drawEllipse(
            self.WIDTH // 4, self.WIDTH // 4, self.WIDTH // 2, self.WIDTH // 2
        )
        super().paintEvent(event)

    def mousePressEvent(self, event):
        if self.tree.tree.game_ui.gui_mode == GUIMode.PLAY:
            return
        is_rightclick = event.button() == Qt.MouseButton.RightButton
        if is_rightclick:
            node = self.node.parent
            self.tree.del_stone(self)
        else:
            node = self.node
        self.tree.callback(node)


class TreeCanvas(QWidget):
    def __init__(self, parent: "Tree", callback):
        self.tree = parent
        super().__init__(parent)
        self.tree_nodes = {}
        self.root = None
        self.tree_cursor = None
        self.setMinimumWidth(TreeNode.WIDTH * 5)
        self.callback = callback
        self.maxx = 0
        self.maxy = 0

    def add_stone(self, stone):
        def add(stone):
            tree_node = TreeNode(self, stone)
            if not self.tree_nodes:
                self.root = tree_node
            self.tree_nodes[id(stone)] = tree_node
            self.tree_cursor = tree_node
            for child in stone.children:
                add(child)

        if not self.root:
            while stone.parent:
                stone = stone.parent
            self.root = stone
        if not (stone.parent and stone.parent.is_pass and stone.is_pass):
            add(stone)
            self.set_stones()

    def del_stone(self, tree_node: TreeNode):
        parent = tree_node.node.parent
        if not parent:
            return

        def _del(tree_node):
            del self.tree_nodes[id(tree_node.node)]
            children = tree_node.node.children
            tree_node.node.__del__()
            tree_node.hide()
            del tree_node
            for child in children:
                _del(self.tree_nodes[id(child)])

        _del(self.tree_nodes[id(tree_node.node)])
        self.tree.set_cursor(parent)

    def set_stones(self):
        alreade_used = set()

        def _set(tree_node, treex, treey):
            tree_node.show()
            while (
                xpos := int((TreeNode.WIDTH * treex) - (TreeNode.WIDTH / 3)),
                ypos := (TreeNode.WIDTH * treey),
            ) in alreade_used:
                treex += 1
            alreade_used.add((xpos, ypos))
            tree_node.treex = treex
            tree_node.treey = treey
            tree_node.setGeometry(xpos, ypos, tree_node.WIDTH, tree_node.WIDTH)
            self.maxx = max(self.maxx, xpos)
            self.maxy = max(self.maxy, ypos)
            for index, child in enumerate(tree_node.node.children):
                node = self.tree_nodes[id(child)]
                if node:
                    _set(node, index + treex, treey + 1)

        _set(self.root, 1, 1)
        self.resize(self.maxx + TreeNode.WIDTH, self.maxy + TreeNode.WIDTH)

    def paintEvent(self, event):
        super().paintEvent(event)
        # visible_rect = self.visibleRegion().rects()[0]
        visible_rect = self.visibleRegion().boundingRect()
        width = visible_rect.width()
        assert self.tree_cursor
        path = self.tree_cursor.node.path()

        def centered(pos):
            return QPoint(pos.x() + TreeNode.WIDTH // 2, pos.y() + TreeNode.WIDTH // 2)

        def conn(tree_node):
            pos = tree_node.pos()
            height = tree_node.height()
            if visible_rect.contains(pos) and tree_node.child_index is not None:
                painter.drawLine(
                    centered(pos),
                    centered(self.tree_nodes[id(tree_node.node.parent)].pos()),
                )

            if (
                pos.y() < visible_rect.y() + visible_rect.height()
                and pos.x() < visible_rect.x() + visible_rect.width()
            ):
                for child in tree_node.node.children:
                    if child_node := self.tree_nodes.get(id(child)):
                        conn(child_node)

        painter = QPainter()
        painter.begin(self)
        if self.root:
            conn(self.root)
        painter.end()


class Tree(QScrollArea, BaseReceiver):
    stones_signal = pyqtSignal(Node)

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.game_ui: GameUI = parent.parent()
        self.canvas = TreeCanvas(parent=self, callback=callback)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setWidget(self.canvas)
        self.stones_signal.connect(self.set_cursor)
        self.setMinimumWidth(int(TreeNode.WIDTH * 1.5))
        self.horizontalScrollBar().valueChanged.connect(self.moved)
        self.verticalScrollBar().valueChanged.connect(self.moved)
        self.events = {results.TurnDone}  # , results.AnnotationDone}
        parent.game_ui.controller.add_receiver(self)

    def moved(self, *args, **kwargs):
        self.canvas.update()

    def set_cursor(self, stone: Node):
        if tree_node := self.canvas.tree_nodes.get(id(stone)):
            self.canvas.tree_cursor = tree_node
        else:
            self.canvas.add_stone(stone)
        self.ensureWidgetVisible(self.canvas.tree_cursor)
        if self.canvas.tree_cursor.node != stone:
            self.set_cursor(stone)
        self.canvas.update()

    def received_turn(self, result: results.TurnDone):
        # return
        self.stones_signal.emit(result.node)

    # def received_annotated(self, result):
    #     self.canvas.update()
