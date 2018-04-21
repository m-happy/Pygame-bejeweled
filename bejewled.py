import random, time, pygame, sys, copy
from pygame.locals import *

FPS = 30
WINDOWWIDTH = 600
WINDOWHEIGHT = 600
BOARDWIDTH = 8
BOARDHEIGHT = 8
GEMIMAGESIZE = 64
NUMGEMIMAGES = 7
assert NUMGEMIMAGES >=5
NUMMATCHSOUNDS = 6
MOVERATE = 25
DEDUCTSPEED = 0.8
PURPLE   = (255, 0, 255)
LIGHTBLUE = ( 170, 190, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
BLACK = ( 0, 0, 0)
BROWN = (85, 65, 0)
HIGHLIGHTCOLOR = PURPLE
BGCOLOR = LIGHTBLUE
GRIDCOLOR = BLUE
GAMEOVERCOLOR = RED
GAMEOVERBGCOLOR = BLACK
SCORECOLOR = BROWN

XMARGIN = int((WINDOWWIDTH - GEMIMAGESIZE * BOARDWIDTH) /2)
YMARGIN = int((WINDOWHEIGHT - GEMIMAGESIZE * BOARDHEIGHT) / 2)
# constants for direction values
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'
EMPTY_SPACE = -1
ROWABOVEBOARD = 'row above board'
def main():
    global FPSCLOCK, DISPLAYSURF, GEMIMAGES, GAMESOUNDS, BASICFONT, BOARDRECTS
    #Initial set up.
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption('Gemgen')
    BASICFONT = pygame.font.Font('freesansbold.ttf', 36)
    #load images
    GEMIMAGES = []
    for i in range(1, NUMGEMIMAGES + 1):
        gemImage  = pygame.image.load('gem%s.png' %i)
        if gemImage.get_size() != (GEMIMAGESIZE, GEMIMAGESIZE):
            gemImage = pygame.transform.smoothscale(gemImage,(GEMIMAGESIZE, GEMIMAGESIZE))
            GEMIMAGES.append(gemImage)
            #load the sounds
    GAMESOUNDS = {}
    GAMESOUNDS['bad swap'] = pygame.mixer.Sound('badswap.wav')
    GAMESOUNDS['match'] = []
    for i in range(NUMMATCHSOUNDS):
        GAMESOUNDS['match'].append(pygame.mixer.Sound('match%s.wav' %i))
    BOARDRECTS = []
    for x in range(BOARDWIDTH):
        BOARDRECTS.append([])
        for y in range(BOARDWIDTH):
            r = pygame.Rect((XMARGIN + (x * GEMIMAGESIZE),
                             YMARGIN + (y * GEMIMAGESIZE),
                             GEMIMAGESIZE,
                             GEMIMAGESIZE))
            BOARDRECTS[x].append(r)
    while True:
        runGame()

def runGame():
    gameBoard = getBlankBoard()
    score = 0
    fillBoardAndAnimate(gameBoard, [], score)
    firstSelectedGem = None
    lastMouseDownX  = None
    lastMouseDownY = None
    gameIsOver = False
    lastScoreDeduction = time.time()
    clickContinueTextSurf = None

    while True:
        clickedSpace = None
        for event in pygame.event.get():
            if event.type == QUIT or (event.type ==KEYUP and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == KEYUP and event.key == K_BACKSPACE:
                return
            elif event.type == MOUSEBUTTONUP:
                if gameIsOver:
                    return
                if event.pos == ( lastMouseDownX, lastMouseDownY):
                    clickedSpace = checkForGemClick(event.post)
                else:
                    firstSelectedGem = checkForGemClick((lastMouseDownX, lastMouseDownY))
                    clickedSpace = checkForGemClick(event.post)
                    if not firstSelectedGem or not clickedSpace:
                        firstSelectedGem = None
                        clickedSpace = None
                    elif event.type == MOUSEBUTTONDOWN:
                        lastMouseDownX, lastMouseDownY = event.pos
                if clickedSpace and not fistSelectedGem:
                    firstSelectedGem = clickedSpace
                elif clickedSpace and firstSelectedGem:
                    firstSwappingGem, secondSwappingGem = getSwappingGems(gameBoard, firstSelectedGem, clickedSpace)
                    if firstSwappingGem == None and secondSwappingGem == None:
                        firstSelectedGem = None
                        continue
                    boardCopy = getBoardCopyMinusGems(gameBoard, firstSwappingGem, secondSwappingGem)
                    animateMovingGems(boardcopy, [firstSwappingGem, secondSwappingGem], [], score)
                    gameBoard[firstSwappingGem['x']][firstSwappingGem['y']] = firstSwappingGem['imageNum']
                    matchedGems = findMatchingGems(gameBoard)
                    if matchedGems == []:
                        GAMESOUNDS['bad swap'].play()
                        animateMovingGems(boardCopy, [firstSwappingGem, secondSwappingGem], [], score)
                        gameBoard[firstSwappingGem['x']][firstSwappingGem['y']] = firstSwappingGem['imageNum']
                        gameBoard[secondSwappingGem['x']][secondSwappingGem['y']] = secondSwappingGem['imageNum']
                    else:
                        scoreAdd = 0
                        while matchedGems !=[]:
                            points = []
                            for gemSet in matchedGems:
                                scoreAdd += ( 10 + (len(gemSet) - 3 ) * 10 )
                                for gem in gemSet:
                                    gameBoard[gem[0]][gem[1]] = EMPTY_SPACE
                                points.append({'points':scoreAdd,
                                               'x': gem[0] * GEMIMAGESIZE + XMARGIN,
                                               'y': gem[1] * GEMIMAGESIZE + YMARGIN})
                                random.choice(GAMESOUNDS['match']).play()
                                score += scoreAdd
                                fillBoardAndAnimate(gameBoard, points, score)
                                matchedGems = findMatchingGems(gameBoard)
                            firstSelectedGems = None
                            if not canMakeMove(gameBoard):
                                gameIsOver = True
            DISPLAYSURF.fill(BGCOLOR)
            drawBoard(gameBoard)
            if firstSelectedGem != None:
                highlightSpace(firstSelectedGem['x'], firstSelectedGem['y'])
            if gameIsOver:
                if clickContinueTextSurf == None:
                    clickContinueTextSurf = BASICFONT.render('Final Score: %s(click to continue)' %(score), 1, GAMEOVERCOLOR, GAMEOVERBGCOLOR)
                    clickContinueTextRect = clickContinueTextSurf.get_rect()
                    clickContinueTextRect.center = int(WINDOWWIDTH / 2 ), int(WINDOWHEIGHT / 2)
                DISPLAYSURF.blit(clickContinueTextSurf, clickContinueTextRect)
            elif score > 0 and time.time() - lastScoreDeduction > DEDUCTSPEED:
                score -=1
                lastScoreDeduction = time.time()
            drawScore(score)
            pygame.display.update()
            FPSCLOCK.tick(FPS)

def getSwappingGems(board, firstXY, secondXY):
    firstGem = {'imageNum': board[firstXY['x']][firstXY['y']],
                'x': firstXY['x'],
                'y': firstXY['y']}
    secondGem = {'imageNum': board[secondXY['x']][second['y']],
                 'x': secondXY['x'],
                 'y': secondXY['y']}
    highlightedGem = None
    if firstGem['x']== secondGem['x'] + 1 and firstGem['y'] == secondGem['y']:
        firstGem['direction'] = LEFT
        secondGem['direction'] = RIGHT
    elif firstGem['x'] == secondGem['x'] - 1 and firstGem['y'] == secondGem['y']:
        firstGem['direction'] = RIGHT
        secondGem['direction'] = LEFT
    elif firstGem['y'] == secondGem['y'] + 1 and firstGem['x'] == secondGem['x']:
        firstGem['direction'] = UP
        secondGem['direction'] = DOWN
    else:
        return None, None
    return firstGem, secondGem
def getBlankBoard():
    board = []
    for x in range(BOARDWIDTH):
        board.append([EMPTY_SPACE] * BOARDHEIGHT)
    return board
def canMakeMove(board):
    oneOffPatterns = (((0,1), (1,0), (2,0)),
                     ((0,1), (1,1), (2,0)),
                     ((0,0), (1,1), (2,0)),
                     ((0,1), (1,0), (2,1)),
                     ((0,0), (1,0), (2,1)),
                     ((0,0), (1,1), (2,1)),
                     ((0,0), (0,2), (0,3)),
                     ((0,0), (0,1), (0,3)))
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            for pat in oneOffPatterns:
                if (getGemAt(board, x + pat[0][0], y+pat[0][1]) == \
                    getGemAt(board, x + pat[1][0], y+pat[1][1]) == \
                    getGemAt(board, x + pat[2][0], Y+pat[2][1]) != None) or \
                    (getGemAt(board,x+pat[0][1], y+pat[0][0]) == \
                     getGemAt(board, x+pat[1][1], y+pat[1][0]) == \
                     getGemAt(board, x+pat[2][1], y+pat[2][0])!= None):
                    return True
    return False


def drawMovingGem(gem, progress):
    movex = 0
    movey = 0
    progress *= 0.01

    if gem['direction'] ==UP:
        movey = -int(progress * GEMIMAGESIZE)
    elif gem['direction'] == DOWN:
        movey = int(progress * GEMIMAGESIZE)
    elif gem['direction'] == RIGHT:
        movex = int(progress * GEMIMAGESIZE)
    elif gem['direction'] == LEFT:
        movex = -int(progress * GEMIMAGESIZE)
    basex = gem['x']
    basey = gem['y']
    if basey == ROWABOVEBOARD:
        basey = -1

    pixelx = XMARGIN + (basex * GEMIMAGESIZE)
    pixely = YMARGIN + (basey * GEMIMAGESIZE)
    r = pygame.Rect( (pixelx + movex, pixely + movey, GEMIMAGESIZE,GEMIMAGESIZE))
    DISPLAYSURF.blit(GEMIMAGES[gem['imageNum']], r)

def pullDownAllGems(board):
    for x in range(BOARDWIDTH):
        gemsInColumn = []
        for y in range(BOARDWIDTH):
            if board[x][y] != EMPTY_SPACE:
                gemsInColumn.append(board[x][y])
        board[x] = ([EMPTY_SPACE] * (BOARDHEIGHT - len(gemsInColumn))) + gemsInColumn

def getGemAt(board, x, y):
    if x < 0 or y < 0 or x >= BOARDWIDTH or y >= BOARDHEIGHT:
        return None
    else:
        return board[x][y]


def getDropSlots(board):
    boardCopy = copy.deepcopy(board)
    pullDownAllGems(boardCopy)

    dropSlots = []
    for i in range(BOARDWIDTH):
        dropSlots.append([])

    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT-1, -1, -1):

            if boardCopy[x][y] == EMPTY_SPACE:
                possibleGems = list(range(len(GEMIMAGES)))
                for offsetX, offsetY in ((0,-1), (1,0), (0,1), (-1,0)):
                    neighborGem = getGemAt(boardCopy, x + offsetX, y + offsetY)
                    if neighborGem != None and neighborGem in possibleGems:
                        possilbeGems.remove(neighborGem)
                newGem = random.choice(possibleGems)
                boardCopy[x][y] = newGem
                dropSlots[x].append(newGem)
    return dropSlots

def findMatchingGems(board):
    gemsToRemove = []
    boardCopy = copy.deepcopy(board)
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            if getGemAt(boardCopy, x, y) == getGemAt(boardCopy, x +1, y) == getGemAt(boardCopy, x+2, y) and getGemAt(boardCopy, x, y) != EMPTY_SPACE:
                targetGem = boardCopy[x][y]
                offset = 0
                removeSet = []
                while getGemAt(boardCopy, x + offset, y) == targetGem:
                    removeSet.append((x + offset, y))
                    boardCopy[x + offset][y] = EMPTY_SPACE
                    offset += 1
                gemsToRemove.apppend(removeSet)
            if getGemAt(boardCopy, x, y) == getGemAt(boardCopy, x, y + 1) == getGemAt(boardCopy, x, y + 2) and getGemAt(boardCopy, x, y) != EMPTY_SPACE:
                targetGem = boardCopy[x][y]
                offset = 0
                removeSet = []
                while getGemAt(boardCopy, x, y + offset) == targetGem:
                    removeSet.append((x, y + offset ))
                    boardCopy[x][y + offset] = EMPTY_SPACE
                    offset +=1
                gemsToRemove.append(removeSet)
    return gemsToRemove

def highlightSpace(x, y):
    pygame.draw.rect(DISPLAYSURF, HIGHLIGHTCOLOR, BOARDRECTS[x][y], 4)

def getDroppingGems(board):
    boardCopy = copy.deepcopy(board)
    droppingGems = []
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT - 2, -1, -1):
            if boardCopy[x][y+1] == EMPTY_SPACE and boardCopy[x][y] != EMPTY_SPACE:
                droppingGems.append( {'imageNum': boardCopy[x][y], 'x': x, 'y':y, 'direction':DOWN})
                boardCopy[x][y] = EMPTY_SPACE
    return droppingGems

