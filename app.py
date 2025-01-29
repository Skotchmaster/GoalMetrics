from flask import Flask, render_template, request, redirect, url_for, session
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date
from database import fetch_data_from_table, main_page, main_page_other, table, main_page_bd
from parser_main_page import add_data

app = Flask(__name__)

@app.route('/<string:league>/<string:year>')
def show_year(year, league):
    year = year.replace('-', '/')
    match_data = fetch_data_from_table(year, league)
    if league not in ['лига чемпионов уефа', 'чемпионат мира', 'чемпионат европы']:
        teams = table(league, year)
        return render_template('leagues/league_results.html', matches=match_data, teams=teams, year=year, league=league)
    else:
        return render_template('leagues/league_results.html', matches=match_data, teams=None, year=year, league=league)

@app.route('/')
def index():
    current_day = date.today()
    return render_template("main.html", grouped_matches=main_page_bd(current_day))

@app.route('/main_page/<string:date>')
def main_page_every_day(date):
    return render_template("main.html", grouped_matches=main_page_bd(date))

@app.route('/<string:competition>')
def league(competition):
    if competition not in ['лига чемпионов уефа', 'чемпионат мира', 'чемпионат европы']:
        main_page_competition = main_page(competition)
    else:
        main_page_competition = main_page_other(competition)
    return render_template('leagues/league.html', teams=dict(sorted(main_page_competition.items(), reverse=True)), league=competition)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(add_data, 'interval', minutes=2, id='add_data_job', replace_existing=True)
    scheduler.start()

    app.run(debug=True)
