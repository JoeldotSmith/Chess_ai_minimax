import pygame as p
import sys
import smartMoveFinder

class GameState:
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_col = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    col_to_files = {v: k for k, v in files_to_col.items()}

    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]
        self.move_functions = {"p": self.get_pawn_moves, "R": self.get_rook_moves, "N": self.get_knight_moves,
                               "B": self.get_bishop_moves, "Q": self.get_queen_moves, "K": self.get_king_moves}

        self.whiteToMove = True
        self.moveLog = []
        self.moveList = []
        self.white_king_loc = (7, 4)
        self.black_king_loc = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.enpassentPossible = ()
        self.currentCastlingRight = CastleRights(True, True, True, True)
        self.castleRightLog = [CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                            self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)]
        self.is_castled = False

    def get_fen(self):
        fen = ""
        for row in self.board:
            counter = 0
            for piece in row:
                letter = piece[1]

                if piece[0] == "b":
                    if counter != 0:
                        fen += str(counter)
                        counter = 0

                    letter.lower()
                    letter += fen
                if piece[0] == "w":
                    if counter != 0:
                        counter += fen
                        counter = 0

                    letter.upper()
                    letter += fen

                if piece[0] == "-":
                    counter += 1

            fen += "/"

        fen = fen[:-1]

        if self.whiteToMove:
            fen += " w "
        else:
            fen += " b "

        if self.currentCastlingRight.wks:
            fen += "K"
        if self.currentCastlingRight.wqs:
            fen += "Q"
        if self.currentCastlingRight.bks:
            fen += "k"
        if self.currentCastlingRight.bqs:
            fen += "q"
        if not self.currentCastlingRight.wks and not self.currentCastlingRight.wqs \
                and not self.currentCastlingRight.bks and not self.currentCastlingRight.bqs:
            fen += " -"

        if self.enpassentPossible != ():
            x = self.enpassentPossible[0]
            y = self.enpassentPossible[1]
            fen += " " + self.col_to_files[x] + self.rows_to_ranks[y]
        else:
            fen += " -"

        fen += " 0"

        fen += " 0"

        return fen


    def make_move(self, move):
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_move
        self.moveLog.append(move)
        self.whiteToMove = not self.whiteToMove
        if move.piece_move == "wK":
            self.white_king_loc = (move.end_row, move.end_col)
        if move.piece_move == "bK":
            self.black_king_loc = (move.end_row, move.end_col)

        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.piece_move[0] + "Q"

        if move.is_enpassent:
            self.board[move.start_row][move.end_col] = "--"

        if (move.piece_move[1]) == "p" and (abs(move.start_row - move.end_row) == 2):
            self.enpassentPossible = ((move.start_row + move.end_row)//2, move.start_col)
        else:
            self.enpassentPossible = ()

        if move.is_castle:
            self.is_castled = True
            if move.end_col - move.start_col == 2:  # kingside
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"
            else:  # queenside
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2]
                self.board[move.end_row][move.end_col - 2] = "--"

        self.updateCastleRights(move)
        self.castleRightLog.append(CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                                self.currentCastlingRight.wqs, self.currentCastlingRight.bqs))

    def undo_move(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.start_row][move.start_col] = move.piece_move
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.whiteToMove = not self.whiteToMove
            if move.piece_move == "wK":
                self.white_king_loc = (move.start_row, move.start_col)
            if move.piece_move == "bK":
                self.black_king_loc = (move.start_row, move.start_col)

            if move.is_enpassent:
                self.board[move.end_row][move.end_col] = "--"
                self.board[move.start_row][move.end_col] = move.piece_captured
                self.enpassentPossible = (move.end_row, move.end_col)

            if (move.piece_move[1]) == "p" and (abs(move.start_row - move.end_row) == 2):
                self.enpassentPossible = ()

            self.castleRightLog.pop()
            newRights = self.castleRightLog[-1]
            self.currentCastlingRight = CastleRights(newRights.wks, newRights.bks, newRights.wqs, newRights.bqs)

            if move.is_castle:
                self.is_castled = False
                if move.end_col - move.start_col == 2:
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = "--"
                else:
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = "--"

            self.checkmate = False
            self.stalemate = False



    def updateCastleRights(self, move):
        if move.piece_move == "wK":
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.piece_move == "bK":
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        elif move.piece_move == "wR":
            if move.start_row == 7:
                if move.start_col == 0:
                    self.currentCastlingRight.wqs = False
                elif move.start_col == 7:
                    self.currentCastlingRight.wks = False
        elif move.piece_move == "bR":
            if move.start_row == 0:
                if move.start_col == 0:
                    self.currentCastlingRight.bqs = False
                elif move.start_col == 7:
                    self.currentCastlingRight.bks = False


    def get_valid_moves(self):
        tempEnpassentPossible = self.enpassentPossible
        tempCastleRights = CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                        self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)
        moves = self.get_all_possible_moves()
        if self.whiteToMove:
            self.get_castle_moves(self.white_king_loc[0], self.white_king_loc[1], moves)
        else:
            self.get_castle_moves(self.black_king_loc[0], self.black_king_loc[1], moves)
        for i in range(len(moves) - 1, -1, -1):
            self.make_move(moves[i])
            self.whiteToMove = not self.whiteToMove
            if self.in_check():
                moves.remove(moves[i])
            self.whiteToMove = not self.whiteToMove
            self.undo_move()

        if len(moves) == 0:
            if self.in_check():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        if self.checkDraw(self.board):
            self.stalemate = True

        self.currentCastlingRight = tempCastleRights
        self.enpassentPossible = tempEnpassentPossible
        return moves

    def checkDraw(self, board):
        black_pieces = []
        white_pieces = []
        for r in range(len(board)):
            for c in range(len(board[r])):
                piece = board[r][c]
                if piece != "--":
                    colour = piece[0]
                    if colour == "b":
                        black_pieces.append(piece)
                    else:
                        white_pieces.append(piece)
        if black_pieces.__contains__("bK") and len(black_pieces) == 1:
            if white_pieces.__contains__("wK") and len(white_pieces) == 1:
                return True

        if (black_pieces.__contains__("bK") and black_pieces.__contains__("bN")) and len(black_pieces) == 2:
            if white_pieces.__contains__("wK") and len(white_pieces) == 1:
                return True

        if (white_pieces.__contains__("wK") and white_pieces.__contains__("wN")) and len(white_pieces) == 2:
            if black_pieces.__contains__("bK") and len(black_pieces) == 1:
                return True

        if (black_pieces.__contains__("bK") and black_pieces.__contains__("bB")) and len(black_pieces) == 2:
            if white_pieces.__contains__("wK") and len(white_pieces) == 1:
                return True

        if (white_pieces.__contains__("wK") and white_pieces.__contains__("wB")) and len(white_pieces) == 2:
            if black_pieces.__contains__("bK") and len(black_pieces) == 1:
                return True

        if len(self.moveList) >= 10:
            a = self.moveList[len(self.moveList) - 1]
            b = self.moveList[len(self.moveList) - 5]
            c = self.moveList[len(self.moveList) - 9]
            x = self.moveList[len(self.moveList) - 2]
            y = self.moveList[len(self.moveList) - 6]
            z = self.moveList[len(self.moveList) - 10]
            if a == b and b == c:
                if x == y and y == z:
                    return True

        return False

    def in_check(self):
        if self.whiteToMove:
            return self.sq_under_attack(self.white_king_loc[0], self.white_king_loc[1])
        if not self.whiteToMove:
            return self.sq_under_attack(self.black_king_loc[0], self.black_king_loc[1])

    def sq_under_attack(self, r, c):
        self.whiteToMove = not self.whiteToMove
        opp_move = self.get_all_possible_moves()
        for move in opp_move:
            if move.end_row == r and move.end_col == c:
                self.whiteToMove = not self.whiteToMove
                return True
        self.whiteToMove = not self.whiteToMove
        return False

    def get_all_possible_moves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == "w" and self.whiteToMove) or (turn == "b" and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.move_functions[piece](r, c, moves)

        return moves

    def get_pawn_moves(self, r, c, moves):
        if self.whiteToMove:
            if self.board[r - 1][c] == "--":
               moves.append(Move((r, c), (r - 1, c), self.board))
               if r == 6 and self.board[r - 2][c] == "--":
                   moves.append(Move((r, c), (r - 2, c), self.board))

            if c-1 >= 0:
                if self.board[r-1][c-1][0] == "b":
                    moves.append(Move((r, c), (r - 1, c - 1), self.board))
                elif (r-1, c-1) == self.enpassentPossible:
                    moves.append(Move((r, c), (r - 1, c - 1), self.board, isEnpassentMove=True))

            if c+1 <= 7:
                if self.board[r-1][c+1][0] == "b":
                    moves.append(Move((r, c), (r - 1, c + 1), self.board))
                elif (r-1, c+1) == self.enpassentPossible:
                    moves.append(Move((r, c), (r - 1, c + 1), self.board, isEnpassentMove=True))

        else:
            if self.board[r + 1][c] == "--":
               moves.append(Move((r, c), (r + 1, c), self.board))
               if r == 1 and self.board[r + 2][c] == "--":
                   moves.append(Move((r, c), (r + 2, c), self.board))

            if c-1 >= 0:
                if self.board[r+1][c-1][0] == "w":
                    moves.append(Move((r, c), (r + 1, c - 1), self.board))
                elif (r+1, c-1) == self.enpassentPossible:
                    moves.append(Move((r, c), (r + 1, c - 1), self.board, isEnpassentMove=True))

            if c+1 <= 7:
                if self.board[r+1][c+1][0] == "w":
                    moves.append(Move((r, c), (r + 1, c + 1), self.board))
                elif (r+1, c+1) == self.enpassentPossible:
                    moves.append(Move((r, c), (r + 1, c + 1), self.board, isEnpassentMove=True))

    def get_rook_moves(self, r, c, moves):
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemy_colour = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--":
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    elif end_piece[0] == enemy_colour:
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_knight_moves(self, r, c, moves):
        knight_moves = ((-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2))
        ally_colour = "w" if self.whiteToMove else "b"
        for m in knight_moves:
            end_row = r + m[0]
            end_col = c + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_colour:
                    moves.append(Move((r, c), (end_row, end_col), self.board))

    def get_bishop_moves(self, r, c, moves):
        directions = ((-1, -1), (1, -1), (-1, 1), (1, 1))
        enemy_colour = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--":
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    elif end_piece[0] == enemy_colour:
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_queen_moves(self, r, c, moves):
        self.get_bishop_moves(r, c, moves)
        self.get_rook_moves(r, c, moves)

    def get_king_moves(self, r, c, moves):
        king_moves = ((1, 1), (-1, 1), (1, -1), (-1, -1), (0, 1), (0, -1), (1, 0), (-1, 0))
        ally_colour = "w" if self.whiteToMove else "b"
        for i in range(8):
            end_row = r + king_moves[i][0]
            end_col = c + king_moves[i][1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_colour:
                    moves.append(Move((r, c), (end_row, end_col), self.board))


    def get_castle_moves(self, r, c, moves):
        if self.sq_under_attack(r, c):
            return
        if (self.whiteToMove and self.currentCastlingRight.wks) or \
                (not self.whiteToMove and self.currentCastlingRight.bks):
            self.kingside_castle_moves(r, c, moves)

        if (self.whiteToMove and self.currentCastlingRight.wqs) or \
                (not self.whiteToMove and self.currentCastlingRight.bqs):
            self.queenside_castle_moves(r, c, moves)

    def kingside_castle_moves(self, r, c, moves):
        if self.board[r][c + 1] == "--" and self.board[r][c + 2] == "--":
            if not self.sq_under_attack(r, c + 1) and not self.sq_under_attack(r, c + 2):
                moves.append(Move((r, c), (r, c + 2), self.board, isCastleMove=True))

    def queenside_castle_moves(self, r, c, moves):
        if self.board[r][c - 1] == "--" and self.board[r][c - 2] == "--" and self.board[r][c - 3] == "--":
            if not self.sq_under_attack(r, c - 1) and not self.sq_under_attack(r, c - 2):
                moves.append(Move((r, c), (r, c - 2), self.board, isCastleMove=True))

class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs

class Move:
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_col = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    col_to_files = {v: k for k, v in files_to_col.items()}

    def __init__(self, start_sq, end_sq, board, isEnpassentMove=False, isCastleMove=False):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.piece_move = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        self.is_pawn_promotion = False
        self.is_enpassent = isEnpassentMove
        self.is_castle = isCastleMove

        if self.is_enpassent:
            self.piece_captured = "wp" if self.piece_move == "bp" else "bp"

        if (self.piece_move == "wp" and self.end_row == 0) or (self.piece_move == "bp" and self.end_row == 7):
            self.is_pawn_promotion = True

        self.move_ID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_ID == other.move_ID
        return False

    def get_chess_notation(self, gs):
        if self.piece_captured != "--":
            takes = "x"
        else:
            takes = ""

        piece = self.piece_move[1]

        if piece == "p":
            if takes == "x":
                piece = self.col_to_files[self.start_col]
            else:
                piece = ""

        location = self.get_rank_file(self.end_row, self.end_col)

        move = piece + takes + location

        if move == "Kg1":
            move = "0-0"
        if move == "Kc1":
            move = "0-0-0"

        if gs.in_check():
            if gs.checkmate:
                move += "#"
            else:
                move += "+"

        return move


    def get_rank_file(self, r, c):
        return self.col_to_files[c] + self.rows_to_ranks[r]

p.init()
p.font.init()
font = p.font.SysFont("montserrat", 60)
p.display.set_caption("Chess")

BLACK = (0, 0, 0)
RED = (224, 52, 92)
BLUE = (75, 115, 153)
WHITE = (255, 255, 255)
WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}
RUN = True

def load_images():
    pieces = ["wp", "wR", "wN", "wB", "wK", "wQ", "bp", "bR", "bN", "bB", "bK", "bQ"]

    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load(piece + ".png"), (SQ_SIZE, SQ_SIZE))

