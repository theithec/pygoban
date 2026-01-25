from . import results
from .board import Marker
from .nodescontroller import Color, Node, NodesController, Pos
from .receivers import BaseReceiver
from .rulesets import BaseRuleset, RuleViolation, ThreePasses
from .timesettings import PlayerTime


class Game:
    """A game of go (or just some moves/annotations)"""

    nodes: NodesController

    def __init__(
        self,
        ruleset: BaseRuleset,
        nodes: NodesController | None = None,
    ):
        self.ruleset = ruleset
        if not nodes:
            nodes = NodesController(self.ruleset.boardsize, self.ruleset.handicap)

        assert nodes
        self.receivers: list[BaseReceiver] = []
        self.ruleset.set_node_controller(nodes)
        self.nodes = nodes
        self._started = False
        self.timers = (
            {
                Color.BLACK: PlayerTime(self, Color.BLACK),
                Color.WHITE: PlayerTime(self, Color.WHITE),
            }
            if ruleset.timesettings and ruleset.timesettings.use_clock
            else None
        )

        self.started = False

    def _start(self, receivers: list[BaseReceiver], cursor: Node | None = None):
        """Start a game, sending the emtpy root node"""
        assert not self._started
        self._started = True
        receiver = receivers.pop(0)
        self.receivers.insert(0, receiver)
        for receiver in receivers:
            self.add_receiver(receiver)
        if cursor:
            curr = cursor
            while curr:
                if not curr.parent:
                    break
                curr = curr.parent
            self.nodes.root = curr
        else:
            self.nodes.root = Node(color=Color.EMPTY, pos=None, parent=None)
            cursor = self.nodes.root
        result = self.nodes.set_cursor(cursor)
        if self.timers:
            timer = self.timers[result.next_color]
            timer.start_timer()
            timer = self.timers[result.next_color.other()]
            result.node.annos.time_left = timer.nexttime()
            result.node.annos.stones_left = timer.byoyomi.stones_left
            result.node.annos.periods_left = timer.byoyomi.periods_left

        self.send_game_event(result)

    def _count(self, result=None):
        """Count a board position"""

        if self.timers:
            for timer in self.timers.values():
                timer.cancel_timer()
        res = result or self.ruleset.count()
        game_result = results.Counted(**res)
        self.send_game_event(game_result)

    def _place(self, color: Color, pos: Pos | None) -> None:
        """Placement of a stone or a pass if `pos` is None"""
        result = self.nodes.get_result(color, pos)
        try:
            self.ruleset.validate_result(result)
        except ThreePasses:
            self._count()
            return
        except RuleViolation as err:
            print(err)
        else:
            self.nodes.apply_result(result)
            if self.timers:  # and not color.is_empty():
                self.nodes.cursor.annos.time_left = self.timers[color].cancel_timer(is_turn=True)
                other_timer = self.timers[color.other()]
                if not other_timer.ended:
                    other_timer.start_timer()
                result.node.annos.periods_left = self.timers[color].byoyomi.periods_left
                result.node.annos.stones_left = self.timers[color].byoyomi.stones_left
            self.send_game_event(result)

    def _reset(self, node: Node):
        """Reset the board to given situation"""
        result: results.TurnDone = self.nodes.set_cursor(node)
        self.send_game_event(result)

    def start(self, receivers: list[BaseReceiver], node: Node | None = None):
        self._start(receivers=receivers, cursor=node)

    def send_game_event(self, result: results.Event):
        """Send the event to all registered recivers"""

        cls = result.__class__
        for receiver in self.receivers:
            if cls not in receiver.events:
                continue
            receiver.receive_game_event(result)

    def period_ended(self, color: Color, next_time: int):
        """A time period ended"""
        assert self.timers
        result: results.Event = results.TimeDone(
            color=color, next_time=next_time, byoyomi=self.timers[color].byoyomi
        )
        self.send_game_event(result)
        if not next_time:
            self.timers = None
            result_type = results.GameResultType.LOST_BY_TIME
            msg = results.GAME_RESULT_STR_BY_TYPE[result_type].format(color=color.other())
            result = results.GameResultDone(
                winner=color.other(), msg=msg, type=results.GameResultType.LOST_BY_TIME
            )
            self.send_game_event(result)

    def toggle_status(self, pos: Pos) -> None:
        result = self.ruleset.toggle_status(pos)
        self._count(result)

    def annotate(self, pos: Pos, name: str | Color | Marker, end: Pos | None = None) -> None:
        cursor = self.nodes.cursor
        if isinstance(name, Color):
            cursor.annos.stones[pos] = name
            cursor.apply_permanent_annos(self.nodes.board)

        elif isinstance(name, Marker):
            cursor.annos.markers[pos] = name
        elif isinstance(name, str):
            if name == "A":
                cursor.annos.chars[pos] = chr(65 + len(cursor.annos.chars))
            elif name == "1":
                numbers = [int(num) for num in cursor.annos.numbers.values()] or [0]
                cursor.annos.numbers[pos] = str(1 + max(numbers))
            elif name == "AR":
                assert end
                cursor.annos.arrows.append((pos, end))
            elif name == "LN":
                assert end
                cursor.annos.lines.append((pos, end))

        self.send_game_event(results.AnnotationDone())

    def rm_anno(self):
        action_result = results.AnnotationDone()
        self.send_game_event(action_result)

    def annotate_winrates(self, infos: dict) -> None:
        self.nodes.cursor.annos.winrates.clear()
        for pos, rate in infos.items():
            self.nodes.cursor.annos.winrates[pos] = rate
        self.send_game_event(results.AnnotationDone())

    def add_receiver(self, receiver: BaseReceiver):
        if receiver not in self.receivers:
            self.receivers.append(receiver)

    def set_end_result(self, result_type, color: Color | None = None):
        if self.timers:
            for timer in self.timers.values():
                timer.cancel_timer()

        types = results.GameResultType
        fmt = results.GAME_RESULT_STR_BY_TYPE[result_type]
        msg = ""
        match result_type:
            case types.LOST_BY_TIME | types.RESIGN:
                assert color
                winner = color.other()
                msg = fmt.format(color=winner)
            case types.COUNTED:
                count_result = self.ruleset.count()
                points_diff = abs(
                    (black_total := count_result["black"].total)
                    - (white_total := count_result["white"].total)
                )
                if black_total > white_total:
                    winner = Color.BLACK
                elif white_total > black_total:
                    winner = Color.WHITE
                else:
                    winner = Color.EMPTY

                msg = fmt.format(color=winner, points_diff=points_diff)

        result = results.GameResultDone(winner=winner, msg=msg, type=result_type)
        self.send_game_event(result)

    def quit(self):
        if self.timers:
            for timer in self.timers.values():
                timer.cancel_timer()
