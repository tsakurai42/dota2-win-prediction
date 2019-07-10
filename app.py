import json
import requests
from pprint import pprint
import pymongo
from flask import Flask, jsonify, render_template, redirect
import pandas as pd
import time
from bson import BSON
from bson import json_util

# OWAPIurl_base = "https://api.overwatchleague.com/"
DotaAPIurl_base = "https://api.opendota.com/api/"

# /teams/{team_id}/team = same data as without teamid, but just one team's data - not useful if i already pulled all the teams' datas
# /teams/{team_id}/matches = chronological(most recent first) of matches played by team
# /teams/{team_id}/heroes = heroes used games played, wins, with hero_id
# /teams/{team_id}/players = all players who have ever played on this team. Has flag "is_current_team_member" to sort by current members
# --
# /proPlayers = list of all pro players, with their "name" (pro name), current team id, team name, if pro, and country code. fantasy_role 1 = core, 2 = supp
#
# /proMatches = seems to only have one pramater of less than match id to find more data. does not seem to have a "only pull leagueid" type parameter
# /leagues = list of tournaments. "tier":"premier" seems to be the top top tournaments

# dota_data_response = requests.get(f'{DotaAPIurl_base}teams') #JSON CALL
# dota_data = dota_data_response.json()

# TEMP WRITE AND READ FROM FILE SO AS NOT TO BOMB THE API SERVER
# with open('dotadata_teams.txt','w') as write_file:
#     json.dump(dota_data, write_file)

# with open('dotadata_players.txt') as json_file:
#     dota_data = json.load(json_file)
app = Flask(__name__)
conn = 'mongodb://localhost:27017'
client = pymongo.MongoClient(conn)

# client.drop_database('dota_teams')
# client.drop_database('dota_players')

db_dota = client.dota
dota_teams_collection = db_dota.teams
dota_players_collection = db_dota.players
dota_players_on_teams_collection = db_dota.players_on_teams
dota_team_hero_stats_collection = db_dota.team_hero_stats

ti_direct_invites = [1838315, 726228, 1883502, 39, 15,
                     2163, 350190, 6214973, 2108395, 2586976, 111474, 2626685]


# only 'relevant' teams that have a more recent match than August 13, 2017, day after TI7 finished
# recent_teams = dota_teams_collection.find(
#     {'last_match_time': {'$gt': 1502582400}, 'wins': {'$gt': 50}})
# dota_teams_collection.delete_many({'name':''})  #some teams seem to be 'abandoned' with high rating but no name.

# this function takes forever, so do not run it often!!!!!!! it runs a call for every team that the above filter finds (last match last 2 yeras, over 50 wins)
# for each_team in recent_teams:
#     dota_data_response = requests.get(f'{DotaAPIurl_base}teams/{each_team["team_id"]}/players') #JSON CALL
#     dota_data = dota_data_response.json()
#     for each_player in dota_data:
#         each_player['team_id']  = each_team['team_id']
#     # pprint(dota_data)
#     dota_players_on_teams_collection.insert_many(dota_data)
#     print(f'finished {each_team["team_id"]} sleep5')
#     time.sleep(5)

#  had to add team name to each player listed because it was annoying to only work with team_id
# all_players = dota_players_on_teams_collection.find()
# for each_player in all_players:
#     dota_players_on_teams_collection.update({'_id':each_player['_id']}, {'$set': {'team_name':dota_teams_collection.find_one({'team_id':each_player['team_id']})['name']}})


@app.route('/')
def index():
    return render_template('index.html')
    # main page ish
    # instead of redirects, just request.get().json() my own website


@app.route('/topteams')
def topteams():
    pro_teams = dota_teams_collection.find(
        {'team_id': {'$in': ti_direct_invites}}, {'_id': 0})
    team_list = []
    for each_team in pro_teams:
        # is_current_team = dota_players_on_teams_collection.find_one(
        #     {'team_id': each_team['team_id'], 'is_current_team_member': True}, {'_id': 0})
        # if is_current_team != None:  # only use teams that have a current member ie active teams
        team_list.append(each_team)
    return jsonify(team_list)


