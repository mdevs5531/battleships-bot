'''
Bot for www.brainjar.org/battleships/ competition.

Originally authored by github.com/mdevs5531
'''
import json
import random
import sys


def str2tuple(string_point):
    return tuple(map(int, string_point))


def tuple2str(tuple_point):
    return "".join(map(str, tuple_point))


class LikelyhoodBot(object):
    '''
    Not perfect by any means, but figure if I can't beat it more than 50%
    of the time it's not bad.
    '''

    # Potential states for each square on the board
    UNKNOWN = 0
    HIT = 1
    MISS = 2
    SUNK = 3
    USELESS = 4

    def __init__(self, state):
        # Seed your random number generator!
        random.seed()
        # State of each square on the board
        self.state = {}
        # Holds a non-bounded number for each square, higher numbers
        # mean it's a more appealing target
        self.fits = {}
        # Which ships still need to be sunk?
        self.remaining_ships = [5, 4, 3, 2]
        for ship in state['destroyed']:
            self.remaining_ships.remove(int(ship))
        # Initialize state and fits
        for x in range(8):
            for y in range(8):
                point = (x, y)
                self.state[point] = self.UNKNOWN
                self.fits[point] = 0
        # me = you
        me = str(state['you'])
        # Run through all moves and update the state of the board
        for move in state['moves']:
            if move[0:1] != me:
                continue
            point = str2tuple(move[1:3])
            result = move[3:4]
            if result == '1':
                self.miss(point)
            elif result == '3':
                self.hit(point)
            elif result == '4':
                self.sunk(point, int(state['destroyed'].pop(0)))
        self.calculateFits()
        self.calculateAdjacents()

    def getMaxMove(self):
        '''
        Returns the square (in 'xy' format) that has the highest fit value
        '''
        items = self.fits.items()
        if len(items) == 0:
            return None
        max_value = max(items, key=lambda x: x[1])
        move = filter(lambda x: x[1] == max_value[1], items)[0][0]
        return tuple2str(move)

    def printState(self):
        '''
        Easy to look at visulaization of what the bot's belief in the
        board state is
        '''
        for y in range(8):
            for x in range(8):
                if self.state[(x, y)] == self.HIT:
                    print ' #  ',
                elif self.state[(x, y)] == self.MISS:
                    print ' *  ',
                elif self.state[(x, y)] == self.SUNK:
                    print '### ',
                else:
                    print '%3d ' % self.fits[(x, y)],
            print ''

    def doesShipFit(self, length, point, direction):
        '''
        Checks if it's possible for an unsunk ship of _length_ to be
        on the board, starting at _point_ (as a minimum coordinate) and
        extending in _direction_

        Code is kinda ugly
        '''
        fits = True
        if direction == 'horizontal':
            y = point[1]
            for x in range(point[0], point[0] + length):
                state = self.state[(x, y)]
                if state == self.MISS or state == self.SUNK:
                    fits = False
                    break
        else:
            x = point[0]
            for y in range(point[1], point[1] + length):
                state = self.state[(x, y)]
                if state == self.MISS or state == self.SUNK:
                    fits = False
                    break
        return fits

    def calculateFits(self):
        '''
        Check all possible positions for all possible remaining ships to see
        if they are valid.  Increments fits by 1 for each possible ship +
        position + direction combo that could be there.

        Caveat: Assumes independence of ship positions, which is untrue.
        However in practice this is a close enough approximation, and means
        we only have to test 352 positions rather than some awful combinatorial
        problem.

        Caveat 2: Assumes ships are more likely to be located in the center
        of the board because there are more possible positions for them there.
        This holds some validity against random ship placement of the kind this
        bot uses, but is pretty shaky math and I haven't really thought it
        through.
        '''
        for length in self.remaining_ships:
            # Verical checks
            for x in range(0, 8):
                for y in range(0, 9 - length):
                    point = (x, y)
                    fit = int(self.doesShipFit(length, point, 'vertical'))
                    for y_fit in range(y, y + length):
                        fit_point = (x, y_fit)
                        if fit_point in self.fits:
                            self.fits[fit_point] += fit
            # Horizontal checks
            for y in range(0, 8):
                for x in range(0, 9 - length):
                    point = (x, y)
                    fit = int(self.doesShipFit(length, point, 'horizontal'))
                    for x_fit in range(x, x + length):
                        fit_point = (x_fit, y)
                        if fit_point in self.fits:
                            self.fits[fit_point] += fit

    def calculateAdjacents(self):
        '''
        Look through each possible remaining shot, and add some value
        depending on if there are adjacent HITs on non-SUNK ships.

        The + 30 for each consecutive adjacent HIT is arbitrary, but
        higher than the maximum fits score possible in the initial board.
        '''
        def check(point, direction):
            new_point = (point[0] + direction[0], point[1] + direction[1])
            if new_point in self.state:
                state = self.state[new_point]
                if state == self.MISS or state == self.SUNK:
                    return 0
                elif state == self.HIT:
                    return 30 + check(new_point, direction)
            return 0

        directions = ((0, 1), (0, -1), (1, 0), (-1, 0))
        for x in range(0, 8):
            for y in range(0, 8):
                point = (x, y)
                if point in self.fits:
                    for direction in directions:
                        self.fits[point] += check(point, direction)

    def hit(self, point):
        '''
        Mark square as hit
        '''
        self.state[point] = self.HIT
        del self.fits[point]

    def miss(self, point):
        '''
        Mark square as missed
        '''
        self.state[point] = self.MISS
        del self.fits[point]

    def sunk(self, point, length):
        '''
        Mark square as sunk, and try to figure out which adjacent squares
        represent the rest of the sunk ship.  This should work in the nice
        clean world we play in right now, where people seed ships that are
        strictly non-adjacent.  However, if ships can be placed adjacent to
        each other it's easily possible for this to mark the wrong squares.
        '''
        x, y = point
        possible_size = 1
        while x - possible_size >= 0 and self.state[(x - possible_size, y)] == self.HIT:
            possible_size += 1
        if possible_size >= length:
            for x in range(x - length + 1, x + 1):
                self.state[(x, y)] = self.SUNK
            return
        possible_size = 1
        while x + possible_size <= 7 and self.state[(x + possible_size, y)] == self.HIT:
            possible_size += 1
        if possible_size >= length:
            for x in range(x, x + length):
                self.state[(x, y)] = self.SUNK
            return
        possible_size = 1
        while y - possible_size >= 0 and self.state[(x, y - possible_size)] == self.HIT:
            possible_size += 1
        if possible_size >= length:
            for y in range(y - length + 1, y + 1):
                self.state[(x, y)] = self.SUNK
            return
        possible_size = 1
        while y + possible_size <= 7 and self.state[(x, y + possible_size)] == self.HIT:
            possible_size += 1
        if possible_size >= length:
            for y in range(y, y + length):
                self.state[(x, y)] = self.SUNK
            return


