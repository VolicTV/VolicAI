import config
class IgnoredUserManager:
    def __init__(self, ignored_users_file):
        self.ignored_users_file = ignored_users_file
        self.ignored_users = self.load_ignored_users()

    def load_ignored_users(self):
        try:
            with open(self.ignored_users_file, 'r') as file:
                return set(line.strip() for line in file)
        except FileNotFoundError:
            return set()

    def save_ignored_users(self):
        with open(self.ignored_users_file, 'w') as file:
            for user in self.ignored_users:
                file.write(f"{user}\n")

    def add_ignored_user(self, username):
        username = username.lstrip('@').lower()
        if username not in self.ignored_users:
            self.ignored_users.add(username)
            self.save_ignored_users()
            return f"Added {username} to the ignored users list."
        return f"{username} is already in the ignored users list."

    def remove_ignored_user(self, username):
        username = username.lstrip('@').lower()
        if username in self.ignored_users:
            self.ignored_users.remove(username)
            self.save_ignored_users()
            return f"Removed {username} from the ignored users list."
        return f"{username} is not in the ignored users list."

    def list_ignored_users(self):
        return list(self.ignored_users)
