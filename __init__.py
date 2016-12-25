from configparser import RawConfigParser

from tklife import LifeApp

DEFAULTS = {
    'cell':
        {
            'start_size': '15',
            'size_limit': '1',
            'color': 'white',
            'draw_func': ''
        },
    'rules':
        {
            'birth': '3',
            'survival': '2,3'
        },
    'background':
        {
            'color': 'black'
        },
    'grid':
        {
            'color': 'grey'
        },
    'selection':
        {
            'color': 'yellow',
            'color_over_cell': 'red'
        },
    'pattern_directories':
        {
            'startup': ''
        }
}

config_file = 'settings.cfg'

if __name__ == '__main__':
    settings = RawConfigParser()
    settings.read_dict(DEFAULTS)

    # read settings
    try:
        with open(config_file, 'r') as f:
            settings.read_file(f)
    except (FileNotFoundError, IOError):
        pass

    # write to settings
    try:
        with open(config_file, 'w') as f:
            settings.write(f)
    except IOError:
        pass

    app = LifeApp(None, settings=settings)