class Placement(object):
    '''
    Pretty dumb code but it works.  Not really worth commenting.
    '''

    def __init__(self):
        self.state = [[0 for y in range(8)] for x in range(8)]
        random.seed()
        self.placement = {}

    def place_ships(self):
        for length in range(5, 1, -1):
            self.place_ship(length)
        print json.dumps(self.placement)

    def valid_placement(self, point, length, direction):
        try:
            if direction == 'horizontal':
                x = point[0]
                for y in range(point[1], point[1] + length):
                    if y == point[1] and y > 0:
                        if self.state[x][y - 1] != 0:
                            return False
                    if y == point[1] + length - 1 and y < 7:
                        if self.state[x][y + 1] != 0:
                            return False
                    if self.state[x][y] != 0:
                        return False
                    if x > 0 and self.state[x - 1][y] != 0:
                        return False
                    if x < 7 and self.state[x + 1][y] != 0:
                        return False
                return True
            elif direction == 'vertical':
                y = point[1]
                for x in range(point[0], point[0] + length):
                    if x == point[0] and x > 0:
                        if self.state[x - 1][y] != 0:
                            return False
                    if x == point[0] + length - 1 and x < 7:
                        if self.state[x + 1][y] != 0:
                            return False
                    if self.state[x][y] != 0:
                        return False
                    if y > 0 and self.state[x][y - 1] != 0:
                        return False
                    if y < 7 and self.state[x][y + 1] != 0:
                        return False
                return True
        except:
            pass
        return False

    def get_random_placement(self, length):
        direction = ['vertical', 'horizontal'][random.randint(0, 1)]
        point = [random.randint(0, 7), random.randint(0, 8 - length)]
        if direction == 'horizontal':
            point.reverse()
        return (direction, point)

    def place_ship(self, length):
        direction, point = self.get_random_placement(length)
        while not self.valid_placement(point, length, direction):
            direction, point = self.get_random_placement(length)
        if direction == 'horizontal':
            x = point[0]
            for y in range(point[1], point[1] + length):
                self.state[x][y] = 1
        else:
            y = point[1]
            for x in range(point[0], point[0] + length):
                self.state[x][y] = 1
        self.placement[str(length)] = {'point': "".join(map(str, reversed(point))),
                                       'orientation': direction}


if __name__ == "__main__":
    # Get input command
    state = json.loads(sys.argv[1])
    if state['cmd'] == 'init':
        place = Placement()
        place.place_ships()
    else:
        bot = LikelyhoodBot(state)
        move = {'move': bot.getMaxMove()}
        print json.dumps(move)
