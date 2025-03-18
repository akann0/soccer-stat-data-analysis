# %%
import soccerdata as sd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# %%
# Setup a scraper for the 2021/2022 Premier League season
ws = sd.WhoScored(leagues="ENG-Premier League", seasons=2021)
# Scrape all games
api = ws.read_events()

# %%


# %%
ws

# %%
ws.leagues

# %%
#get the data types for each column
api.dtypes

# %%
api

# %%
api["type"].unique()

# %%
gameId = 1485563
# get rows where the gameId is equal to the gameId variable
game = api[api["game_id"] == gameId]

# %%
# lets see all columns, so zero max
pd.set_option("display.max_columns", 0)

game[game["is_goal"] == True]

# %% [markdown]
# In order to show what actions are likely to lead to goals, I have to create a stat, similar to xG, which shows the expected likelyhood of the team scoring based on the action shown.  In order to backderive this we must first add the data point of when the next goal was scored (and by whom)into the dataframe.

# %%
goals = api[api["type"] == "Goal"]
goals

# split goals into a dictionary based on gameId so it can be accessed by gameId in linear time
goals_dict = dict(tuple(goals.groupby("game_id")))
goals_dict

# %%
def getTimeandTeamToNextGoal(moment, goals_dict):
    # get the game_id, team_name, time_min, and time_sec from the moment
    game_id = moment["game_id"]
    half = moment["period"]
    team_name = moment["team"]
    time_min = moment["minute"]
    time_sec = moment["second"]
    # get goals from the game
    game_goals = pd.DataFrame()
    if game_id in goals_dict:
        game_goals = goals_dict[game_id]
    # get goals that happened after the time_min and time_sec
        game_goals = game_goals[
        ((game_goals["minute"] > time_min)
        | ((game_goals["minute"] == time_min) & (game_goals["second"] > time_sec)))
        & (game_goals["period"] == half)
        ]
    # if there are no goals after the time_min and time_sec, return 90
    if len(game_goals) == 0:
        return 0
    # get the first goal that happened after the time_min and time_sec
    goal = game_goals.iloc[0]
    # return the minute of the goal
    team = 1 if goal["team"] == team_name else -1
    return team * (goal["minute"] - time_min)


# %%


# %%
# let's cut api into 10 games so that running analysis is faster
games = api["game_id"].unique()
print(len(games))
games = np.array_split(games, len(games) // 50)

first_ten_games = api[api["game_id"].isin(games[0])]
first_ten_games["next_goal"] = first_ten_games.apply(lambda x: getTimeandTeamToNextGoal(x, goals_dict), axis=1)
first_ten_games

# %%
X_SECTIONS = 6
Y_SECTIONS = 3
MINUTES_AFTER_STUDIED = 90

first_ten_games["rounded_x"] = round(first_ten_games["x"]*X_SECTIONS - 50, -2) // 100
first_ten_games["rounded_y"] = round(first_ten_games["y"]*Y_SECTIONS - 50, -2) // 100

print("check", first_ten_games["rounded_x"].value_counts())
print("check2", first_ten_games["rounded_y"].value_counts())

# I'm gonna want to make a line graph out of data, what should this data look like?
# for now, just right in front of the goal
opponent_box = pd.DataFrame(columns=["attack_goal", "defense_goal", "attack_up_to_now", "defense_up_to_now", "attack_after_now", "defense_after_now"])

for x in range(X_SECTIONS):
    for y in range(Y_SECTIONS):
        passes_in_range = first_ten_games[first_ten_games["rounded_x"] == x]
        passes_in_range = passes_in_range[passes_in_range["rounded_y"] == y]
        print(f"({x*10},{y*10}) - {len(passes_in_range)}")

        # get the quanities for each next_goal value
        quantities = passes_in_range["next_goal"].value_counts()

        #get the totals, so we can count "the rest" easier
        totals = [0, 0]
        for i in range(MINUTES_AFTER_STUDIED):
            if i in quantities:
                totals[0] += quantities[i]
            if -i in quantities:
                totals[1] += quantities[-i]
        totals.append(totals[0] + totals[1])


        us = 0
        them = 0
        for i in range(MINUTES_AFTER_STUDIED-85):
            if i == 0:
                continue
            # count the quanitiy value i, -i
            current = [0,0]
            if i in quantities:
                current[0] = quantities[i]
            if -i in quantities:
                current[1] = quantities[-i]
            us += current[0]
            them += current[1]
            if i in [1, 5, 10]:
                print(f"({x*10},{y*10}) - {i} - {us} - {them}")
            if (x == 5 and y == 1):
                # total = len(passes_in_range)
                total = us+them
                curr_total = current[0]+current[1]
                curr_total = curr_total if curr_total > 0 else 1
                
                
                # opponent_box.loc[i] = [current[0]/curr_total, current[1]/curr_total, us/total, them/total, (totals[0]-us)/(totals[2]-total), (totals[1]-them)/(totals[2]-total)]
                opponent_box.loc[i] = [(us/i)/len(passes_in_range), (them/i)/len(passes_in_range), 0,0,0,0]
        
# get the quanities for each next_goal value





# %%
# make a line graph for the opponent box
opponent_box.plot.line()

# %% [markdown]
# There's an obvious confounding variable I forgot to consider here - given the position, the attacking team is more likely to score 15 minutes from now not because of the position they were in 10 minutes ago, but because better teams have the ball in the attacking area more.  Subtracting out this confounding variable might lead us to better results; but we will have to get to that later.  

# %% [markdown]
# 


