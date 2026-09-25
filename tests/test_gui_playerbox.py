import pytest

from pygoban import Color
from pygoban.gui.boxes.playerbox import PlayerBox
from pygoban.gui import GUIMode
from pygoban.timesettings import TimeSettings


@pytest.mark.parametrize(
    ("color", "expected_color"),
    [(Color.BLACK, "Schwarz"), (Color.WHITE, "Weiß")],
)
def test_player_box_shows_color_and_score(qtbot, color, expected_color):
    widget = PlayerBox(color)
    qtbot.addWidget(widget)

    assert widget.color_label.text() == expected_color
    assert widget.prisoners_label.text() == "0"
    assert widget.time_label.text() == "--:--:--"
    assert widget.points_caption.isHidden()

    widget.set_prisoners(4)
    widget.set_time(3661)
    widget.set_points(12.5)

    assert widget.prisoners_label.text() == "4"
    assert widget.time_label.text() == "01:01:01"
    assert widget.points_label.text() == "12.5"
    assert widget.points_caption.isHidden()

    widget.points_toggle.click()
    assert not widget.points_caption.isHidden()
    assert not widget.points_label.isHidden()

    widget.points_toggle.click()
    assert widget.points_caption.isHidden()
    assert widget.points_label.isHidden()


def test_player_box_shows_optional_byoyomi_settings(qtbot):
    widget = PlayerBox(
        Color.WHITE,
        TimeSettings(maintime=300, byoyomi_time=30, byoyomi_num=5, byoyomi_stones=1),
    )
    qtbot.addWidget(widget)

    assert widget.time_label.text() == "00:05:00"
    assert widget.additional_time_label.text() == "Byo-yomi: 5 x 30 s, 1 Stein(e) je Periode"

    widget.set_additional_time_text("")
    assert widget.additional_time_label.isHidden()


def test_game_and_count_boxes_share_style_but_keep_mode_contents(game_widget):
    players_box = game_widget.bar.inner.players_box
    game_box = players_box.boxes_by_mode[GUIMode.PLAY][Color.BLACK]
    count_box = players_box.boxes_by_mode[GUIMode.COUNT][Color.BLACK]

    assert game_box.styleSheet() == count_box.styleSheet()
    assert hasattr(game_box, "prisoners_label")
    assert not hasattr(game_box, "total_label")
    assert hasattr(count_box, "total_label")
    assert not hasattr(count_box, "prisoners_label")

    class Score:
        def summands(self):
            return [("points", 10), ("komi", 0.5)]

        @property
        def total(self):
            return 10.5

    players_box.received_count({Color.BLACK: Score(), Color.WHITE: Score()})

    assert count_box.labels["points"].text() == "10"
    assert count_box.labels["komi"].text() == "0.5"
    assert count_box.total_label.text() == "10.5"
    last_row = count_box.card_layout.itemAt(count_box.card_layout.count() - 1).layout()
    assert last_row.itemAt(0).widget().text() == "GESAMTPUNKTE"