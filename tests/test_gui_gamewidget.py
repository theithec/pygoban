from unittest.mock import Mock, patch

from pygoban import Color, Marker, Pos, results
from pygoban.gui import GUIMode
from pygoban.gui.gamewidget import GameWidget, GuiReceiver


class TestGameWidget:
    def test_placement(self, game_widget: GameWidget):
        i1 = game_widget.boardwidget.intersections[Pos(0, 0)]
        game_widget.inter_clicked(i1, is_rightclick=False)

    def test_initialization(self, game_widget: GameWidget):
        """Test GameWidget initialization"""
        assert game_widget.parties is not None
        assert game_widget.controller is not None
        assert game_widget.boardwidget is not None
        assert game_widget.boardoverlay is not None
        assert game_widget.bar is not None
        assert game_widget.ruleset is not None
        assert game_widget.receiver is not None
        assert game_widget.gui_mode == GUIMode.EDIT
        assert game_widget.initial_gui_mode == GUIMode.EDIT
        assert game_widget.show_analyzed_variation is False

    def test_gui_mode_property(self, game_widget: GameWidget):
        """Test gui_mode property setter and getter"""
        # Test initial mode
        assert game_widget.gui_mode == GUIMode.EDIT

        # Test mode change
        game_widget.gui_mode = GUIMode.COUNT
        assert game_widget.gui_mode == GUIMode.COUNT

        # Test mode change listener
        mock_listener = Mock()
        game_widget.mode_change_listeners.append(mock_listener)
        game_widget.gui_mode = GUIMode.EDIT
        mock_listener.mode_changed.assert_called_once_with(GUIMode.EDIT)

    def test_inter_clicked_left_click_normal_play(self, game_widget: GameWidget):
        """Test left click for normal stone placement"""
        # Get an intersection
        iwidget = game_widget.boardwidget.intersections[Pos(0, 0)]

        # Mock the controller play method
        game_widget.controller.play = Mock()

        # Simulate left click
        game_widget.inter_clicked(iwidget, is_rightclick=False)

        # Should call controller.play
        game_widget.controller.play.assert_called_once()

    def test_inter_clicked_left_click_annotation(self, game_widget: GameWidget):
        """Test left click with annotation mode"""
        iwidget = game_widget.boardwidget.intersections[Pos(0, 0)]

        # Set annotation type
        game_widget.annotation_type = "TR"
        game_widget.controller.annotate = Mock()

        # Click with annotation
        game_widget.inter_clicked(iwidget, is_rightclick=False)

        # Should call controller.annotate
        game_widget.controller.annotate.assert_called_once_with(
            pos=Pos(0, 0), name=Marker.TR, end=None
        )

    def test_inter_clicked_left_click_number_annotation(self, game_widget: GameWidget):
        """Test left click with number annotation"""
        iwidget = game_widget.boardwidget.intersections[Pos(0, 0)]

        # Set number annotation
        game_widget.annotation_type = "1"
        game_widget.controller.annotate = Mock()

        # Click with annotation
        game_widget.inter_clicked(iwidget, is_rightclick=False)

        game_widget.controller.annotate.assert_called_once_with(pos=Pos(0, 0), name="1", end=None)

    def test_inter_clicked_left_click_arrow_annotation_first_click(self, game_widget: GameWidget):
        """Test first click for arrow annotation"""
        iwidget = game_widget.boardwidget.intersections[Pos(0, 0)]

        # Set arrow annotation
        game_widget.annotation_type = "AR"
        game_widget.controller.annotate = Mock()

        # First click should set start position
        game_widget.inter_clicked(iwidget, is_rightclick=False)

        # Should not call annotate yet, just set start position
        game_widget.controller.annotate.assert_not_called()
        assert game_widget.boardoverlay.startpos == Pos(0, 0)

    def test_inter_clicked_left_click_arrow_annotation_second_click(self, game_widget: GameWidget):
        """Test second click for arrow annotation"""
        iwidget1 = game_widget.boardwidget.intersections[Pos(0, 0)]
        iwidget2 = game_widget.boardwidget.intersections[Pos(1, 0)]

        # Set arrow annotation and set start position
        game_widget.annotation_type = "AR"
        game_widget.boardoverlay.startpos = Pos(0, 0)
        game_widget.controller.annotate = Mock()

        # Second click should complete arrow
        game_widget.inter_clicked(iwidget2, is_rightclick=False)

        game_widget.controller.annotate.assert_called_once_with(
            pos=Pos(0, 0), name="AR", end=Pos(1, 0)
        )
        assert game_widget.boardoverlay.startpos is None

    def test_inter_clicked_count_mode(self, game_widget: GameWidget):
        """Test click in count mode"""
        # Set up count mode and a stone on the board
        game_widget.gui_mode = GUIMode.COUNT
        game_widget.controller.toggle_status = Mock()

        iwidget = game_widget.boardwidget.intersections[Pos(0, 0)]

        # Mock the board intersection to have a stone
        if game_widget.last_turn:
            game_widget.last_turn.board.intersection = Mock(return_value=Mock(color=Color.BLACK))

        # Click in count mode
        game_widget.inter_clicked(iwidget, is_rightclick=False)

        game_widget.controller.toggle_status.assert_called_once_with(Pos(0, 0))

    def test_inter_clicked_right_click_annotation_removal(self, game_widget: GameWidget):
        """Test right click to remove annotations"""
        game_widget.gui_mode = GUIMode.EDIT
        game_widget.annotation_type = "TR"
        game_widget.controller.annotate = Mock()
        game_widget.controller.rm_anno = Mock()

        # Set up annotations with a triangle marker
        if game_widget.last_turn and game_widget.last_turn.node:
            game_widget.last_turn.node.annos.markers[Pos(0, 0)] = Marker.TR

        iwidget = game_widget.boardwidget.intersections[Pos(0, 0)]

        # Right click should remove annotation
        game_widget.inter_clicked(iwidget, is_rightclick=True)

        game_widget.controller.rm_anno.assert_called_once()

    def test_undo(self, game_widget: GameWidget):
        """Test undo functionality"""
        game_widget.controller.do_prev_stone = Mock()

        # Change gui mode first
        game_widget.gui_mode = GUIMode.COUNT

        # Call undo
        game_widget.undo()

        # Should reset to initial mode and go back one stone
        assert game_widget.gui_mode == GUIMode.EDIT
        game_widget.controller.do_prev_stone.assert_called_once()

    @patch("pygoban.gui.gamewidget.copy")
    def test_open_as_new(self, mock_copy, game_widget: GameWidget):
        """Test opening game as new"""
        mock_ruleset = Mock()
        mock_copy.return_value = mock_ruleset

        game_widget.main_ui.add_game = Mock()

        # Mock the node chain if last_turn exists
        if game_widget.last_turn and game_widget.last_turn.node:
            mock_root = Mock()
            mock_root.as_copy.return_value = Mock()
            game_widget.last_turn.node.root = Mock(return_value=mock_root)

        game_widget.open_as_new()

        game_widget.main_ui.add_game.assert_called_once()
        mock_copy.assert_called_once_with(game_widget.ruleset)

    def test_navigation_shortcuts(self, game_widget: GameWidget):
        """Test navigation shortcuts are created"""
        # Check that shortcuts are created (should be 4 for up, down, left, right)
        assert len(game_widget.nav_shortcuts) == 4

    def test_gameended_signal(self, game_widget: GameWidget):
        """Test game ended signal"""
        # Test that the signal exists
        assert hasattr(game_widget, "gameended_signal")

        # Test signal emission
        mock_slot = Mock()
        game_widget.gameended_signal.connect(mock_slot)

        game_widget.gameended_signal.emit("Test message")
        mock_slot.assert_called_once_with("Test message")


