from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

from database import fetch_data_from_table, main_page, main_page_other, table, main_page_bd, get_connection
from parser_main_page import add_data
from models import User, load_user
from forms import LoginForm, RegisterForm
import config
app = Flask(__name__)
app.config['SECRET_KEY'] = config.secret_key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.user_loader(load_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        connection = get_connection()
        username = form.username.data
        password = generate_password_hash(form.password.data)

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE name = %s", (username,))
                existing_user = cursor.fetchone()

                if existing_user:
                    flash("Пользователь с таким именем уже существует!", "danger")
                    return redirect(url_for("register"))

                cursor.execute("INSERT INTO users (name, password) VALUES (%s, %s)", (username, password))
                connection.commit()

            flash("Вы успешно зарегистрированы!", "success")
            return redirect(url_for("login"))

        except Exception as e:
            flash(f"Ошибка при регистрации: {e}", "danger")

        finally:
            connection.close()

    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        connection = get_connection()
        if connection is None:
            return render_template('login.html', form=form)

        username = form.username.data
        password = form.password.data

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE name=%s", (username,))
                user = cursor.fetchone()

            if not user:
                return render_template('login.html', form=form)

            if not check_password_hash(user["password"], password):
                return render_template('login.html', form=form)

            user_obj = User(id=user["id"], username=user["name"], password=user["password"])
            login_user(user_obj)


            return redirect(url_for('dashboard', user_id=user["id"]))

        except Exception as e:
            print("Ошибка входа:", e)

        finally:
            connection.close()

    return render_template('login.html', form=form)



@app.route('/dashboard/<int:user_id>')
@login_required
def dashboard(user_id):
    if current_user.id != user_id:
        flash("Вы не можете просматривать чужие страницы!", "danger")
        return redirect(url_for('dashboard', user_id=current_user.id))

    return render_template('dashboard.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы!', 'info')
    return redirect(url_for('login'))

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
    scheduler.add_job(add_data, 'interval', minutes=1, id='add_data_job', replace_existing=True)
    scheduler.start()

    app.run(debug=True)
