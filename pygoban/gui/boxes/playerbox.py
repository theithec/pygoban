import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
	QApplication,
	QCheckBox,
	QGroupBox,
	QHBoxLayout,
	QLabel,
	QVBoxLayout,
	QWidget,
)

from pygoban import Color
from pygoban.timesettings import TimeSettings


class PlayerBox(QGroupBox):
	"""Display one Go player's color, prisoners, clock, and final score."""

	def __init__(
		self,
		color: Color,
		timesettings: TimeSettings | None = None,
		parent: QWidget | None = None,
	) -> None:
		color_name = "Schwarz" if color == Color.BLACK else "Weiß"
		super().__init__(parent=parent)
		self.setObjectName("playerBox")
		self.color = color
		background, foreground, muted, accent, border = (
			("#171717", "#f5f5f5", "#bcbcbc", "#f1d36c", "#555555")
			if color == Color.BLACK
			else ("#f8f8f5", "#202020", "#686860", "#806511", "#c8c5b9")
		)

		self.setStyleSheet(
			f"QGroupBox#playerBox {{ background-color: {background}; "
			f"border: 2px solid {border}; border-radius: 14px; color: {foreground}; }}"
			f"QLabel {{ color: {foreground}; }}"
			"QLabel#playerName { font-size: 20px; font-weight: 700; }"
			f"QLabel#stone {{ border-radius: 19px; border: 2px solid {border}; }}"
			f"QLabel#prisonersTitle, QLabel#byoyomi {{ color: {muted}; }}"
			"QLabel#prisoners { font-size: 27px; font-weight: 700; }"
			"QLabel#clock { font-family: 'DejaVu Sans Mono'; font-size: 32px; font-weight: 700; }"
			f"QLabel#points {{ font-size: 20px; font-weight: 700; color: {accent}; }}"
			f"QCheckBox {{ color: {foreground}; spacing: 7px; }}"
			"QCheckBox::indicator { width: 16px; height: 16px; }"
			f"QCheckBox::indicator:checked {{ background: {accent}; border: 1px solid {accent}; }}"
		)

		layout = QVBoxLayout(self)
		layout.setContentsMargins(18, 16, 18, 16)
		layout.setSpacing(10)

		header = QHBoxLayout()
		self.stone_label = QLabel()
		self.stone_label.setObjectName("stone")
		self.stone_label.setFixedSize(38, 38)
		self.stone_label.setStyleSheet(
			"background-color: #080808;"
			if color == Color.BLACK
			else "background-color: #ffffff;"
		)
		self.color_label = QLabel(color_name)
		self.color_label.setObjectName("playerName")
		header.addWidget(self.stone_label)
		header.addWidget(self.color_label)
		header.addStretch()
		layout.addLayout(header)

		prisoners_row = QHBoxLayout()
		prisoners_title = QLabel("GEFANGENE STEINE")
		prisoners_title.setObjectName("prisonersTitle")
		self.prisoners_label = QLabel("0")
		self.prisoners_label.setObjectName("prisoners")
		prisoners_row.addWidget(prisoners_title)
		prisoners_row.addStretch()
		prisoners_row.addWidget(self.prisoners_label)
		layout.addLayout(prisoners_row)

		self.time_label = QLabel("--:--:--")
		self.time_label.setObjectName("clock")
		self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(self.time_label)

		self.additional_time_label = QLabel("")
		self.additional_time_label.setObjectName("byoyomi")
		self.additional_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(self.additional_time_label)

		self.points_caption = QLabel("Punkte:")
		self.points_label = QLabel("")
		self.points_label.setObjectName("points")
		self.points_toggle = QCheckBox("Punkte anzeigen")
		self.points_toggle.toggled.connect(self.set_points_visible)
		points_row = QHBoxLayout()
		points_row.addWidget(self.points_toggle)
		points_row.addStretch()
		points_row.addWidget(self.points_caption)
		points_row.addWidget(self.points_label)
		layout.addLayout(points_row)
		self.set_points_visible(False)

		if timesettings is not None:
			self.set_time(timesettings.maintime)
			if timesettings.byoyomi_num > 0:
				self.set_additional_time_text(
					"Byo-yomi: "
					f"{timesettings.byoyomi_num} x {timesettings.byoyomi_time} s, "
					f"{timesettings.byoyomi_stones} Stein(e) je Periode"
				)

	def set_prisoners(self, count: int) -> None:
		self.prisoners_label.setText(str(count))

	def set_time(self, seconds: float) -> None:
		remaining = max(int(seconds), 0)
		hours, remaining = divmod(remaining, 3600)
		minutes, remaining = divmod(remaining, 60)
		self.time_label.setText(f"{hours:02d}:{minutes:02d}:{remaining:02d}")

	def set_additional_time_text(self, text: str) -> None:
		self.additional_time_label.setText(text)
		self.additional_time_label.setVisible(bool(text))

	def set_points(self, points: float) -> None:
		self.points_label.setText(str(points))

	def set_points_visible(self, visible: bool) -> None:
		self.points_caption.setVisible(visible)
		self.points_label.setVisible(visible)


def main() -> int:
	app = QApplication(sys.argv)
	widget = PlayerBox(
		Color.WHITE,
		TimeSettings(maintime=300, byoyomi_time=30, byoyomi_num=5, byoyomi_stones=1),
	)
	widget.set_prisoners(7)
	widget.set_time(245)
	widget.set_points(18.5)
	widget.points_toggle.setChecked(True)
	widget.show()
	return app.exec()


if __name__ == "__main__":
	raise SystemExit(main())
