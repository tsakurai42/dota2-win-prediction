import json
import requests
from pprint import pprint
import pymongo
from bson import json_util
import pandas as pd
import time

conn = 'mongodb://localhost:27017'
client = pymongo.MongoClient(conn)
db_dota = client.dota
dota_team_match_collection = db_dota.team_matches

with open('team_matches.json') as f:
    for i in f:
        i = json_util.loads(i)
        dota_team_match_collection.insert_one(i)