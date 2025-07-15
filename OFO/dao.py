import json
import os

def auth_user(username, password):
    current_dir = os.path.dirname(__file__)
    filepath = os.path.join(current_dir, 'data', 'users.json')  # tức là OFO/data/users.json

    with open(filepath, encoding="utf-8") as f:
        users = json.load(f)

        for u in users:
            if u["username"] == username and u["password"] == password:
                return True

    return False

if __name__ == "__main__":
    print(auth_user("user", 123))