import sys
from lib import sgf


with open(sys.argv[1]) as sgffile:
    txt = sgffile.read()


sgf.parse(txt)



