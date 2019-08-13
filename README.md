# Dota2 match prediction

After scraping opendota.com for pro team match history, I ran several classification algorithms to attempt to fit the hero picks and teams to predict which team will win.

# Dota2 pro team info

Combining requests, plotly, and D3 to graph pro teams' players' win rates, the teams' hero win rates, and animated/timed plots of team fights of recent matches

## Flask app

There's some excess files, but app.py runs a flask server. The main index runs the match predictions. The "/teamviz" path runs the info page.

## Libraries Used
Pandas, XGBoost, SKLearn, keras, Matplotlib, Pymongo, datetime, numpy, scipy, random, pickle
