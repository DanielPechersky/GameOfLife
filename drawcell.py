import random


def func(locals_):
    x = locals_['x']
    y = locals_['y']
    x_canvas = locals_['x_canvas']
    y_canvas = locals_['y_canvas']
    cellsize = locals_['self'].cellsize
    iteration = locals_['self'].iteration
    tag = locals_['tag']

    colors = ('#0f0', '#0b0', '#0e4')

    color = random.choice(colors)

    locals_['self'].create_rectangle(
        x_canvas, y_canvas,
        x_canvas + cellsize,
        y_canvas + cellsize,
        fill=color,
        width=0, tag=tag)
