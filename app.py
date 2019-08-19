import json
import requests
from pprint import pprint
import pymongo
from flask import Flask, jsonify, render_template, redirect,request, flash
import pandas as pd
import time
from bson import BSON
from bson import json_util
import pickle
import xgboost as xgb


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
app.secret_key = b'jf87w978ey2bfkcoxc829345876398485'
conn = 'mongodb://localhost:27017'
client = pymongo.MongoClient(conn)

# client.drop_database('dota_teams')
# client.drop_database('dota_players')

db_dota = client.dota
dota_teams_collection = db_dota.teams
dota_players_collection = db_dota.players
dota_players_on_teams_collection = db_dota.players_on_teams
dota_team_hero_stats_collection = db_dota.team_hero_stats
dota_team_match_collection = db_dota.team_matches

ti_direct_invites = [1838315, 726228, 1883502, 39, 15,
                     2163, 350190, 6214973, 2108395, 2586976, 111474, 2626685]

#qualifiers         #add royal never give up, mineski, na'vi, chaos esports club, infamous, newbee
                        #6209804            543897      36      7203342         2672298     1375614

# only 'relevant' teams that have a more recent match than August 13, 2017, day after TI7 finished
# recent_teams = dota_teams_collection.find(
#     {'last_match_time': {'$gt': 1502582400}, 'wins': {'$gt': 50}})
#                   1498000000 is close to start of TI
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
def predictorindex():
    return render_template('index2.html')

