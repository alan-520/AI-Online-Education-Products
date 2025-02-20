"""
# Project           : Gamification Web
# Author            : Heping Zhao
# Date created      : 25/10/2019
# Description       : Game System
"""
import requests
import json

# set the apikey and limit
apikey = "TBOV2Y433YH8"  # test value
lmt = 8

# our test search
search_term = "excited"

# get the top 8 GIFs for the search term
r = requests.get(
    "https://api.tenor.com/v1/search?q=%s&key=%s&limit=%s" % (search_term, apikey, lmt))

if r.status_code == 200:
    # load the GIFs using the urls for the smaller GIF sizes
    top_8gifs = json.loads(r.content)
    print(top_8gifs)
else:
    top_8gifs = None


# continue a similar pattern until the user makes a selection or starts a new search.
