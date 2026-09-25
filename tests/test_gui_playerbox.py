import pytest

from pygoban import Color
from pygoban.gui.boxes.playerbox import PlayerBox
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