@app.route("/calculate", methods=["GET","POST"])
def calc():
    datadata = request.form
    print(f'data is {datadata}')
    ti_invites_id = [1838315, 1883502, 726228, 39, 2163, 15, 350190, 6214973, 2108395, 2586976, 111474, 2626685, 6209804, 543897, 36, 2672298, 1375614]
    ti_invites_name = ['Team Secret', 'Vici Gaming', 'Virtus.Pro', 'Evil Geniuses', 'PSG.LGD', 'Team Liquid', 'Fnatic', 'Ninjas in Pyjamas', 'TNC Predator', 'OG', 'Alliance', 'Keen Gaming', 'Royal Never Give Up', 'Mineski', 'Natus Vincere', 'Infamous Gaming', 'Newbee']
    print(datadata['radiant_team'])
    print(datadata['dire_team'])
    for _ in datadata.getlist('radiant_heroes'):
        print(f'rad: {_}')
    if "1" in datadata.getlist('radiant_heroes'):
        print('test worked!')
    print(datadata['radiant_heroes'])
    print(datadata['dire_heroes'])
    X_test = [41,1,0]
    hero_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 119, 120, 121, 129]
    hero_dict = { 86: 'Rubick', 106: 'Ember Spirit', 7: 'Earthshaker', 50: 'Dazzle', 29: 'Tidehunter', 33: 'Enigma', 91: 'Io', 3: 'Bane', 5: 'Crystal Maiden', 13: 'Puck', 11: 'Shadow Fiend', 69: 'Doom', 30: 'Witch Doctor', 55: 'Dark Seer', 74: 'Invoker', 20: 'Vengeful Spirit', 62: 'Bounty Hunter', 9: 'Mirana', 88: 'Nyx Assassin', 26: 'Lion', 84: 'Ogre Magi', 39: 'Queen of Pain', 103: 'Elder Titan', 51: 'Clockwerk', 66: 'Chen', 53: "Nature's Prophet", 100: 'Tusk', 65: 'Batrider', 15: 'Razor', 6: 'Drow Ranger', 109: 'Terrorblade', 2: 'Axe', 99: 'Bristleback', 12: 'Phantom Lancer', 76: 'Outworld Devourer', 10: 'Morphling', 98: 'Timbersaw', 68: 'Ancient Apparition', 28: 'Slardar', 78: 'Brewmaster', 19: 'Tiny', 90: 'Keeper of the Light', 23: 'Kunkka', 80: 'Lone Druid', 8: 'Juggernaut', 16: 'Sand King', 79: 'Shadow Demon', 114: 'Monkey King', 17: 'Storm Spirit', 107: 'Earth Spirit', 87: 'Disruptor', 95: 'Troll Warlord', 71: 'Spirit Breaker', 63: 'Weaver', 44: 'Phantom Assassin', 72: 'Gyrocopter', 21: 'Windranger', 89: 'Naga Siren', 36: 'Necrophos', 46: 'Templar Assassin', 1: 'Anti-Mage', 22: 'Zeus', 40: 'Venomancer', 102: 'Abaddon', 18: 'Sven', 97: 'Magnus', 96: 'Centaur Warrunner', 60: 'Night Stalker', 54: 'Lifestealer', 85: 'Undying', 25: 'Lina', 41: 'Faceless Void', 64: 'Jakiro', 75: 'Silencer', 43: 'Death Prophet', 92: 'Visage', 67: 'Spectre', 38: 'Beastmaster', 31: 'Lich', 93: 'Slark', 52: 'Leshrac', 61: 'Broodmother', 94: 'Medusa', 47: 'Viper', 48: 'Luna', 45: 'Pugna', 49: 'Dragon Knight', 111: 'Oracle', 77: 'Lycan', 56: 'Clinkz', 58: 'Enchantress', 27: 'Shadow Shaman', 101: 'Skywrath Mage', 113: 'Arc Warden', 70: 'Ursa', 112: 'Winter Wyvern', 42: 'Wraith King', 83: 'Treant Protector', 104: 'Legion Commander', 57: 'Omniknight', 59: 'Huskar', 120: 'Pangolier', 4: 'Bloodseeker', 37: 'Warlock', 35: 'Sniper', 108: 'Underlord', 82: 'Meepo', 73: 'Alchemist', 110: 'Phoenix', 14: 'Pudge', 34: 'Tinker', 81: 'Chaos Knight', 121: 'Grimstroke', 119: 'Dark Willow', 105: 'Techies', 32: 'Riki', 129: 'Mars' }
    for _ in hero_ids:
        if str(_) in datadata.getlist('dire_heroes'):
            X_test.append(1)
        else:
            X_test.append(0)
    for _ in hero_ids:
        if str(_) in datadata.getlist('radiant_heroes'):
            X_test.append(1)
        else:
            X_test.append(0)
    for _ in ti_invites_id:
        if str(_) == datadata['dire_team']:
            X_test.append(1)
        else:
            X_test.append(0)
    for _ in ti_invites_id:
        if str(_) == datadata['radiant_team']:
            X_test.append(1)
        else:
            X_test.append(0)
    # print(X_test)
    match_info = "For match between Radiant: "
    match_info += ti_invites_name[ti_invites_id.index(int(datadata['radiant_team']))] + " ("
    match_info += str([hero_dict[int(_)] for _ in datadata.getlist('radiant_heroes')])
    match_info += ") and Dire: " + ti_invites_name[ti_invites_id.index(int(datadata['dire_team']))] +" ("
    match_info += str([hero_dict[int(_)] for _ in datadata.getlist('dire_heroes')])
    match_info += "), "
    load_model = pickle.load(open('model.pickle.dat','rb'))
    print(load_model)
    prediction = load_model.predict(pd.DataFrame([X_test],columns=['patch', 'fp_dire', 'fp_radiant', 'dire_1', 'dire_2', 'dire_3', 'dire_4', 'dire_5', 'dire_6', 'dire_7', 'dire_8', 'dire_9', 'dire_10', 'dire_11', 'dire_12', 'dire_13', 'dire_14', 'dire_15', 'dire_16', 'dire_17', 'dire_18', 'dire_19', 'dire_20', 'dire_21', 'dire_22', 'dire_23', 'dire_25', 'dire_26', 'dire_27', 'dire_28', 'dire_29', 'dire_30', 'dire_31', 'dire_32', 'dire_33', 'dire_34', 'dire_35', 'dire_36', 'dire_37', 'dire_38', 'dire_39', 'dire_40', 'dire_41', 'dire_42', 'dire_43', 'dire_44', 'dire_45', 'dire_46', 'dire_47', 'dire_48', 'dire_49', 'dire_50', 'dire_51', 'dire_52', 'dire_53', 'dire_54', 'dire_55', 'dire_56', 'dire_57', 'dire_58', 'dire_59', 'dire_60', 'dire_61', 'dire_62', 'dire_63', 'dire_64', 'dire_65', 'dire_66', 'dire_67', 'dire_68', 'dire_69', 'dire_70', 'dire_71', 'dire_72', 'dire_73', 'dire_74', 'dire_75', 'dire_76', 'dire_77', 'dire_78', 'dire_79', 'dire_80', 'dire_81', 'dire_82', 'dire_83', 'dire_84', 'dire_85', 'dire_86', 'dire_87', 'dire_88', 'dire_89', 'dire_90', 'dire_91', 'dire_92', 'dire_93', 'dire_94', 'dire_95', 'dire_96', 'dire_97', 'dire_98', 'dire_99', 'dire_100', 'dire_101', 'dire_102', 'dire_103', 'dire_104', 'dire_105', 'dire_106', 'dire_107', 'dire_108', 'dire_109', 'dire_110', 'dire_111', 'dire_112', 'dire_113', 'dire_114', 'dire_119', 'dire_120', 'dire_121', 'dire_129', 'radiant_1', 'radiant_2', 'radiant_3', 'radiant_4', 'radiant_5', 'radiant_6', 'radiant_7', 'radiant_8', 'radiant_9', 'radiant_10', 'radiant_11', 'radiant_12', 'radiant_13', 'radiant_14', 'radiant_15', 'radiant_16', 'radiant_17', 'radiant_18', 'radiant_19', 'radiant_20', 'radiant_21', 'radiant_22', 'radiant_23', 'radiant_25', 'radiant_26', 'radiant_27', 'radiant_28', 'radiant_29', 'radiant_30', 'radiant_31', 'radiant_32', 'radiant_33', 'radiant_34', 'radiant_35', 'radiant_36', 'radiant_37', 'radiant_38', 'radiant_39', 'radiant_40', 'radiant_41', 'radiant_42', 'radiant_43', 'radiant_44', 'radiant_45', 'radiant_46', 'radiant_47', 'radiant_48', 'radiant_49', 'radiant_50', 'radiant_51', 'radiant_52', 'radiant_53', 'radiant_54', 'radiant_55', 'radiant_56', 'radiant_57', 'radiant_58', 'radiant_59', 'radiant_60', 'radiant_61', 'radiant_62', 'radiant_63', 'radiant_64', 'radiant_65', 'radiant_66', 'radiant_67', 'radiant_68', 'radiant_69', 'radiant_70', 'radiant_71', 'radiant_72', 'radiant_73', 'radiant_74', 'radiant_75', 'radiant_76', 'radiant_77', 'radiant_78', 'radiant_79', 'radiant_80', 'radiant_81', 'radiant_82', 'radiant_83', 'radiant_84', 'radiant_85', 'radiant_86', 'radiant_87', 'radiant_88', 'radiant_89', 'radiant_90', 'radiant_91', 'radiant_92', 'radiant_93', 'radiant_94', 'radiant_95', 'radiant_96', 'radiant_97', 'radiant_98', 'radiant_99', 'radiant_100', 'radiant_101', 'radiant_102', 'radiant_103', 'radiant_104', 'radiant_105', 'radiant_106', 'radiant_107', 'radiant_108', 'radiant_109', 'radiant_110', 'radiant_111', 'radiant_112', 'radiant_113', 'radiant_114', 'radiant_119', 'radiant_120', 'radiant_121', 'radiant_129', 'dire_team_15', 'dire_team_36', 'dire_team_39', 'dire_team_2163', 'dire_team_111474', 'dire_team_350190', 'dire_team_543897', 'dire_team_726228', 'dire_team_1375614', 'dire_team_1838315', 'dire_team_1883502', 'dire_team_2108395', 'dire_team_2586976', 'dire_team_2626685', 'dire_team_2672298', 'dire_team_6209804', 'dire_team_6214973', 'rad_team_15', 'rad_team_36', 'rad_team_39', 'rad_team_2163', 'rad_team_111474', 'rad_team_350190', 'rad_team_543897', 'rad_team_726228', 'rad_team_1375614', 'rad_team_1838315', 'rad_team_1883502', 'rad_team_2108395', 'rad_team_2586976', 'rad_team_2626685', 'rad_team_2672298', 'rad_team_6209804', 'rad_team_6214973']))
    if prediction[0] == 0:
        match_info += "Dire predicted to win"
    elif prediction[0] == 1:
        match_info += "Radiant predicted to win"
    flash(match_info)
    return redirect('../', code=302)

@app.route('/teamviz')
def vizindex():
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

# @app.route('/grabheroandwinlossdata')
# def teamdata_to_db():
#     for team_id in ti_direct_invites:
#         dota_data_response = requests.get(f'{DotaAPIurl_base}teams/{team_id}/matches')
#         dota_data = dota_data_response.json()
#         dota_team_match_collection.insert_many(dota_data)
#     dota_team_match_collection.deleteMany( {'start_time': {'$lt': 1498000000}})
    # game_list = dota_team_match_collection.find( {''})
#dota_team_match_collection = db_dota.team_matches


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