import sys

import numpy as np

from apiConnection import get_data
import pandas as pd
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
from tabulate import  tabulate


nbaList = ['player_points_rebounds_assists']
nflList = ['player_pass_yds','player_rush_yds','player_reception_yds']
sportIds = ['basketball_nba']

if len(sys.argv)==2:
    apiKey = sys.argv[1]
def getEventIds(sport):
    eventIdList = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={apiKey}&regions=us&markets=h2h,spreads&oddsFormat=american"
    return get_data(eventIdList)


def getOdds(sport,statType):

    playerOddsDataFrameList = []
    result_dict = getEventIds(sport)
    for value in result_dict:
        eventId = value['id']
        stringValue = f"https://api.the-odds-api.com/v4/sports/{sport}/events/{eventId}/odds?apiKey={apiKey}&regions=us&markets={statType}&oddsFormat=american&bookmaker=fanduel"
        result_dict = get_data(stringValue)
        game_name = result_dict['home_team'] + ' vs ' + result_dict['away_team']
        game_date = result_dict['commence_time']
        try:
            result_dict = result_dict['bookmakers'][0]
            result_dict = result_dict['markets'][0]
            for odds in result_dict['outcomes']:
                odds_dict = {
                    'game_name': game_name,
                    'player_name': odds['description'],
                    'casinoLine': odds['point'],
                    'date': game_date
                }
                playerOddsDataFrameList.append(pd.DataFrame(odds_dict, index = [0]))
        except IndexError:
            print(f'odds for {game_name} not out yet!')
    playerOddsDataFrame = pd.concat(playerOddsDataFrameList, ignore_index=True)
    playerOddsDataFrame.drop_duplicates(subset = ['game_name','player_name'], inplace=True,ignore_index=True,keep='first')

    return playerOddsDataFrame

def getPlayerStats(sport, statType):
    playerOddsDf = getOdds(sport,statType)

    playerList = playerOddsDf['player_name'].unique()

    allCurrentPlayer = pd.DataFrame(players.get_active_players())

    playerOddsDf['seasonAvgTotal'] = float(0)
    playerOddsDf['last5gamesTotal'] = float(0)

    for name in playerList:
        try:
            player_id = allCurrentPlayer.loc[allCurrentPlayer['full_name'] == name]['id'].iloc[0]
            gameLogs = playergamelog.PlayerGameLog(player_id = player_id, season='2023')
            gameLogs = gameLogs.get_data_frames()[0]
            gameLogsLast5 = gameLogs.head(5)
            averagesSum = (gameLogs['PTS'].sum() + gameLogs['REB'].sum() + gameLogs['AST'].sum())/(len(gameLogs))
            averagesSum5games = (gameLogsLast5['PTS'].sum() + gameLogsLast5['REB'].sum() + gameLogsLast5['AST'].sum())/(len(gameLogsLast5))
            playerOddsDf.loc[playerOddsDf.player_name == name, ['seasonAvgTotal','last5gamesTotal']] = averagesSum, averagesSum5games
        except:
            playerOddsDf = playerOddsDf[playerOddsDf['player_name'] != name]
            print(f'{name} not found')

    playerOddsDf['5gamesDiff'] = playerOddsDf['last5gamesTotal'] - playerOddsDf['casinoLine']
    playerOddsDf['seasonDiff'] = playerOddsDf['seasonAvgTotal'] - playerOddsDf['casinoLine']
    playerOddsDf['combinationDiff'] = playerOddsDf['seasonDiff'] + playerOddsDf['5gamesDiff']


    return playerOddsDf.sort_values('combinationDiff', ascending = False)

print(tabulate(getPlayerStats('basketball_nba','player_points_rebounds_assists'), headers='keys'))