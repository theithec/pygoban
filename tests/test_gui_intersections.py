import pytest

from pygoban import Color
from pygoban.gui.intersections import variation_number_color, winrate_colors


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