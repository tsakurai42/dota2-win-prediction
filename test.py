import json
import requests
from pprint import pprint
import pymongo
#from flask import Flask, jsonify, render_template, redirect
#import pandas as pd
import time
# from bson import BSON
# from bson import json_util

DotaAPIurl_base = "https://api.opendota.com/api/"
conn = 'mongodb://localhost:27017'
client = pymongo.MongoClient(conn)
db_dota = client.dota
dota_team_match_collection = db_dota.team_matches
# dota_team_match_collection.drop()
ti_direct_invites = [1838315, 726228, 1883502, 39, 15]#,
                     #2163, 350190, 6214973, 2108395, 2586976, 111474, 2626685,6209804,543897,36,7203342,2672298,1375614]
# for team_id in ti_direct_invites:
#     dota_data_response = requests.get(f'{DotaAPIurl_base}teams/{team_id}/matches')
#     dota_data = dota_data_response.json()
#     for each_match in dota_data:
#         each_match['team_id'] = team_id

#     dota_team_match_collection.insert_many(dota_data)
#     print(f'added {team_id}')
# dota_team_match_collection.delete_many( {'start_time': {'$lt': 1561804526}})  #1498000000}})

matches = dota_team_match_collection.find()
total_num_matches = dota_team_match_collection.find().count()
print(f'{total_num_matches} boop')
for enum, each_match in enumerate(matches):
    if each_match['radiant'] == True:
        self_team = 0
    else:
        self_team = 1
    other_team = 1-self_team
    dota_data_response = requests.get(f'{DotaAPIurl_base}matches/{each_match["match_id"]}')
    dota_data = dota_data_response.json()
    # print(dota_data)
    picks = {}
    t = 1
    o = 1
    for each_pickban in dota_data['picks_bans']:
        # print(each_pickban)
        if each_pickban['is_pick'] == True:
            if t==1 and o==1:
                if each_pickban['team'] == 0:
                    picks[f'first_pick_team'] = 'Radiant'
                else:
                    picks[f'first_pick_team'] = 'Dire'
            if each_pickban['team'] == self_team:
                picks[f'self_pick{t}'] = each_pickban['hero_id']
                t+=1
            elif each_pickban['team'] == other_team: #could just say else
                picks[f'opposing_pick{o}'] = each_pickban['hero_id']
                o+=1
    picks['patch'] = dota_data['patch']
    print(f'{enum+1}/{total_num_matches}')
    # print(picks)
    # print('-'*15)
    dota_team_match_collection.update_one({'_id':each_match['_id']}, {'$set': picks})
    time.sleep(2)
