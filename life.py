from collections import namedtuple

Rules = namedtuple('Rules', 'b s')


class Pattern(namedtuple('Pattern', 'width height rules commands')):

    Command = namedtuple('Command', 'length state')

    def __new__(cls, *args):
        return super().__new__(cls, *args)

    @property
    def center_x(self):
        return int((self.width - 1) / 2)

    @property
    def center_y(self):
        return int((self.height - 1) / 2)

    def interpret(self, interpreter_func,
                  xflipped=False, yflipped=False,
                  rotation=0):

        xstart = 0
        ystart = 0
        if not xflipped:
            xflip = 1
        else:
            xflip = -1
            xstart = self.width
        if not yflipped:
            yflip = 1
        else:
            yflip = -1
            ystart = self.height

        if rotation == 0:
            def f(state, x, y):
                interpreter_func(state,
                                 xstart + x,
                                 ystart + y)

        elif rotation == 1:
            def f(state, x, y):
                interpreter_func(state,
                                 xstart - y,
                                 ystart + x)

        elif rotation == 2:
            def f(state, x, y):
                interpreter_func(state,
                                 ystart - self.width - x,
                                 xstart - self.height - y)

        elif rotation == 3:
            def f(state, x, y):
                interpreter_func(state,
                                 ystart - (self.height) - y,
                                 xstart + x)

        x = 0
        y = 0
        for command in self.commands:
            if command.state == '$':
                x = 0
                y += yflip * command.length
            else:
                for _ in range(command.length):
                    f(command.state, x, y)
                    x += xflip

    @staticmethod
    def parsefile(filename):
        with open(filename, 'r') as f:
            pattern_name = None

            # look for name comment and get header
            header = f.readline().strip()
            while header.startswith('#'):
                if header.startswith('#N'):
                    pattern_name = header[2:].strip()
                header = f.readline().strip()
            header = header.replace(' ', '')

            if pattern_name is None:
                pattern_name = f.name[:f.name.rfind('.')]
                pattern_name = pattern_name.rsplit('\\', 1)[-1]
                pattern_name = pattern_name.rsplit('/', 1)[-1]
            headerparts = header.split(',')

            pattern_width = int(headerparts[0][2:])
            pattern_height = int(headerparts[1][2:])

            if headerparts[2] is None:
                pattern_rules = Rules([3], [2, 3])
            else:
                rules = headerparts[2].replace('rule=', '').split('/')
                if rules[0][0].casefold() == 'b':
                    birth_string = rules[0][1:]
                    survival_string = rules[1][1:]
                elif rules[0][0].casefold() == 's':
                    birth_string = rules[1][1:]
                    survival_string = rules[0][1:]
                else:
                    birth_string = rules[1]
                    survival_string = rules[0]

                birth_rule = []
                for character in birth_string:
                    birth_rule.append(int(character))

                survival_rule = []
                for character in survival_string:
                    survival_rule.append(int(character))

                pattern_rules = Rules(tuple(birth_rule), tuple(survival_rule))

            def parse_commands(line):
                parsed_commands = []
                length = ''

                for character in line:
                    if character.isdigit():
                        length += character
                    else:
                        if length == '':
                            command = Pattern.Command(1, character)
                        else:
                            command = Pattern.Command(int(length), character)

                        parsed_commands.append(command)
                        length = ''

                return parsed_commands

            # length is amount of, $ is new line, b or B=dead cell,
            # any other character is alive cell
            pattern_commands = []
            unparsed_line = f.readline().strip().replace(' ', '')

            while unparsed_line[-1] != '!':
                line_to_process = unparsed_line
                unparsed_line = ''
                while (line_to_process[-1].isdigit()):
                    unparsed_line = line_to_process[-1] + unparsed_line

                pattern_commands.extend(parse_commands(line_to_process))

                unparsed_line += f.readline().strip().replace(' ', '')

            pattern_commands.extend(parse_commands(unparsed_line[:-1]))

        return (pattern_name, Pattern(pattern_width, pattern_height,
                                      pattern_rules, pattern_commands))


class Selection(Pattern):
    def __new__(cls, pattern):
        new_selection = super().__new__(cls, *pattern)
        new_selection.xflipped = False
        new_selection.yflipped = False
        new_selection.rotation = 0
        return new_selection

    def horizontal_flip(self):
        if self.rotation % 2 == 0:
            self.xflipped ^= True
        else:
            self.yflipped ^= True

    def vertical_flip(self):
        if self.rotation % 2 == 0:
            self.yflipped ^= True
        else:
            self.xflipped ^= True

    def rotate_pattern(self):
        self.rotation = (self.rotation + 1) % 4

    def interpret(self, interpreter_func):
        super().interpret(interpreter_func,
                          self.xflipped, self.yflipped,
                          self.rotation)

MOORE_NEIGHBOURHOOD = (
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1))


class CellGrid(list):
    def __init__(self, cellsize, widthfunc, heightfunc):
        self._cellsize = cellsize

        # width and height are relative to cellsize, get functions to be able
        # to evaluate width and height
        self._widthfunc = widthfunc
        self._heightfunc = heightfunc

        self._calc_dimensions()

        super().__init__(self._new_grid())

    def cell_next_generation(self, x, y, rules):
        alive_neighbour_count = 0

        for n in MOORE_NEIGHBOURHOOD:
            alive_neighbour_count += (self
                                      [self.wrap_x(x + n[0])]
                                      [self.wrap_y(y + n[1])])

        # if cell is alive
        if self[x][y]:
            ruleset = rules.s
        else:
            ruleset = rules.b

        for rule in ruleset:
            if alive_neighbour_count == rule:
                return True
        return False

    def next_generation(self, rules):
        self.setgrid(
            [[self.cell_next_generation(x, y, rules)
              for y in range(self.height)]
             for x in range(self.width)]
            )

    def grid(self, scalar):
        """ Convert canvas to grid scalar """
        return int(scalar / self.cellsize)

    def canvas(self, scalar):
        """ Convert grid to canvas scalar """
        return scalar * self.cellsize

    def wrap_x(self, scalar):
        return scalar % self.width

    def wrap_y(self, scalar):
        return scalar % self.height

    def setgrid(self, newgrid):
        self.clear()
        self.extend(newgrid)

    def reset(self):
        self.setgrid(self._new_grid())

    def copy_grid(self):
        return [col[:] for col in self]

    @property
    def cellsize(self):
        return self._cellsize

    @cellsize.setter
    def cellsize(self, new_cellsize):
        self._cellsize = new_cellsize
        self._calc_dimensions()
        self.reset()

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def canvaswidth(self):
        return self.width * self.cellsize

    @property
    def canvasheight(self):
        return self.height * self.cellsize

    def _calc_dimensions(self):
        self._width = self._widthfunc(self.cellsize)
        self._height = self._heightfunc(self.cellsize)

    def _new_grid(self):
        return [[False for _ in range(self.height)]
                for _ in range(self.width)]
