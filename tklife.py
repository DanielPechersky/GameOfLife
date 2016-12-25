from tkinter import Canvas

import os
import sys
from tkinter.filedialog import askopenfilenames

from life import CellGrid
import life
import tkinter as tk
import tkinter.ttk as ttk


class CellCanvas(CellGrid, Canvas):
    def __init__(self, settings, widthfunc, heightfunc,
                 master=None, cellsize=None, cnf={}, **kw):

        self._settings = settings
        self.iteration = 0

        if cellsize is None:
            cellsize = int(self._settings['cell']['start_size'])

        CellGrid.__init__(self, cellsize, widthfunc, heightfunc)

        Canvas.__init__(self, master, cnf, **kw)
        self.config(
            width=self.canvaswidth,
            height=self.canvasheight,
            highlightthickness=0, closeenough=0)

        try:
            if self._settings['cell']['draw_func'] is not None:
                self.draw_func = __import__(self._settings
                                            ['cell']['draw_func']).func
        except (ValueError, ImportError):
            self.draw_func = None

    def draw_cell(self, x, y, color=None, tag='cell'):
        x_canvas = self.canvas(x)
        y_canvas = self.canvas(y)

        def def_draw():
            self.create_rectangle(
                x_canvas, y_canvas,
                x_canvas + self.cellsize,
                y_canvas + self.cellsize,
                fill=color,
                width=0, tag=tag)

        if color is None:
            color = self._settings['cell']['color']
            if self.draw_func is not None:
                self.draw_func(locals())
            else:
                def_draw()
        else:
            def_draw()

    def draw_all_cells(self, prev_generation, color=None):
        def analyze_cell(x, y):
            if self[x][y] ^ prev_generation[x][y]:
                if self[x][y]:
                    self.draw_cell(x, y, color)
                else:
                    self.undraw_cell(x, y)

        for x in range(self.width):
            for y in range(self.height):
                analyze_cell(x, y)

    def undraw_cell(self, x, y):
        """
        Deletes all canvas objects at cell coordinates x and y,
        presumably one cell
        """

        # add 1 to canvas coords to avoid grid lines
        x_loc = self.canvas(x) + 1
        y_loc = self.canvas(y) + 1

        for item in self.find_overlapping(x_loc, y_loc,
                                          x_loc, y_loc):
            self.delete(item)

    def undraw_all_cells(self):
        """ Deletes all canvas objects with a tag of 'cell' """
        self.delete('cell')

    def draw_grid(self, color=None):

        if color is None:
            color = self._settings['grid']['color']

        self.delete('grid_line')

        for half_line in [self.cellsize - 1, self.cellsize]:
            for x in range(half_line, self.canvaswidth,
                           self.cellsize):

                self.create_line(
                    x, 0, x, self.canvasheight,
                    fill=color, tag='grid_line')

            for y in range(half_line, self.canvasheight,
                           self.cellsize):

                self.create_line(
                    0, y, self.canvaswidth, y,
                    fill=color, tag='grid_line')

    def new_gen(self, rules, color=None):
        prev_generation = self.copy_grid()
        self.next_generation(rules)
        self.draw_all_cells(prev_generation, color)
        self.iteration += 1

    def reset(self):
        CellGrid.reset(self)
        self.undraw_all_cells()
        self.draw_grid()
        self.iteration = 0

    @property
    def cellsize(self):
        return self._cellsize

    @cellsize.setter
    def cellsize(self, new_cellsize):
        self._cellsize = new_cellsize
        self._calc_dimensions()
        self.reset()


