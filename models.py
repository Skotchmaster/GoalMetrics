from flask_login import UserMixin
from database import get_connection

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

def load_user(user_id):
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

    if not user:
        return None

    return User(id=user["id"], username=user["name"], password=user["password"])  # ✅ Используем ключи