class TestGuiReceiver:
    def test_gui_receiver_initialization(self, game_widget: GameWidget):
        """Test GuiReceiver initialization"""
        receiver = GuiReceiver(game_widget)

        assert receiver.game_ui == game_widget
        assert results.TurnDone in receiver.events
        assert results.AnnotationDone in receiver.events
        assert results.Counted in receiver.events
        assert results.GameResultDone in receiver.events

    def test_received_turn(self, game_widget: GameWidget):
        """Test handling of turn done event"""
        receiver = GuiReceiver(game_widget)

        # Mock the board widget update and stone sound
        game_widget.boardwidget.update = Mock()
        game_widget.stonesound.play = Mock()

        # Create a mock turn result
        mock_result = Mock()
        mock_result.node.color = Color.BLACK
        mock_result.node.pos = Pos(0, 0)

        receiver.received_turn(mock_result)

        game_widget.boardwidget.update.assert_called()
        # game_widget.stonesound.play.assert_called()

    def test_received_turn_empty_intersection(self, game_widget: GameWidget):
        """Test handling of turn with empty intersection"""
        receiver = GuiReceiver(game_widget)

        game_widget.boardwidget.update = Mock()
        game_widget.stonesound.play = Mock()

        # Mock turn with empty color
        mock_result = Mock()
        mock_result.node.color = Color.EMPTY

        receiver.received_turn(mock_result)

        game_widget.boardwidget.update.assert_called()
        game_widget.stonesound.play.assert_not_called()

    def test_received_annotated(self, game_widget: GameWidget):
        """Test handling of annotation event"""
        receiver = GuiReceiver(game_widget)
        game_widget.boardwidget.update = Mock()

        mock_result = Mock()
        receiver.received_annotated(mock_result)

        game_widget.boardwidget.update.assert_called_once()

    def test_received_count(self, game_widget: GameWidget):
        """Test handling of count event"""
        receiver = GuiReceiver(game_widget)
        game_widget.boardwidget.update = Mock()

        mock_result = Mock()
        receiver.received_count(mock_result)

        assert game_widget.gui_mode == GUIMode.COUNT
        game_widget.boardwidget.update.assert_called_once()

    def test_received_result_done(self, game_widget: GameWidget):
        """Test handling of result done event"""
        receiver = GuiReceiver(game_widget)
        game_widget.boardwidget.update = Mock()

        # Mock controller sub-controllers
        mock_subctrl = Mock()
        game_widget.controller._subs = {"sub1": mock_subctrl}

        mock_result = Mock()
        receiver.received_result_done(mock_result)

        assert game_widget.gui_mode == GUIMode.EDIT
        mock_subctrl.quit.assert_called_once()
        game_widget.boardwidget.update.assert_called_once()
