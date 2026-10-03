from types import SimpleNamespace

import pytest
from PyQt6.QtCore import QEvent
from PyQt6.QtGui import QColor, QFont

from pygoban import Color, Pos
from pygoban.gui.intersections import (
    IntersectionWidget,
    variation_number_color,
    winrate_colors,
)


@pytest.mark.parametrize(
    ("percentage", "background", "foreground"),
    [
        (-10, "#c93636", "#ffffff"),
        (0, "#c93636", "#ffffff"),
        (50, "#e5c84b", "#000000"),
        (100, "#2e9d55", "#000000"),
        (120, "#2e9d55", "#000000"),
    ],
)
def test_winrate_colors(percentage, background, foreground):
    bg, fg = winrate_colors(percentage)

    assert bg.name() == background
    assert fg.name() == foreground


def test_winrate_colors_transition_towards_green():
    low, _ = winrate_colors(10)
    high, _ = winrate_colors(90)

    assert low.red() > low.green()
    assert high.green() > high.red()


def test_variation_number_colors_follow_order_and_contrast_with_stones():
    first = variation_number_color(1, Color.BLACK)
    second = variation_number_color(2, Color.BLACK)
    black_stone_text = variation_number_color(10, Color.BLACK)
    white_stone_text = variation_number_color(10, Color.WHITE)

    assert first.hue() != second.hue()
    assert black_stone_text.value() == 255
    assert white_stone_text.value() == 105
    assert variation_number_color(100, Color.WHITE).hue() in range(360)


def test_best_move_uses_blue_winrate_ellipse(qt_app):
    class Painter:
        def __init__(self):
            self.brush = QColor("transparent")
            self.ellipse_brush = None

        def setPen(self, _pen):
            pass

        def setBrush(self, brush):
            self.brush = QColor(brush)

        def drawEllipse(self, *_args):
            self.ellipse_brush = self.brush

        def font(self):
            return QFont()

        def setFont(self, _font):
            pass

        def drawText(self, *_args):
            pass

    painter = Painter()
    params = SimpleNamespace(size=40, font_bottom=0, small_size=20)

    IntersectionWidget.draw_winrate(
        ("50", "1", [], 0), painter, params, is_best_move=True
    )

    assert painter.ellipse_brush == QColor("#3478f6")


def test_analysis_variation_reveals_moves_and_clears_on_leave(qtbot, game_widget):
    hovered_pos = next(iter(game_widget.boardwidget.intersections))
    widget = game_widget.boardwidget.intersections[hovered_pos]
    widget.inter = game_widget.last_turn.board.intersection(hovered_pos)
    first, second, third = (Pos(0, 0), Pos(1, 0), Pos(2, 0))
    game_widget.last_turn.node.annos.winrates[hovered_pos] = (
        "50",
        "0",
        [first, second, third],
        0,
    )

    widget.eventFilter(widget, QEvent(QEvent.Type.Enter))

    progress = game_widget.last_turn.node.annos.progress
    assert progress == {first: (1, Color.BLACK)}
    assert game_widget.show_analyzed_variation

    interval = game_widget.main_ui.settings.analysis_variation_interval_ms
    qtbot.wait(interval + 30)
    assert progress == {first: (1, Color.BLACK), second: (2, Color.WHITE)}

    widget.eventFilter(widget, QEvent(QEvent.Type.Leave))
    assert progress == {}
    assert not game_widget.show_analyzed_variation

    qtbot.wait(interval + 30)
    assert progress == {}
