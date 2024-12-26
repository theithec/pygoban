import sys

from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout


app = QApplication(sys.argv)
gw = QWidget()
layout = QVBoxLayout()
for i in range(0, 100, 5):
    btn = QPushButton(str(i))
    v = int(i * 2.55)
    r, g, b = 255 - v, v // 1, 0
    luminace = float(0.2126 * r + 0.7152 * g + 0.0722 * b)
    fg = "black" if luminace > 75 else "white"
    print("vi", i, r, g, b, fg)
    btn.setStyleSheet(f"background-color: rgb({r},{g}, {b}); color: {fg};")
    layout.addWidget(btn)
gw.setLayout(layout)
gw.show()

# Start the event loop.
app.exec()
