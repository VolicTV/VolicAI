# VolicAI

An advanced AI-powered Twitch bot designed specifically for VolicTV's channel. VolicAI manages quotes, provides AI-driven interactions, tracks Valorant stats, and enhances overall chat engagement using TwitchIO and OpenAI's GPT-3.5.

## Features

- Quote management (add, retrieve, search, count)
- User data collection and analysis
- AI-powered responses and interactions
- Compatibility matching between users
- Valorant player statistics tracking
- Moderation tools (ignore/unignore users)

## Project Structure

```
twitch_bot/
│
├── bot.py                 # Main bot script
├── config.py              # Configuration file for API keys and settings
├── requirements.txt       # List of dependencies
│
├── api/                   # API-related functions
│   ├── __init__.py
│   ├── ai_manager.py      # AI response generation
│   ├── compatibility_manager.py # User compatibility matching
│   ├── quote_manager.py   # Quote management functions
│   ├── twitch_api.py      # Twitch API interactions
│   └── valorant_manager.py # Valorant stats tracking
│
├── commands/              # Bot commands
│   ├── __init__.py
│   ├── ai_commands.py     # AI-related commands
│   ├── compatibility_commands.py # Compatibility commands
│   ├── quote_commands.py  # Quote-related commands
│   ├── user_commands.py   # User-related commands
│   └── valorant_commands.py # Valorant-related commands
│
├── User/                  # User data management
│   └── user_data_manager.py
│
├── utils/                 # Utility functions
│   ├── __init__.py
│   └── logger.py          # Logging configuration
│
└── SingleScripts/         # Standalone scripts
    ├── fetch_all_quotes.py
    ├── migrate_quotes.py
    └── update_quotes_from_csv.py

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
