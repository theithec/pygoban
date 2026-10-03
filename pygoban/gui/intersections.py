# pylint: disable=invalid-name, comparison-with-callable, using-constant-test
import os
from functools import lru_cache
from typing import TYPE_CHECKING, cast

from PyQt6.QtCore import (  # type: ignore  # pylint: disable=no-name-in-module
    QEvent,
    QRect,
    Qt,
    QTimer,
)
from PyQt6.QtGui import (  # pylint: disable=no-name-in-module
    QColor,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import QWidget  # pylint: disable=no-name-in-module

from .. import Color, Intersection, Node, Pos
from . import BASE_DIR, GameUI, GUIMode

if TYPE_CHECKING:
    from .boardwidget import BoardWidget, InsParams

def winrate_colors(perc: float) -> tuple[QColor, QColor]:
    """Return a red-to-green winrate background and a contrasting text color."""
    value = min(max(float(perc), 0.0), 100.0)
    stops = (QColor("#c93636"), QColor("#e5c84b"), QColor("#2e9d55"))
    segment = min(int(value // 50), 1)
    fraction = (value - segment * 50) / 50
    start, end = stops[segment], stops[segment + 1]
    background = QColor(
        round(start.red() + (end.red() - start.red()) * fraction),
        round(start.green() + (end.green() - start.green()) * fraction),
        round(start.blue() + (end.blue() - start.blue()) * fraction),
    )

    def luminance(channel: int) -> float:
        normalized = channel / 255
        return (
            normalized / 12.92
            if normalized <= 0.04045
            else ((normalized + 0.055) / 1.055) ** 2.4
        )

    lightness = (
        0.2126 * luminance(background.red())
        + 0.7152 * luminance(background.green())
        + 0.0722 * luminance(background.blue())
    )
    black_contrast = (lightness + 0.05) / 0.05
    white_contrast = 1.05 / (lightness + 0.05)
    foreground = QColor("black" if black_contrast >= white_contrast else "white")
    return background, foreground


def variation_number_color(index: int, stone_color: Color) -> QColor:
    """Return an ordered hue with readable brightness on the variation stone."""
    hue = ((max(index, 1) - 1) * 30) % 360
    value = 255 if stone_color == Color.BLACK else 105
    return QColor.fromHsv(hue, 220, value)


@lru_cache()
def get_pixmap(status: Color) -> QPixmap | None:
    if status == Color.BLACK:
        path = "gui/imgs/black.png"
    elif status == Color.WHITE:
        path = "gui/imgs/white.png"
    else:
        return None
    return QPixmap(QImage(os.path.join(BASE_DIR, path)))


class IntersectionWidget(QWidget):
    """Visual representation of a intersection in a go board"""

    node: Node

    def __init__(self, parent: "BoardWidget", board_pos: Pos, is_hoshi: bool) -> None:
        super().__init__(parent)
        self.board_pos: Pos = board_pos
        self.game_ui: GameUI = cast(GameUI, parent.parent())
        self.is_hoshi = is_hoshi
        self._is_current = None
        self._hover = False
        self.installEventFilter(self)
        self.inter: Intersection | None = None
        self._analysis_moves: list[Pos | None] = []
        self._analysis_index = 0
        self._analysis_color = Color.BLACK
        self._analysis_timer = QTimer(self)
        self._analysis_timer.setSingleShot(True)
        self._analysis_timer.timeout.connect(self._show_next_analysis_move)

    def mousePressEvent(self, event) -> None:
        self.game_ui.inter_clicked(
            self, is_rightclick=event.button() == Qt.MouseButton.RightButton
        )

        self._hover = False

    def draw_number(self, painter, params) -> None:
        self.draw_char(str(len(self.node.annos.numbers)), painter, params)

    def _show_next_analysis_move(self) -> None:
        if not self._analysis_moves or not self.game_ui.last_turn:
            return

        pos = self._analysis_moves[self._analysis_index]
        if pos is not None:
            self.game_ui.last_turn.node.annos.progress[pos] = (
                self._analysis_index + 1,
                self._analysis_color,
            )
        self._analysis_index += 1
        self._analysis_color = self._analysis_color.other()
        self.parent().repaint()

        if self._analysis_index < len(self._analysis_moves):
            interval = self.game_ui.main_ui.settings.analysis_variation_interval_ms
            self._analysis_timer.start(max(1, interval))

    def _clear_analysis_preview(self, last_turn) -> None:
        self._analysis_timer.stop()
        self._analysis_moves.clear()
        self._analysis_index = 0
        self.game_ui.show_analyzed_variation = False
        if last_turn.node.annos.progress:
            last_turn.node.annos.progress.clear()
            self.parent().repaint()

    def draw_char(self, txt, painter, params, color=None):
        font = painter.font()
        font.setPixelSize(int(params.font_height))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(color or QColor("red"))
        painter.drawText(
            QRect(0, -(params.size // 8), params.size, params.size),
            Qt.AlignmentFlag.AlignCenter,
            txt,
        )

    @staticmethod
    def draw_winrate(info, painter, params, is_best_move: bool = False):
        fwidth = 4
        perc = float(info[0])
        background, foreground = winrate_colors(perc)
        if is_best_move:
            background = QColor("#3478f6")
            foreground = QColor("white")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawEllipse(
            fwidth, fwidth, params.size - (fwidth * 2), params.size - (fwidth * 2)
        )
        font = painter.font()
        txt = info[0]
        font.setPixelSize(int(params.size / (len(txt) / 1.4)))
        painter.setFont(font)
        painter.setPen(foreground)
        painter.drawText(
            QRect(0, params.font_bottom, params.size, params.size),
            Qt.AlignmentFlag.AlignCenter,
            txt,
        )
        txt = info[1]
        txt = txt[: min(4, len(txt))]
        font = painter.font()
        psize = int(params.small_size / (len(txt) / 2))
        font.setPixelSize(psize)
        painter.setFont(font)
        painter.drawText(
            QRect(psize, int(psize * 0.7), params.small_size, params.size),
            Qt.AlignmentFlag.AlignCenter,
            txt,
        )

    def draw_circle(self, painter, params):
        width = params.size // 8
        pen = QPen(QColor("red"), width)
        painter.setPen(pen)
        painter.drawEllipse(
            width, width, params.size - (width * 2), params.size - (width * 2)
        )

    def draw_triangle(self, painter, params):
        path = QPainterPath()
        fwidth = params.size // 8
        size = params.size - (fwidth // 2)
        path.moveTo(fwidth, size - fwidth)
        path.lineTo(size // 2, fwidth)
        path.lineTo(size, size - fwidth)
        path.lineTo(fwidth, size - fwidth)
        pen = QPen(QColor("red"), fwidth)
        painter.strokePath(path, pen)

    def draw_square(self, painter, params):
        path = QPainterPath()
        # fwidth = 4
        fwidth = params.size // 8
        size = params.size  # - (fwidth // 2)
        path.moveTo(fwidth, fwidth)
        path.lineTo(fwidth, size - fwidth)
        path.lineTo(size - fwidth, size - fwidth)
        path.lineTo(size - fwidth, fwidth)
        path.lineTo(fwidth, fwidth)
        pen = QPen(QColor("red"), fwidth)
        painter.strokePath(path, pen)

    def draw_owned(self, color, painter, params):
        assert (owned_pixmap := get_pixmap(color))
        painter.setOpacity(0.5)
        painter.drawPixmap(
            QRect(
                params.small_pos,
                params.small_pos,
                params.small_size,
                params.small_size,
            ),
            owned_pixmap,
        )
        painter.setOpacity(1)

    def draw_dimmed(self, painter: QPainter, params: "InsParams"):
        painter.setBrush(QColor("gray"))
        painter.setOpacity(0.8)
        painter.fillRect(0, 0, params.size, params.size, painter.brush())
        painter.setOpacity(1)

    def _draw_hoshi(self, painter: QPainter, params: "InsParams") -> None:
        if not self.is_hoshi:
            return
        brush = painter.brush()
        painter.setBrush(QColor("black"))
        painter.drawEllipse(
            params.hoshi_pos, params.hoshi_pos, params.hoshi_size, params.hoshi_size
        )
        painter.setBrush(brush)

    def _draw_stone(self, painter: QPainter, params: "InsParams", last_turn) -> None:
        stone_pixmap = get_pixmap(self.inter.color)
        if not stone_pixmap:
            return
        painter.drawPixmap(
            QRect(
                params.stone_pos,
                params.stone_pos,
                params.stone_size,
                params.stone_size,
            ),
            stone_pixmap,
        )
        if self.board_pos == last_turn.node.pos:
            painter.setBrush(QColor("red"))
            painter.drawEllipse(
                params.small_pos,
                params.small_pos,
                params.small_size,
                params.small_size,
            )

    def _draw_edit_annotations(self, painter: QPainter, params: "InsParams", last_turn):
        if self.game_ui.gui_mode != GUIMode.EDIT:
            return False
        annos = last_turn.node.annos
        marked = False
        if marker := annos.markers.get(self.board_pos):
            getattr(self, f"draw_{marker.value}")(painter, params)
            marked = True
        if color := annos.owned.get(self.board_pos):
            self.draw_owned(color, painter, params)
            marked = True
        elif txt := annos.chars.get(self.board_pos):
            self.draw_char(txt, painter, params)
            marked = True
        elif txt := annos.numbers.get(self.board_pos):
            self.draw_char(txt, painter, params)
            marked = True
        return marked

    def _draw_child_hint(self, painter: QPainter, params: "InsParams", last_turn) -> None:
        if self.game_ui.gui_mode not in (GUIMode.EDIT, GUIMode.PLAY):
            return
        child = next(
            (child for child in last_turn.node.children if self.board_pos == child.pos),
            None,
        )
        if child:
            child_pixmap = get_pixmap(child.color)
            painter.setOpacity(0.5)
            painter.drawPixmap(
                QRect(
                    params.small_pos,
                    params.small_pos,
                    params.small_size,
                    params.small_size,
                ),
                child_pixmap,
            )
        painter.setOpacity(1)

    def _draw_hover(self, painter: QPainter, params: "InsParams", last_turn) -> None:
        if self.inter.color != Color.EMPTY or not self._hover or self.game_ui.annotation_type:
            return
        hover_pixmap = get_pixmap(last_turn.next_color)
        assert hover_pixmap
        painter.setOpacity(0.8)
        painter.drawPixmap(
            QRect(
                params.stone_pos,
                params.stone_pos,
                params.stone_size,
                params.stone_size,
            ),
            hover_pixmap,
        )

    def _draw_analyzed_variation(
        self, painter: QPainter, params: "InsParams", last_turn
    ) -> None:
        analyzed_variation = last_turn.node.annos.progress.get(self.board_pos)
        if not analyzed_variation:
            return
        index, color = analyzed_variation
        vari_pixmap = get_pixmap(color)
        assert vari_pixmap
        painter.setOpacity(0.8)
        painter.drawPixmap(
            QRect(
                params.stone_pos,
                params.stone_pos,
                params.stone_size,
                params.stone_size,
            ),
            vari_pixmap,
        )
        painter.setOpacity(1)
        self.draw_char(str(index), painter, params, variation_number_color(index, color))

    def _draw_count_ownership(self, painter: QPainter, params: "InsParams") -> None:
        if self.game_ui.gui_mode != GUIMode.COUNT or not self.inter.owner:
            return
        self.draw_owned(self.inter.owner, painter, params)
        owned_pixmap = get_pixmap(self.inter.owner)
        assert owned_pixmap
        painter.setOpacity(0.5)
        painter.drawPixmap(
            QRect(
                params.small_pos,
                params.small_pos,
                params.small_size,
                params.small_size,
            ),
            owned_pixmap,
        )
        painter.setOpacity(1)

    def paintEvent(self, _) -> None:
        """Draw"""
        if not (last_turn := self.game_ui.last_turn):
            return
        self.inter = last_turn.board.intersection(self.board_pos)
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHints(
            painter.RenderHint.Antialiasing | painter.RenderHint.SmoothPixmapTransform
        )
        pen = painter.pen()
        pen.setWidth(2)
        pen.setColor(QColor("black"))
        painter.setPen(pen)
        params: InsParams = cast("BoardWidget", self.parent()).ins_params
        self._draw_hoshi(painter, params)

        assert self.inter
        stone_pixmap = get_pixmap(self.inter.color)
        if (
            (not stone_pixmap)
            and (rate := last_turn.node.annos.winrates.get(self.board_pos))
            and not self.game_ui.show_analyzed_variation
        ):
            self.draw_winrate(
                rate,
                painter,
                params,
                is_best_move=self.board_pos == last_turn.node.annos.best_move,
            )

        self._draw_stone(painter, params, last_turn)
        marked = self._draw_edit_annotations(painter, params, last_turn)
        if not marked:
            self._draw_child_hint(painter, params, last_turn)
        self._draw_hover(painter, params, last_turn)
        self._draw_analyzed_variation(painter, params, last_turn)
        self._draw_count_ownership(painter, params)
        self._hover = False
        painter.end()

    def eventFilter(self, _object, event):
        if not (last_turn := self.game_ui.last_turn):
            return False

        if self.inter and self.inter.color == Color.EMPTY:
            type_ = event.type()

            analyzed_variation_stones = []
            if rate := last_turn.node.annos.winrates.get(self.board_pos):
                analyzed_variation_stones = rate[2]

            if type_ == QEvent.Type.Enter:
                # and not self.controller.bar.inner.boxes["EditBox"].decogroup.checkedButton()
                self._hover = True
                if analyzed_variation_stones:
                    self._clear_analysis_preview(last_turn)
                    self._analysis_moves = analyzed_variation_stones
                    self._analysis_color = last_turn.next_color
                    self.game_ui.show_analyzed_variation = True
                    self._show_next_analysis_move()
                else:
                    self.repaint()

                return True

            if (
                type_ == QEvent.Type.Leave
                # and not self.controller.bar.inner.boxes["EditBox"].decogroup.checkedButton()
            ):
                # if not self.controller.is_annotating:
                self._hover = False
                self._clear_analysis_preview(last_turn)
                self.repaint()
                return True

        return False
