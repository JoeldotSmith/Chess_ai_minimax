import random


pieceScores = {"K": 0, "Q": 9, "R": 5, "B": 3, "N": 3, "p": 1}
CHECKMATE = 1000
STALEMATE = 0
DEPTH = 3
inBook = True
nextMove = None




def findRandomMove(validMoves):
    i = random.randint(0, len(validMoves) - 1)

    return validMoves[i]


def findBestMove(gs, validMoves):
    global nextMove
    if inBook:
        nextMove = checkOpeningBook(gs, gs.moveList, validMoves)

    if not inBook:
        nextMove = None
        findMoveNegaMaxAlphaBeta(gs, validMoves, DEPTH, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1)
    return nextMove


def findMoveMinMax(gs, validMoves, depth, whiteToMove):
    global nextMove

    if depth == 0:
        return scoreMaterial(gs.board, gs, validMoves)

    if whiteToMove:
        maxScore = -CHECKMATE
        for move in validMoves:
            gs.make_move(move)
            nextMoves = gs.get_valid_moves()
            score = findMoveMinMax(gs, nextMoves, depth - 1, False)
            if score > maxScore:
                maxScore = score
                if depth == DEPTH:
                    nextMove = move
            gs.undo_move()
        return maxScore

    else:
        minScore = CHECKMATE
        for move in validMoves:
            gs.make_move(move)
            nextMoves = gs.get_valid_moves()
            score = findMoveMinMax(gs, nextMoves, depth - 1, True)
            if score < minScore:
                minScore = score
                if depth == DEPTH:
                    nextMove = move
            gs.undo_move()
        return minScore


def findMoveNegaMax(gs, validMoves, depth, turnMultiplier):
    global nextMove
    if depth == 0:
        return turnMultiplier * scoreMaterial(gs.board, gs, validMoves)

    maxScore = -CHECKMATE
    random.shuffle(validMoves)
    for move in validMoves:
        gs.make_move(move)
        nextMoves = gs.get_valid_moves()
        score = -findMoveNegaMax(gs, nextMoves, depth - 1, -turnMultiplier)
        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
        gs.undo_move()
    return maxScore


def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier):
    global nextMove
    if depth == 0:
        return turnMultiplier * scoreMaterial(gs.board, gs, validMoves)

    maxScore = -CHECKMATE
    for move in validMoves:
        gs.make_move(move)
        nextMoves = gs.get_valid_moves()
        score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier)
        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
        gs.undo_move()
        if maxScore > alpha:
            alpha = maxScore
        if alpha >= beta:
            break
    return maxScore



def scoreMaterial(board, gs, validMoves):
    score = 0
    nWPieces = 0
    nBPieces = 0

    if gs.checkmate:
        if gs.whiteToMove:
            return -CHECKMATE
        else:
            return CHECKMATE
    if gs.stalemate:
        return STALEMATE

    for row in board:
        for square in row:
            if square[0] == "w":
                score += pieceScores[square[1]] * 1.5
                nWPieces += 1
            if square[0] == "b":
                score -= pieceScores[square[1]] * 1.5
                nBPieces += 1

    if gs.whiteToMove:
        activityScore = (len(validMoves)/nWPieces) * 0.25
        for i in range(8):
            if gs.board[7][i] == ("wN" or "wB"):
                activityScore -= 0.1

    else:
        activityScore = len(validMoves)/nBPieces
        for i in range(8):
            if gs.board[0][i] == ("bN" or "bB"):
                activityScore -= 0.1


    for i in range(4):
        for j in range(4):
            square = board[2 + i][2 + j]
            if (1 <= i <= 2) and (1 <= j <= 2):
                scoreIncrease = 0.1
            else:
                scoreIncrease = 0.05

            if square != "--":
                if square[0] == "w":
                    if square[1] == ("N" or "B"):
                        scoreIncrease += 0.1


                if square[0] == "b":
                    if square[1] == ("N" or "B"):
                        scoreIncrease += 0.1


    if not (gs.currentCastlingRight.wks and gs.currentCastlingRight.wqs):
        score -= 0.3
    if not (gs.currentCastlingRight.bks and gs.currentCastlingRight.bqs):
        score += 0.3

    if gs.is_castled:
        if gs.whiteToMove:
            score += 0.5
        else:
            score -= 0.5

    if gs.whiteToMove:
        score += (scoreIncrease + activityScore)
    else:
        score -= (scoreIncrease + activityScore)

    return score

def checkOpeningBook(gs, moveList, validMoves):
    global inBook
    openingBook = open("Opening_book.txt", "r")
    moveString = ""
    if len(moveList) != 0:

        if len(moveList) % 2 != 0:
            moveList = moveList + [""]

        moveSubList = [moveList[n:n+2] for n in range(0, len(moveList), 2)]
        for i in range(len(moveSubList)):
            moveString += str(i+1) + "." + moveSubList[i][0] + " " + moveSubList[i][1]
            if moveSubList[i][1] != "":
                moveString += " "
    openingBookLines = openingBook.readlines()


    move_lines = [line for line in openingBookLines if moveString in line]
    if len(move_lines) == 0:
        inBook = False
        return None
    for move in move_lines:
        move_lines[move_lines.index(move)] = move.removesuffix("\n")
    picked_line = move_lines[random.randint(0, len(move_lines)) - 1]
    if moveString == "":
        movesLeftInLine = picked_line
    else:
        movesLeftInLine = picked_line.split(moveString)[1]
    moves = movesLeftInLine.split(" ")
    for move in moves:
        moves[moves.index(move)] = move.replace(".", "")
    for move in moves:
        if move[0] in ("1", "2", "3", "4", "5", "6", "7", "8"):
            moves[moves.index(move)] = move[:0] + move[1:]
    newMove = moves[0]

    for move in validMoves:
        gs.make_move(move)
        x = move.get_chess_notation(gs)
        gs.undo_move()
        if x == newMove:
            return move


    openingBook.close()

    inBook = False
    return None

def orderedMoves(gs, board, validMoves):
    def orderer(move):
        return scoreMaterial(board, gs, validMoves)

    in_order = sorted(validMoves, key=orderer, reverse=gs.whiteToMove)
    return list(in_order)