class LifeApp(tk.Tk):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.parent = parent

        self._settings = settings

        self.title("Game Of Life")
        self.resizable(width=False, height=False)

        def parse_rules(rules):
            return [int(rule) for rule in rules.split(',')]

        self.rules = life.Rules(parse_rules(self._settings['rules']['birth']),
                                parse_rules(self._settings['rules']['survival']))

        self.patterns = {}
        self.patternselection = None

        self.bind('d', lambda event: self.patternselection.horizontal_flip())
        self.bind('f', lambda event: self.patternselection.vertical_flip())
        self.bind('r', lambda event: self.patternselection.rotate_pattern())

        main_frame = ttk.Frame(self)
        main_frame.pack()

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        bot_frame = ttk.Frame(main_frame)
        bot_frame.pack(side=tk.BOTTOM, fill=tk.X)
        # Top Frame

        def widthfunc(cellsize):
            return int(self.winfo_screenwidth() * 0.9 / cellsize)

        def heightfunc(cellsize):
            return int(self.winfo_screenheight() * 0.8 / cellsize)

        self.cells = CellCanvas(self._settings,
                                widthfunc, heightfunc,
                                master=main_frame,
                                background=self._settings['background']
                                                         ['color'])

        self.cells.bind('<Button-1>', self.canvas_press)
        self.cells.bind('<Enter>', self.mouse_entered_canvas)
        self.cells.bind('<Leave>', self.mouse_left_canvas)
        self.cells.bind('<Motion>', self.mouse_moved_in_canvas)
        self.cells.bind('<Button-2>',
                        lambda event: self.patternselection.rotate_pattern())
        self.cells.pack()

        self.pattern_info = tk.StringVar()
        pattern_info_label = ttk.Label(
            top_frame, textvariable=self.pattern_info, anchor=tk.W)
        pattern_info_label.pack(side=tk.RIGHT, padx=10)

        for i in range(2):
            label_text = ('B:', 'S:')[i]
            ruleset = (self._birth_rules, self._survival_rules)[i]
            ttk.Label(top_frame, text=label_text).pack(side=tk.LEFT, padx=10)
            for o in range(9):
                ttk.Label(top_frame, text=str(o)).pack(side=tk.LEFT)
                ttk.Checkbutton(
                    top_frame, variable=ruleset[o]).pack(side=tk.LEFT)

        # Bot Frame
        run_button = ttk.Button(bot_frame, text="Start")
        run_button.pack(side=tk.LEFT, padx=10)

        ttk.Label(bot_frame, text="Speed").pack(side=tk.LEFT, padx=15)

        def update_slider_moved(new_updaterate):
            self.cell_updater.set_update_rate(
                round(int(new_updaterate[:new_updaterate.find('.')]), -2))

        update_rate_slider = ttk.Scale(
            bot_frame, from_=100, to=500, orient=tk.HORIZONTAL)
        update_rate_slider['command'] = update_slider_moved
        update_rate_slider.pack(side=tk.LEFT, padx=15)

        reset_button = ttk.Button(bot_frame, text="Reset")
        reset_button['command'] = self.reset
        reset_button.pack(side=tk.LEFT, padx=15)

        ttk.Label(bot_frame, text='Cell Size').pack(side=tk.LEFT, padx=15)

        self.entry_str = tk.StringVar()
        self.cell_size = int(self._settings['cell']['start_size'])
        cell_size_entry = ttk.Entry(bot_frame, textvariable=self.entry_str)
        cell_size_entry.pack(side=tk.LEFT, padx=15)

        def open_files():
            self.add_pattern_files(
                askopenfilenames(initialdir='.', title='Choose patterns'))

        open_file_button = ttk.Button(bot_frame, text="Open File")
        open_file_button['command'] = open_files

        open_file_button.pack(side=tk.RIGHT, padx=10)

        self.pattern_selection_box = ttk.Combobox(bot_frame, state='readonly')
        self.pattern_selection_box.bind(
            '<<ComboboxSelected>>', self.pattern_selected)
        self.pattern_selection_box.pack(side=tk.RIGHT, padx=15)

        self.place_pattern_button = ttk.Button(
            bot_frame, text="Place Patterns", width=len("Place Patterns"))
        self.place_pattern_button['command'] = self.toggle_pattern_placing
        self.place_pattern_button.pack(side=tk.RIGHT, padx=15)

        dirs = self._settings['pattern_directories']['startup'].split(',')
        for dir_ in dirs:
            for file in os.listdir(os.path.join(sys.path[0], dir_)):
                if file.endswith('.rle'):
                    self.add_pattern_file(
                        os.path.join(sys.path[0], dir_, file))
        del dirs

        def new_gen():
            self.cells.new_gen(self.rules)

        self.cell_updater = Updater(
            100, new_gen, self,
            lambda b=run_button: b.config(text='Stop'),
            lambda b=run_button: b.config(text='Start'))

        run_button['command'] = self.cell_updater.toggle_run
        update_rate_slider.set(self.cell_updater.rate)

        self.selection_updater = Updater(20, self.draw_selection, self)
        self.selection_updater.x = 0
        self.selection_updater.y = 0

        self.cells.draw_grid()

        self.mainloop()

    @property
    def rules(self):
        rules = []
        for r in [self._birth_rules, self._survival_rules]:
            rule_set = []
            for i in range(9):
                if r[i].get():
                    rule_set.append(i)
            rules.append(rule_set)

        return life.Rules(tuple(rules[0]), tuple(rules[1]))

    @rules.setter
    def rules(self, new_rules):
        def empty_ruleset(): return [tk.BooleanVar() for _ in range(9)]

        if not hasattr(self, '_birth_rules'):
            self._birth_rules = empty_ruleset()
        if not hasattr(self, '_survival_rules'):
            self._survival_rules = empty_ruleset()

        rulesets = (self._birth_rules, self._survival_rules)
        new_rulesets = (new_rules.b, new_rules.s)

        for i in range(2):
            for rule in rulesets[i]:
                rule.set(False)

            for rule in new_rulesets[i]:
                rulesets[i][rule].set(True)

    def add_pattern_files(self, files):
        for file in files:
            self.add_pattern_file(file)

    def add_pattern_file(self, file):
        try:
            new_pattern = life.Pattern.parsefile(file)
        except IOError as e:
            print(e)
        else:
            self.patterns[new_pattern[0]] = new_pattern[1]
            self.pattern_selection_box['values'] = sorted(self.patterns.keys())

    def mouse_loc_from_event(self, event):
        self.selection_updater.x = self.cells.grid(event.x - 1)
        self.selection_updater.y = self.cells.grid(event.y - 1)

    def mouse_entered_canvas(self, event):
        self.mouse_loc_from_event(event)
        self.selection_updater.start_run()

    def mouse_left_canvas(self, event):
        self.disable_pattern_placing()
        self.selection_updater.stop_run()
        self.cells.delete('selection')

    def mouse_moved_in_canvas(self, event):
        self.mouse_loc_from_event(event)

    def draw_selection(self):
        self.cells.delete('selection')

        x = self.selection_updater.x
        y = self.selection_updater.y

        def get_selectioncolor(x, y):
            if not self.cells[x][y]:
                return self._settings['selection']['color']
            else:
                return self._settings['selection']['color_over_cell']

        if self.patternselection is None:
            self.cells.draw_cell(x, y, get_selectioncolor(x, y), 'selection')
        else:
            xstart = x - self.patternselection.center_x
            ystart = y - self.patternselection.center_y

            def draw_pattern_selection(state, x, y):
                if state != 'b' and state != 'B':
                    x = self.cells.wrap_x(xstart + x)
                    y = self.cells.wrap_y(ystart + y)

                    self.cells.draw_cell(
                        x, y, get_selectioncolor(x, y), 'selection')

            # replace with func

            self.patternselection.interpret(draw_pattern_selection)

    def canvas_press(self, event):
        x = self.cells.grid(event.x)
        y = self.cells.grid(event.y)

        def invert(x, y):
            self.cells[x][y] ^= True

            if self.cells[x][y]:
                self.cells.draw_cell(x, y)
            else:
                self.cells.undraw_cell(x, y)

        if self.patternselection is None:
            invert(x, y)

        else:
            xstart = x - self.patternselection.center_x
            ystart = y - self.patternselection.center_y

            def place_pattern(state, x, y):
                if state != 'b' and state != 'B':
                    x = self.cells.wrap_x(xstart + x)
                    y = self.cells.wrap_y(ystart + y)
                    invert(x, y)

            # replace with func

            if self.patternselection.rules != self.rules:
                self.rules = self.patternselection.rules
                self.reset()

            self.patternselection.interpret(place_pattern)

    def enable_pattern_placing(self):
        try:
            self.patternselection = life.Selection(
                self.patterns[self.selected_pattern_name])
        except KeyError:
            pass
        else:
            self.place_pattern_button['text'] = "X"

    def disable_pattern_placing(self):
        self.patternselection = None
        self.place_pattern_button['text'] = "Place Patterns"

    def toggle_pattern_placing(self):
        if self.patternselection is None:
            self.enable_pattern_placing()
        else:
            self.disable_pattern_placing()

    def pattern_selected(self, event):
        pattern = self.patterns[self.selected_pattern_name]
        self.pattern_info.set(str.format("{}: W: {} H: {} B: {} S: {}",
                              self.selected_pattern_name,
                              str(pattern.width),
                              str(pattern.height),
                              str(pattern.rules.b),
                              str(pattern.rules.s)))

    @property
    def selected_pattern_name(self):
        return self.pattern_selection_box.get()

    @property
    def cell_size(self):
        return int(self.entry_str.get())

    @cell_size.setter
    def cell_size(self, new_cell_size):
        self.entry_str.set(new_cell_size)

    def reset(self):
        self.cell_updater.stop_run()

        try:
            new_cell_size = self.cell_size
        except AttributeError:
            self.cells.reset()
        else:
            if self.cells.cellsize != new_cell_size:
                limit = int(self._settings['cell']['size_limit'])
                if new_cell_size < limit:
                    new_cell_size = limit

                self.cells.cellsize = new_cell_size

                # if cell size becomes too big, hide canvas
                if (self.cells.canvaswidth == 0 or
                        self.cells.canvasheight == 0):
                    self.cells.config(width=0, height=0)
                else:
                    self.cells.config(
                        width=self.cells.canvaswidth,
                        height=self.cells.canvasheight)
            else:
                self.cells.reset()


class Updater(object):
    def __init__(self, rate, func, root,
                 start_run_func=None, stop_run_func=None):
        self.rate = rate
        self.func = func
        self.start_run_func = start_run_func
        self.stop_run_func = stop_run_func
        self.root = root
        self.update_process = None

    def set_update_rate(self, new_update_rate):
        wasrunning = False
        if self.isrunning:
            self.stop_run()
            wasrunning = True

        self.rate = new_update_rate

        if wasrunning:
            self.start_run()

    def start_run(self):
        if self.start_run_func is not None:
            self.start_run_func()

        if self.isrunning:
            self.stop_run()

        self._schedule_next_update()

    def stop_run(self):
        if self.stop_run_func is not None:
            self.stop_run_func()

        if self.isrunning:
            self.root.after_cancel(self.update_process)
            self.update_process = None

    def toggle_run(self):
        if self.isrunning:
            self.stop_run()
        else:
            self.start_run()

    @property
    def isrunning(self):
        if self.update_process is not None:
            return True
        return False

    def _schedule_next_update(self):
        self.update_process = self.root.after(
            self.rate, self._update)

    def _update(self):
        self.func()
        self._schedule_next_update()
