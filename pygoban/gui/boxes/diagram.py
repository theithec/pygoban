from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QHBoxLayout  # pylint: disable=no-name-in-module

from pygoban import results
from pygoban.gui.boxes import Box


class DiagramBox(Box):
    name = "Diagram"

    def init(self, **kwargs):
        layout = QHBoxLayout()
        self.cnt = 0
        self.events = {results.AnnotationDone, results.TurnDone}

        self.chart = QChart()
        self.xaxis = QValueAxis(self.chart)
        self.xaxis.setRange(-100, 100)
        self.chart.addAxis(self.xaxis, Qt.AlignmentFlag.AlignLeft)
        self.yaxis = QValueAxis(self.chart)
        self.yaxis.setRange(0, 100)
        self.chart.addAxis(self.yaxis, Qt.AlignmentFlag.AlignBottom)
        # self.zeroline = QLineSeries()
        # self.zeroline.append(1, 10)
        # self.zeroline.append(100, 10)
        # self.series.append(20, 30)
        # self.series.append(30, -20)
        # self.series.append(30, 10)
        # self.series.append(40, 10)
        # self.series.append(50, -20)
        # self.series.append(60, -10)
        self.turnlines = QLineSeries()
        self.turnlines.append(10, 10)
        self.turnlines.append(20, -10)
        self.turnlines.append(30, 10)
        self.cnt = 30
        # self.turnlines.append(30, 12)
        # self.s2.append(10, 0)
        # self.zeroline.setName("WInrate")
        # self.s2.append(30, 0)

        # self.s2.append(60, 0)
        # self.chart.legend().hide()
        self.chart.addSeries(self.turnlines)
        # self.chart.addSeries(self.zeroline)
        # self.chart.addSeries(self.s2)
        # self.chart.createDefaultAxes()
        self.chart.setTitle("Simple line chart exampl2e")

        self._chart_view = QChartView(self.chart)
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        layout.addWidget(self._chart_view)
        self.setLayout(layout)

    def received_annotated(self, result: results.AnnotationDone) -> None:
        print("Anno", result)

    def received_turn(self, result: results.TurnDone) -> None:
        print("R turn")
        self.turnlines.clear()
        self.turnlines.append(self.cnt, self.cnt // 2)
        self.cnt += 10
        self.turnlines.append(self.cnt, self.cnt)
        self._chart_view.update()
        # self.chart.removeAxis(self.xaxis)
        # self.chart.removeAxis(self.yaxis)