def draw_board(screen):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            if (r+c) % 2 == 1:
                p.draw.rect(screen, BLUE, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            if (r+c) % 2 == 0:
                p.draw.rect(screen, WHITE, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def draw_pieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def main():
    screen = p.display.set_mode((WIDTH, HEIGHT))

    clock = p.time.Clock()
    gs = GameState()
    valid_moves = gs.get_valid_moves()
    move_made = False

    sq_selected = ()
    player_clicks = []
    playerOne = True
    playerTwo = False

    load_images()

    while RUN:
        clock.tick(MAX_FPS)

        humanMove = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)

        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()

            if event.type == p.KEYDOWN:
                if event.key == p.K_LEFT:
                    gs.undo_move()
                    move_made = True

            if event.type == p.MOUSEBUTTONDOWN:
                if humanMove:
                    location = p.mouse.get_pos()
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    if sq_selected == (row, col):
                        sq_selected = ()
                        player_clicks = []
                    else:
                        sq_selected = (row, col)
                        player_clicks.append(sq_selected)

                    if len(player_clicks) == 2:
                        move = Move(player_clicks[0], player_clicks[1], gs.board)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                gs.make_move(valid_moves[i])
                                gs.moveList.append((move.get_chess_notation(gs)))
                                move_made = True
                                # print(gs.get_fen())
                                sq_selected = ()
                                player_clicks = []
                        if not move_made:
                            player_clicks = [sq_selected]

        if not gs.checkmate and not gs.stalemate and not humanMove:
            AImove = smartMoveFinder.findBestMove(gs, valid_moves)
            if AImove is None:
                AImove = smartMoveFinder.findRandomMove(valid_moves)
            gs.make_move(AImove)
            gs.moveList.append(AImove.get_chess_notation(gs))
            move_made = True

        if move_made:
            valid_moves = gs.get_valid_moves()
            move_made = False

        draw_board(screen)
        if sq_selected != ():
            if gs.board[sq_selected[0]][sq_selected[1]] != "--":
                p.draw.rect(screen, RED, p.Rect(sq_selected[1] * SQ_SIZE, sq_selected[0] * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        draw_pieces(screen, gs.board)

        if gs.checkmate:
            text = font.render("Checkmate!", True, BLACK)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(text, text_rect)
        if gs.stalemate:
            text = font.render("Draw!", True, BLACK)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

            screen.blit(text, text_rect)

        p.display.update()

main()
