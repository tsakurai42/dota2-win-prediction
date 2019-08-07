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
ti_invites = [1838315, 1883502, 726228, 39, 2163, 15, 350190,6214973,
                    2108395, 2586976, 111474, 2626685, 6209804, 543897, 36, 7203342, 2672298, 1375614]
team_names = ['Team Secret', 'Virtus Pro', 'Vici Gaming', 'Evil Geniuses', 'Team Liquid', 'PSG.LGD', 'Fnatic', 'Ninjas in Pyjamas',
              'TNC Predator', 'OG', 'Alliance', 'Keen Gaming', 'Newbee', 'Infamous', 'Chaos Esports Club', 'Natus Vincere', 'Royal Never Give Up', 'Mineski']

              #qualifiers start at Newbee, at 6209804

#this entire next section should be commented out on re-run whenever the script breaks and you have to go search for the match_ID that broke it.
matches_parsed_in_db = dota_team_match_collection.count_documents({})
matches_parsed = []
if matches_parsed_in_db != 0:
    match_ids = dota_team_match_collection.find({}, {'match_id': 1, '_id': 0})
    for each_match in match_ids:
        matches_parsed.append(each_match['match_id'])  #create list of every match already in the db
for team_id in ti_invites:
    dota_data_response = requests.get(
        f'{DotaAPIurl_base}teams/{team_id}/matches')
    dota_data = dota_data_response.json()
    remade_data = []
    remake_match = {}
    for each_match in dota_data:
        if each_match['start_time'] > 1498000000 and each_match['match_id'] not in matches_parsed: #start time at TI7 and match not already in db
            matches_parsed.append(each_match['match_id'])
            remake_match = {}
            remake_match['match_id'] = each_match['match_id']
            remake_match['winner'] = 'Radiant' if each_match['radiant_win'] == True else 'Dire'

            if each_match['radiant'] == True:
                remake_match['radiant_team_id'] = team_id
                remake_match['dire_team_id'] = each_match['opposing_team_id']
            else:
                remake_match['radiant_team_id'] = each_match['opposing_team_id']
                remake_match['dire_team_id'] = team_id
            remake_match['duration'] = each_match['duration']
            remake_match['start_time'] = each_match['start_time']
            remade_data.append(remake_match)
    # print(remade_data)
    dota_team_match_collection.insert_many(remade_data)
    print(f'added {team_id}')


matches = dota_team_match_collection.find()
total_num_matches = dota_team_match_collection.count_documents({})
print(f'{total_num_matches}')
for enum, each_match in enumerate(matches):
    if 'patch' not in each_match.keys():
        dota_data_response = requests.get(
            f'{DotaAPIurl_base}matches/{each_match["match_id"]}')
        dota_data = dota_data_response.json()
        picks = {}
        r = 1
        d = 1
        print(
            f'{enum+1}/{total_num_matches}: {each_match["match_id"]} {each_match["_id"]}')
        # print(dota_data['picks_bans'])
        if dota_data['picks_bans'] != None:
            for each_pickban in dota_data['picks_bans']:
                if each_pickban['is_pick'] == True:
                    if r == 1 and d == 1:
                        picks[f'first_pick_team'] = 'Radiant' if each_pickban['team'] == 0 else 'Dire'

                    if each_pickban['team'] == 0:
                        picks[f'radiant_pick_{r}'] = each_pickban['hero_id']
                        r += 1
                    elif each_pickban['team'] == 1:  # could just say else
                        picks[f'dire_pick_{d}'] = each_pickban['hero_id']
                        d += 1
        else:
            dota_team_match_collection.delete_one({'_id': each_match['_id']})
            print('deleted record')
        picks['patch'] = dota_data['patch']

        dota_team_match_collection.update_one(
            {'_id': each_match['_id']}, {'$set': picks})
        time.sleep(1)
