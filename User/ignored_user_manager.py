import json
from utils.logger import command_logger

class IgnoredUserManager:
    def __init__(self, ignored_users_file):
        """Initialize with path to ignored users JSON file"""
        self.ignored_users_file = ignored_users_file
        self.ignored_users = self.load_ignored_users()

    def load_ignored_users(self):
        """Load ignored users from JSON file"""
        try:
            with open(self.ignored_users_file, 'r') as file:
                data = json.load(file)
                return set(data)
        except FileNotFoundError:
            # Create file if it doesn't exist
            self.save_ignored_users(set())
            return set()
        except json.JSONDecodeError:
            command_logger.error(f"Error decoding {self.ignored_users_file}. Starting with empty set.")
            return set()

    def save_ignored_users(self, users=None):
        """Save ignored users to JSON file"""
        if users is None:
            users = self.ignored_users
        try:
            with open(self.ignored_users_file, 'w') as file:
                json.dump(list(users), file, indent=2)
        except Exception as e:
            command_logger.error(f"Error saving ignored users: {str(e)}")

    def add_ignored_user(self, username):
        """Add user to ignored list"""
        username = username.lstrip('@').lower()
        if username not in self.ignored_users:
            self.ignored_users.add(username)
            self.save_ignored_users()
            return f"Added {username} to the ignored users list."
        return f"{username} is already in the ignored users list."

    def remove_ignored_user(self, username):
        """Remove user from ignored list"""
        username = username.lstrip('@').lower()
        if username in self.ignored_users:
            self.ignored_users.remove(username)
            self.save_ignored_users()
            return f"Removed {username} from the ignored users list."
        return f"{username} is not in the ignored users list."

    def list_ignored_users(self):
        """Get list of all ignored users"""
        return list(self.ignored_users)

    def is_ignored(self, username):
        """Check if a user is ignored"""
        return username.lstrip('@').lower() in self.ignored_users