def animateMovingGems(board, gems, pointsText, score):
    progress = 0
    while progress < 100:
        DISPLAYSURF.fill(BGCOLOR)
        drawBoard(board)
        for gem in gems:
            drawMovingGem(gem, progress)
        drawScore(score)
        for pointText in pointsText:
            pointsSurf = BASICFONT.render(str(pointText['points']), 1, SCORECOLOR)
            pointsRect = pointsSurf.get_rect()
            pointsRect.Center = (pointText['x'], pointText['y'])
            DISPLAYSURF.blit(pointsSurf, pointsRect)
        pygame.display.update()
        FPSCLOCK.tick(FPS)
        progress += MOVERATE

def moveGems(board, movingGems):
    for gem in movingGems:
        if gem['y'] != ROWABOVEBOARD:
            board[gem['x']][gem['y']] = EMPTY_SPACE
            movex = 0
            movey = 0
            if gem['direction'] == LEFT:
                movex = -1
            elif gem['direction'] == RIGHT:
                movex = 1
            elif gem['direction'] == DOWN:
                movey = 1
            elif gem['direction'] == UP:
                movey = -1
            board[gem['x'] + movex][gem['y'] + movey] = gem['imageNum']
        else:
            board[gem['x']][0] = gem['imageNum']

def fillBoardAndAnimate(board, points, score):
    dropSlots = getDropSlots(board)
    while dropSlots != [[]] * BOARDWIDTH:
        movingGems = getDroppingGems(board)
        for x in range(len(dropSlots)):
            if len(dropSlots[x]) != 0:
                movingGems.append({'imageNum': dropSlots[x][0], 'x':x, 'y': ROWABOVEBOARD, 'direction': DOWN})
        boardCopy = getBoardCopyMinusGems(board, movingGems)
        animateMovingGems(boardCopy, movingGems, points, score)
        moveGems(board, movingGems)

        for x in range(len(dropSlots)):
            if len(dropSlots[x]) == 0:
                continue
            board[x][0] = dropSlots[x][0]
            del dropSlots[x][0]


def checkForGemClick(pos):
    for x in range(BOARDWIDTH):
        for y in range(BOARDWIDTH):
            pygame.draw.rect(DISPLAYSURF, GRIDCOLOR, BOARDRECTS[x][y], 1)
            gemToDraw = board[x][y]
            if gemToDraw != EMPTY_SPACE:
                DISPLAYSURF.blit(GEMIMAGES[gemToDraw], BOARDRECTS[x][y])

def getBoardCopyMinusGems(board, gems):
    boardCopy = copy.deepcopy(board)
    for gem in gems:
        if gem['y'] != ROWABOVEBOARD:
            boardCopy[gem['x']][gem['y']] = EMPTY_SPACE

    return boardCopy

def drawScore(score):
    scoreImg = BASICFONT.render(str(score), 1, SCORECOLOR)
    scoreRect = scoreImg.get_rect()
    scoreRect.bottomleft = (10, WINDOWHEIGHT - 6 )
    DISPLAYSURF.blit(scoreImg, scoreRect)

if __name__ == '__main__':
    main()
    
   
                     
                             
                             
                      
    
                                              
                
