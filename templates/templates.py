import pathlib
from os import listdir
from os.path import isfile, join

path = pathlib.Path(__file__).parent.absolute()
files = [f for f in listdir(path) if isfile(join(path, f)) and f.endswith('.txt')]

TEMPLATE = {}

for file in files:
    with open(join(path, file), 'r') as f:
        TEMPLATE[int(file[:-4])] = f.read()

        # This allows us to later get a template based on familiarity level,
        # with least familiar being TEMPLATE[1] and most being the larger levels
