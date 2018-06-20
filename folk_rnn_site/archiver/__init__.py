from datetime import date

MAX_RECENT_ITEMS = 5
TUNE_PREVIEWS_PER_PAGE = 10
YEAR_CHOICES = range(date.today().year, date.today().year-20, -1)




# algorithmic nerdery
# modified from https://stackoverflow.com/questions/352670/weighted-random-selection-with-and-without-replacement
import heapq
import math
import random

def weightedSelectionWithoutReplacement(seq, weights, k=1):
    assert len(seq) == len(weights) > 0
    elt = [(math.log(random.random()) / weights[i], i) for i in range(len(weights))]
    return [seq[x[1]] for x in heapq.nlargest(k, elt)]