#!/usr/bin/python

UNKNOWN = 0
HIT = 1
MISS = 2
SUNK = 3


def str2tuple(string_point):
    return tuple(map(int, string_point))


def tuple2str(tuple_point):
    return "".join(map(str, tuple_point))


class Probability(object):

    def __init__(self, state):
        self.log = open('prob.log', 'a')
        self.free = []
        self.state = {}
        self.fits = {}
        self.probs = {}
        self.remaining_ships = [5, 4, 3, 2]
        for ship in state['destroyed']:
            self.remaining_ships.remove(int(ship))
        for x in range(8):
            for y in range(8):
                point = (x, y)
                self.free.append(point)
                self.probs[point] = 0
                self.state[point] = UNKNOWN
                self.fits[point] = 0
        me = str(state['you'])
        sinkings = 0
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
                sinkings += 1
                self.sunk(point, int(state['destroyed'].pop(0)))
        if sinkings:
            self.log.write(str(state) + '\n')
        self.calculateFits()
        self.calculateAdjacents()

    def getMaxMove(self):
        items = self.fits.items()
        if len(items) == 0:
            return None
        max_value = max(items, key=lambda x: x[1])
        move = filter(lambda x: x[1] == max_value[1], items)[0][0]
        self.log.close()
        return tuple2str(move)

    def printState(self):
        for y in range(8):
            for x in range(8):
                if self.state[(x, y)] == HIT:
                    print ' #  ',
                elif self.state[(x, y)] == MISS:
                    print ' *  ',
                elif self.state[(x, y)] == SUNK:
                    print '### ',
                else:
                    print '%3d ' % self.fits[(x, y)],
            print ''

    def doesShipFit(self, length, point, direction):
        fits = True
        if direction == 'horizontal':
            y = point[1]
            for x in range(point[0], point[0] + length):
                state = self.state[(x, y)]
                if state == MISS or state == SUNK:
                    fits = False
                    break
        else:
            x = point[0]
            for y in range(point[1], point[1] + length):
                state = self.state[(x, y)]
                if state == MISS or state == SUNK:
                    fits = False
                    break
        return fits

    def calculateFits(self):
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
        def check(point, direction):
            new_point = (point[0] + direction[0], point[1] + direction[1])
            if new_point in self.state:
                state = self.state[new_point]
                if state == MISS or state == SUNK:
                    return 0
                elif state == HIT:
                    return 30 + check(new_point, direction)
            return 0

        def mark(point, state):
            if state == HIT:
                if point in self.fits:
                    self.fits[point] += 30

        directions = ((0, 1), (0, -1), (1, 0), (-1, 0))
        for x in range(0, 8):
            for y in range(0, 8):
                point = (x, y)
                if point in self.fits:
                    for direction in directions:
                        self.fits[point] += check(point, direction)

    def hit(self, point):
        self.state[point] = HIT
        del self.fits[point]

    def miss(self, point):
        self.state[point] = MISS
        del self.fits[point]

    def sunk(self, point, length):
        x, y = point
        possible_size = 1
        while x - possible_size >= 0 and self.state[(x - possible_size, y)] == HIT:
            possible_size += 1
        if possible_size >= length:
            for x in range(x - length + 1, x + 1):
                self.state[(x, y)] = SUNK
            return
        possible_size = 1
        while x + possible_size <= 7 and self.state[(x + possible_size, y)] == HIT:
            possible_size += 1
        if possible_size >= length:
            for x in range(x, x + length):
                self.state[(x, y)] = SUNK
            return
        possible_size = 1
        while y - possible_size >= 0 and self.state[(x, y - possible_size)] == HIT:
            possible_size += 1
        if possible_size >= length:
            for y in range(y - length + 1, y + 1):
                self.state[(x, y)] = SUNK
            return
        possible_size = 1
        while y + possible_size <= 7 and self.state[(x, y + possible_size)] == HIT:
            possible_size += 1
        if possible_size >= length:
            for y in range(y, y + length):
                self.state[(x, y)] = SUNK
            return


if __name__ == '__main__':
    state = {
        'moves': ['0613', '0621', '0513', '0413', '0314'],
        'you': 0,
        'destroyed': ['3']
    }
    while(True):
        p = Probability(state)
        p.printState()
        break
