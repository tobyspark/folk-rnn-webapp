from datetime import date

# PLEASE DO TOUCH

# The example search terms on the tunes page
TUNE_SEARCH_EXAMPLES = [
        'DeepBach', 
        'Glas Herry', 
        'M:3/4', 
        'K:Cmix', 
        'G/A/G/F/ ED', 
        'dBd edc',
        ]
RECORDING_SEARCH_EXAMPLES = [
        'Ensemble x.y', 
        'Partnerships', 
        'St. Dunstan',
        ]
COMPETITION_SEARCH_EXAMPLES = [
        'August',
        date.today().year,
        'The Humours of Time Pigeon', # TODO: once there are some competitions to know what might be good to search for
        ]
MAX_RECENT_ITEMS = 5 # e.g. how many 'popular tunes' listed on the homepage
TUNE_PREVIEWS_PER_PAGE = 10 # e.g. how many search results are listed on the tunes page
YEAR_CHOICES = range(date.today().year, date.today().year-20, -1)


# PLEASE DON'T TOUCH

default_app_config = 'archiver.apps.ArchiverConfig'

# algorithmic nerdery, here for want of anywhere better
# modified from https://stackoverflow.com/questions/352670/weighted-random-selection-with-and-without-replacement
import heapq
import math
import random
def weightedSelectionWithoutReplacement(seq, weights, k=1):
    assert len(seq) == len(weights) > 0
    elt = [(math.log(random.random()) / weights[i], i) for i in range(len(weights))]
    return [seq[x[1]] for x in heapq.nlargest(k, elt)]