@app.route('/playersontopteams/<team_id>')
def topplayers(team_id):
    team_players = dota_players_on_teams_collection.find(
        {'team_id': int(team_id), 'is_current_team_member': True}, {'_id': 0})
    team_list = []
    for each_player in team_players:
        # print(each_player)
        team_list.append(each_player)
    return jsonify(team_list)


@app.route('/teamherostats/<team_id>')
def team_heroes(team_id):
    hero_data = dota_team_hero_stats_collection.find_one({'team_id': int(team_id)},{'_id':0})
    # pprint(hero_data['hero_data'])
    return(jsonify(hero_data['hero_data']))

# @app.route('/buildteamherostats')
# def build_team_heroes():
#     for eachteamid in ti_direct_invites:
#         dota_data_response = requests.get(
#             f'{DotaAPIurl_base}teams/{eachteamid}/heroes')  # JSON CALL
#         dota_data = dota_data_response.json()
#         hero_data = {}
#         for each_hero in dota_data:
#             hero_data[str(each_hero['hero_id'])] = {
#                 'wins': each_hero['wins'], 'games_played': each_hero['games_played'], 'localized_name': each_hero['localized_name']}
#         # pprint(dota_data)
#         pprint(hero_data)
#         dota_team_hero_stats_collection.insert_one(
#             {'team_id': eachteamid, 'hero_data': hero_data})

@app.route('/rebuildalldatadangerdanger')
def rebuild_db():

    #doesn't rebuild players collection but if needed i guess i can add it

    dota_teams_collection.drop()
    dota_data_response = requests.get(f'{DotaAPIurl_base}teams')  # JSON CALL
    dota_data = dota_data_response.json()
    dota_teams_collection.insert_many(dota_data)
    # some teams seem to be 'abandoned' with high rating but no name.
    dota_teams_collection.delete_many({'name': ''})

    # collection of players on TI teams
    dota_players_on_teams_collection.drop()
    TI_teams = dota_teams_collection.find(
        {'team_id': {'$in': ti_direct_invites}}, {'_id': 0})
    for each_team in TI_teams:
        dota_data_response = requests.get(
            f'{DotaAPIurl_base}teams/{each_team["team_id"]}/players')  # JSON CALL
        dota_data = dota_data_response.json()
        for each_player in dota_data:
            each_player['team_id'] = each_team['team_id']
        dota_players_on_teams_collection.insert_many(dota_data)
        print(f'finished {each_team["team_id"]} sleep5')
        time.sleep(5)

    # collection of pro players, more data than previous collection
    dota_data_response = requests.get(
        f'{DotaAPIurl_base}proplayers')  # JSON CALL
    dota_data = dota_data_response.json()
    dota_players_collection.drop()
    dota_players_collection.insert_many(dota_data)

    for eachteamid in ti_direct_invites:
        dota_data_response = requests.get(f'{DotaAPIurl_base}teams/{eachteamid}/heroes')  # JSON CALL
        dota_data = dota_data_response.json()
        hero_data = {}
        for each_hero in dota_data:
            hero_data[str(each_hero['hero_id'])] = {
                'wins': each_hero['wins'], 'games_played': each_hero['games_played'], 'localized_name': each_hero['localized_name']}
        dota_team_hero_stats_collection.insert_one({'team_id': eachteamid, 'hero_data': hero_data})
    
    return 'done'
# @app.route(/'specificteam/<team_id>')
# def team():
#     query mongodb for <team_id> data, like wins/losses, current players, current rating
#     return json of team data

# @app.route('/specificplayer/<player_id>')
# def player():
#     query mongodb for player <player_id> data
#     return json of player data


if __name__ == "__main__":
    app.run(debug=True)
