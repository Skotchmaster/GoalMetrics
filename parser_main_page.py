import requests
from collections import defaultdict
from lxml import html
import pymysql
from datetime import datetime

from config import host, user, password, db_name

def get_connection():
    connection = pymysql.connect(
        host=host,
        port=3306,
        user=user,
        password=password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection


def fetch_html_content(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def check_competition(competition, competiton_name):
    all_competitions ={
    'Премьер-лига': 'https://s.scr365.net/img/flags/3.svg',
    'Примера': 'https://s.scr365.net/img/flags/4m.png',
    'Бундеслига': 'https://s.scr365.net/img/flags/6.svg',
    'Серия А': 'https://s.scr365.net/img/flags/2.svg',
    'Лига 1': 'https://s.scr365.net/img/flags/7.svg',
    'Чемпионат Мира': 'https://s.scr365.net/s1/logo/22_33_11/46atU_16_742.png',
    'Чемпионат Европы': 'https://s.scr365.net/s1/logo/22_282_9/A7dqy_16_24.png',
    'Российская премьер-лига': 'https://s.scr365.net/img/flags/1.svg',
    'Лига чемпионов УЕФА': 'https://s.scr365.net/s1/logo/21_69_9/to3rP5Z_16_19.svg'}
    for key, value in all_competitions.items():
        if value == competition and competiton_name == key:
            return key, value
    return False

def get_data(date):
    results = defaultdict(list)
    base_page = fetch_html_content(f'https://soccer365.ru/online/&date={date}')
    tree = html.fromstring(base_page)
    table = tree.xpath('//div[@id="result_data"]')
    if table:
        for index in range(1, 8):
            competition_img = tree.xpath(f'//div[@class="live_comptt_bd"][{index}]//div[@class="block_header"]//div[@class="img16"]//img/@src')[0]
            competition_name = tree.xpath(f'//div[@class="live_comptt_bd"][{index}]//div[@class="block_header"]//div[@class="img16"]//span/text()')[0]
            if check_competition(competition_img, competition_name) is not False:
                index_of_game = 1
                while tree.xpath(f'//div[@class="live_comptt_bd"][{index}]//div[@class="game_block"][{index_of_game}]'):
                    status = tree.xpath(f'//div[@class="live_comptt_bd"][{index}]//div[@class="game_block"][{index_of_game}]//div[@class="status"]//span/text()')
                    if not status:
                        status = tree.xpath(f'//div[@class="live_comptt_bd"][{index}]//div[@class="game_block"][{index_of_game}]//div[@class="status"]/text()')
                    status = status[0]
                    first_team = tree.xpath(f'//div[@class="live_comptt_bd"][{index}]//div[@class="game_block"][{index_of_game}]//div[@class="result"]//div[@class="ht"]//div[@class="name"]//span/text()')[0]
                    first_team_img = tree.xpath(
                        f'//div[@class="live_comptt_bd"][{index}]//div[@class="game_block"][{index_of_game}]//div[@class="ht"]//div[@class="name"]//img/@src')[0]
                    second_team = tree.xpath(
                        f'//div[@class="live_comptt_bd"][{index}]//div[@class="game_block"][{index_of_game}]//div[@class="result"]//div[@class="at"]//div[@class="name"]//span/text()')[0]
                    second_team_img = tree.xpath(
                        f'//div[@class="live_comptt_bd"][{index}]//div[@class="game_block"][{index_of_game}]//div[@class="result"]//div[@class="at"]//div[@class="name"]//img/@src')[0]
                    goals_first = tree.xpath(
                        f'//div[@class="live_comptt_bd"][{index}]//div[@class="game_block"][{index_of_game}]//div[@class="result"]//div[@class="ht"]//div[@class="gls"]/text()')[0]
                    goals_second = tree.xpath(f'//div[@class="live_comptt_bd"][{index}]//div[@class="game_block"][{index_of_game}]//div[@class="result"]//div[@class="at"]//div[@class="gls"]/text()')[0]
                    tour = tree.xpath(f'//div[@class="live_comptt_bd"][{index}]//div[@class="game_block"][{index_of_game}]//div[@class="stage"]/text()')[0]
                    results[check_competition(competition_img, competition_name)[0]].append([date, tour, status, first_team, first_team_img, second_team, second_team_img, goals_first + ":" + goals_second])
                    index_of_game += 1
    print(results)
    return results

def create_db_connection():
    try:
        connection = pymysql.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as ex:
        print("Connection refused...")
        print(ex)
        return None

def create_main_page(connection, columns):
    with connection.cursor() as cursor:
        create_table_query = f"CREATE TABLE IF NOT EXISTS `главная страница` ({columns})"
        cursor.execute(create_table_query)
        connection.commit()

def insert_data_in_main_page(connection, data):
    with connection.cursor() as cursor:
        insert_query = """
        INSERT INTO `главная страница` (дата, соревнование, тур, статус, первая_команда, эмблема_первой_комады, вторая_команда, эмблема_второй_команды, счет)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            тур = VALUES(тур),
            статус = VALUES(статус),
            эмблема_первой_комады = VALUES(эмблема_первой_комады),
            эмблема_второй_команды = VALUES(эмблема_второй_команды),
            счет = VALUES(счет)
        """
        cursor.execute(insert_query, data)
        connection.commit()

connection = create_db_connection()
create_main_page(connection, """
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    дата VARCHAR(64),
                    соревнование VARCHAR(64),
                    тур VARCHAR(64),
                    статус VARCHAR(64),
                    первая_команда VARCHAR(64),
                    эмблема_первой_комады VARCHAR(255),
                    вторая_команда VARCHAR(64),
                    эмблема_второй_команды VARCHAR(255),
                    счет VARCHAR(64),
                    UNIQUE KEY unique_match (дата, первая_команда, вторая_команда)
                """)


# def generate_date_range_and_parse(start_date, end_date):
#     current_date = start_date
#     while current_date <= end_date:
#         all_data = get_data(current_date.strftime('%Y-%m-%d'))
#         for competition in all_data.keys():
#             for game in all_data[competition]:
#                 game_data = game
#                 game_data.insert(1, competition)
#                 insert_data_in_main_page(connection, game_data)
#         current_date += timedelta(days=1)
#
# start_date = datetime(2024, 6, 1).date()
# end_date = datetime(2025, 1, 28).date()
#
# generate_date_range_and_parse(start_date, end_date)



def add_data():
    connection = create_db_connection()
    current_date = datetime.now().date()
    all_data = get_data(current_date)

    for competition in all_data.keys():
        for game in all_data[competition]:
            game_data = game
            game_data.insert(1, competition)
            insert_data_in_main_page(connection, game_data)