from threading import Thread

from . import results
from .board import Marker
from .nodescontroller import Color, Node, NodesController, Pos
from .receivers import BaseReceiver
from .rulesets import Counter, Ruleset, RuleViolation, ThreePasses
from .timesettings import PlayerTime


class Game:
    """A game of go (or just some moves/annotations)"""

    nodes: NodesController

    def __init__(
        self,
        ruleset: Ruleset,
        nodes: NodesController | None = None,
    ):
        self.ruleset = ruleset
        if not nodes:
            nodes = NodesController(self.ruleset.boardsize, self.ruleset.handicap)
        assert nodes
        self.receivers: list[BaseReceiver] = []
        self.ruleset.set_node_controller(nodes)
        self.nodes = nodes
        self._event_threads: list[Thread] = []
        self._started = False
        self.timers = (
            {
                Color.BLACK: PlayerTime(self, Color.BLACK),
                Color.WHITE: PlayerTime(self, Color.WHITE),
            }
            if ruleset.timesettings
            else None
        )

        self.started = False

    def send_game_event(self, result: results.Event):
        """Send the event to all registered recivers"""
        for receiver in self.receivers:
            if not result.__class__ in receiver.events:
                continue
            receiver.receive_game_event(result)
            # thread = Thread(target=receiver.receive_game_event, args=(result,))
            # self._event_threads.append(thread)
            # thread.start()

    def period_ended(self, color: Color, next_time: int):
        """A time period ended"""
        if not (timers := self.timers):
            return
        result: results.Event = results.TimeDone(
            color=color, next_time=next_time, byoyomi=timers[color].byoyomi
        )
        self.send_game_event(result)
        if not next_time:
            result_type = results.GameResultType.LOST_BY_TIME
            msg = results.GAME_RESULT_STR_BY_TYPE[result_type].format(color=color.other())
            result = results.GameResultDone(
                winner=color.other(), msg=msg, type=results.GameResultType.LOST_BY_TIME
            )
            self.send_game_event(result)

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
            self.timers[result.next_color].start_timer()
            result.node.annos.time_left = {
                Color.BLACK: self.timers[result.next_color].nexttime(),
                Color.WHITE: self.timers[result.next_color.other()].nexttime(),
            }

        self.send_game_event(result)

    def _count(self):
        """Count a board position"""

        if self.timers:
            for timer in self.timers.values():
                timer.cancel_timer()
        cnt = Counter(board=self.nodes.board)
        coords, killed = cnt.result()
        game_result = results.Counted(
            black=results.ColorResult(killed=killed[Color.WHITE], coords=coords[Color.BLACK]),
            white=results.ColorResult(killed=killed[Color.BLACK], coords=coords[Color.WHITE]),
        )
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
            if self.timers:
                next_next_time = self.timers[color].cancel_timer(is_turn=True)
                curr_next_time = (other_timer := self.timers[color.other()]).nexttime()
                self.nodes.cursor.annos.time_left = {
                    color.other(): curr_next_time,
                    color: next_next_time,
                }
                if not other_timer.ended:
                    other_timer.start_timer()
                result.byoyomi = self.timers[color].byoyomi
            self.send_game_event(result)

    def _reset(self, node: Node):
        """Reset the board to given situation"""
        result: results.TurnDone = self.nodes.set_cursor(node)
        self.send_game_event(result)

    # def undo(self):
    #    if parent := self.nodes.cursor.parent:
    #        self._reset(parent)

    def start(self, receivers: list[BaseReceiver], node: Node | None = None):
        assert not self.started
        self._start(receivers=receivers, cursor=node)
        self.started = True

    def toggle_status(self, pos: Pos) -> None:
        chain = self.nodes.board.get_chain(pos)
        start = self.nodes.board.intersection(pos)
        owner = (
            None if start.owner else (Color.BLACK if start.color == Color.WHITE else Color.WHITE)
        )
        for cpos in chain:
            inter = self.nodes.board.intersection(cpos)
            inter.owner = owner
        self._count()

    def annotate(self, pos: Pos, name: str | Color | Marker) -> None:
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
                cursor.annos.numbers[pos] = str(1 + len(cursor.annos.numbers))

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
        print("Print TODO WRITE RESULT")
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
                cnt = Counter(board=self.nodes.board)
                coords, killed = cnt.result()
                for color in (Color.BLACK, Color.WHITE):
                    killed[color] += self.nodes.total_dead[color.other()] + len(coords[color])
                killed[Color.WHITE] += self.ruleset.komi
                winner = max(killed, key=killed.get)
                points_diff = killed[winner] - killed[winner.other()]

                msg = fmt.format(color=winner, points_diff=points_diff)

        result = results.GameResultDone(winner=winner, msg=msg, type=result_type)
        self.send_game_event(result)

    def quit(self):
        if self.timers:
            for timer in self.timers.values():
                timer.cancel_timer()
