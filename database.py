import pymysql
from collections import defaultdict
from config import host, user, password, db_name
import re

def get_connection():
    return pymysql.connect(
        host=host,
        port=3306,
        user=user,
        password=password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )

def fetch_data_from_table(year, competition):
    try:
        connection = get_connection()
        matches_data = defaultdict(list)
        sorted_matches_data = defaultdict(list)
        extra_tours = defaultdict(list)
        final_tours = defaultdict(list)

        with connection.cursor() as cursor:
            select_all_rows = f"SELECT * FROM `{competition} {year}_результаты_туров`"
            cursor.execute(select_all_rows)
            rows = cursor.fetchall()
            if competition not in ['лига чемпионов уефа', 'чемпионат мира', 'чемпионат европы']:
                for row in rows:
                    if not any(char.isdigit() for char in row['тур']):
                        extra_tours[row['тур']].append(row)
                    else:
                        matches_data[row['тур']].append(row)
                    for tour in sorted(matches_data.keys(), key=lambda x: int(re.findall(r'\d+', x)[0]), reverse=True):
                        sorted_matches_data[tour] = matches_data[tour]
            else:
                for row in rows:
                        matches_data[row['тур']].append(row)
                for tour in matches_data.keys():
                    sorted_matches_data[tour] = matches_data[tour]

        for key, value in extra_tours.items():
            final_tours[key] += value
        for key, value in sorted_matches_data.items():
            final_tours[key] += value

    except Exception as e:
        print(f"Ошибка при доступе к таблице: {e}")
    finally:
        connection.close()

    return final_tours

def main_page(competition):
    try:
        connection = get_connection()
        top_4 = defaultdict(list)
        years_list = get_years_list(competition)

        for year in years_list:
            current_year = format_year(year, competition)
            with connection.cursor() as cursor:
                select_all_rows = f"SELECT * FROM `{competition} {current_year}_таблица`"
                cursor.execute(select_all_rows)
                rows = cursor.fetchall()

                for four in range(4):
                    top_4[current_year].append([rows[four]['эмблема_команды'], rows[four]['название_команды']])

    except Exception as e:
        print(f"Ошибка при доступе к таблице: {e}")
    finally:
        connection.close()

    return top_4

def main_page_other(competition):
    try:
        connection = get_connection()
        top_4 = defaultdict(list)
        with connection.cursor() as cursor:
            select_all_rows = f"SELECT * FROM `{competition}`"
            cursor.execute(select_all_rows)
            rows = cursor.fetchall()
            for row in rows:
                print(row)
                top_4[row['соревнование']].append([row['эмблема_первого_места'], row['первое_место']])
                top_4[row['соревнование']].append([row['эмблема_второго_места'], row['второе_место']])
                top_4[row['соревнование']].append([row['эмблема_третьего_места'], row['третье_место']])
                top_4[row['соревнование']].append([row['эмблема_четвертого_места'], row['четвертое_место']])
    except Exception as e:
        print(f"Ошибка при доступе к таблице: {e}")
    finally:
        connection.close()

    return top_4


def table(competition, year):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            select_table = f"SELECT * FROM `{competition} {year}_таблица`"
            cursor.execute(select_table)
            rows = cursor.fetchall()
    except Exception as e:
        print(f"Ошибка при доступе к таблице: {e}")
    finally:
        connection.close()

    return rows

def get_years_list(competition):
    competition_years = {
        "премьер-лига": {
            "range": range(1889, 2024),
            "excluded": set(range(1915, 1919)) | set(range(1939, 1946))
        },
        "российская премьер-лига": {
            "range": range(1992, 2024),
            "excluded": set()
        },
        "серия а": {
            "range": range(1929, 2024),
            "excluded": set(range(1943, 1945))
        },
        "бундеслига": {
            "range": range(1963, 2024),
            "excluded": set()
        },
        "примера": {
            "range": range(1928, 2024),
            "excluded": set(range(1936, 1939))
        },
        "лига 1": {
            "range": range(1932, 2024),
            "excluded": set(range(1938, 1946))
        },
        "лига чемионов уефа": {
            "range": range(1955, 2024),
            "excluded": set()
        },
        "чемпионат мира": {
            "range": range(1930, 2024, 4),
            "excluded": set(range(1942, 1947, 4))
        },
        "чемпионат европы": {
            "range": range(1960, 2024),
            "excluded": set()
        }
    }

    if competition in competition_years:
        data = competition_years[competition]
        return [year for year in data["range"] if year not in data["excluded"]]
    return []

def format_year(year, competition):
    rpl = competition == "российская премьер-лига" and year in range(1992, 2011)
    wc = competition == "чемпионат мира"
    euro = competition == "чемпионат европы"
    if rpl or wc or euro:
        return str(year)
    return f"{year}/{year + 1}"

def extract_year(year):
    match = re.search(r'\d{4}/\d{4}', year)
    if match:
        return match.group(0)
    return year

def main_page_bd(date):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = f"SELECT * FROM `главная страница` WHERE дата = '{date}';"
            cursor.execute(query)
            res = list(cursor.fetchall())
            grouped_matches = defaultdict(list)
            for match in res:
                grouped_matches[match['соревнование']].append(match)

            grouped_matches = dict(grouped_matches)
            return grouped_matches

    except Exception as e:
        print(f"Ошибка при доступе к таблице: {e}")
        return {}
    finally:
        connection.close()
