from pygoban import Board, Color, Pos, Intersection


def test_kill():
    board = Board(5)
    board[1][0] = Intersection(Color.BLACK)
    board[0][0] = Intersection(Color.WHITE)
    board[0][1] = Intersection(Color.BLACK)
    result = board.analyze(Pos(0, 1))
    assert result[0] == set([Pos(0, 0)])
    board[1][1] = Color.BLACK
    result = board.analyze(Pos(1, 1))
    assert result[0] == set()


def test_chain():
    board = Board(5)
    board[1][0] = Intersection(Color.BLACK)
    board[2][0] = Intersection(Color.BLACK)
    assert (
        board.get_chain(Pos(1, 0))
        == board.get_chain(Pos(2, 0))
        == set((Pos(1, 0), Pos(2, 0)))
    )


def test_rectangular_board():
    board = Board(9, 13)

    assert board.boardsize == 9
    assert board.boardheight == 13
    assert len(board) == 9
    assert len(board[0]) == 13
    assert set(board.adjacent_ins(Pos(8, 12))) == {Pos(7, 12), Pos(8, 11)}
    assert len(list(board.iter())) == 9 * 13
