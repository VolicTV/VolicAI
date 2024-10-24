# VolicAI

VolicAI is a Twitch bot designed to enhance your streaming experience with a variety of interactive features. This bot is built using the TwitchIO library and integrates with several APIs to provide a rich set of functionalities.

## Features

- **Quote Management**: Add, remove, and display quotes from your Twitch chat.
- **User Data Management**: Collect and manage user data, including chat history and user summaries.
- **AI-Powered Responses**: Generate witty responses to chat messages using AI.
- **Compatibility Analysis**: Analyze user compatibility based on chat interactions.
- **Valorant Integration**: Fetch and display Valorant game data.
- **Custom Commands**: Easily add and manage custom commands for your chat.

## Project Structure

```
twitch_bot/
│
├── bot.py # Main bot script
├── config.py # Configuration file for API keys and settings
├── requirements.txt # List of dependencies
│
├── api/ # Directory for API-related functions
│ ├── init.py
│ ├── twitch_api.py # Functions to interact with the Twitch API
│ ├── stream_elements.py # Functions to interact with the Stream Elements API
│ ├── google_sheets.py # Functions to interact with the Google Sheets API
│ ├── ai_manager.py # AI-related functions and interactions
│ ├── compatibility_manager.py # Manage user compatibility features
│ └── valorant_manager.py # Manage Valorant-related features
│
├── commands/ # Directory for bot commands
│ ├── init.py
│ ├── ai_commands.py # Commands related to AI interactions
│ ├── compatibility_commands.py # Commands for user compatibility
│ ├── user_commands.py # User management commands
│ ├── valorant_commands.py # Commands for Valorant stats and interactions
│ └── quote_commands.py # Commands for managing quotes
│
├── utils/ # Utility functions
│ ├── init.py
│ ├── logger.py # Logging functions for debugging
│ └── ignored_user_manager.py # Manage ignored users
│
└── User/ # User data management
├── init.py
└── user_data_manager.py # Manage user data and interactions
```

## Component Explanations

1. **bot.py**: The main script that runs the bot. It handles the connection to Twitch and manages command processing.
2. **config.py**: Stores API keys, channel name, and other configuration settings. Keeps sensitive information separate from the main code.
3. **requirements.txt**: Lists all Python packages the project depends on.
4. **api/quote_manager.py**: Contains the QuoteManager class for managing quotes, including loading, saving, and retrieving quotes.
5. **fetch_all_quotes.py**: A separate script to fetch all quotes from Stream Elements and save them to a CSV file.

## Setup Instructions

1. **Clone the Repository**
   ```
   git clone https://github.com/your-username/twitch-quote-bot.git
   cd twitch-quote-bot
   ```

2. **Set Up Your Environment**
   - Ensure Python 3.7 or higher is installed.
   - Create and activate a virtual environment:
     ```
     python -m venv venv
     source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
     ```

3. **Install Dependencies**
   ```
   pip install -r requirements.txt
   ```

4. **Configuration**
   - Create a `config.py` file with your API credentials and settings:
     ```python
     TWITCH_OAUTH_TOKEN = 'your_oauth_token'
     TWITCH_CLIENT_ID = 'your_client_id'
     TWITCH_CLIENT_SECRET = 'your_client_secret'
     TWITCH_CHANNEL = 'your_channel_name'
     OPENAI_API_KEY = 'your_openai_api_key'
     MONGO_URI = 'your_mongodb_connection_string'
     ```

5. **Database Setup**
   - Ensure MongoDB is installed and running.
   - The bot will automatically create necessary collections.

6. **Running the Bot**
   ```
   python bot.py
   ```

## Usage

- **Quotes**: `!quote`, `!quotesearch <term>`, `!quotecount`, `!lastquote`
- **AI Interactions**: `!airesponse <prompt>`, `!roast <username>`
- **User Compatibility**: `!compatibility <user1> <user2>`
- **Valorant Stats**: `!setriotid <riot_id>`, `!valorantstats`
- **Moderation**: `!ignore <username>`, `!unignore <username>`, `!ignorelist`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For any questions or support, please contact VolicTV.
