# VolicAI

VolicAI is a Twitch bot designed to enhance streaming experience with AI-powered interactions, Valorant stats tracking, and community engagement features. Built with TwitchIO and integrated with OpenAI's GPT models.

## Key Features

- 🤖 **AI-Powered Interactions**
  - Dynamic chat responses using GPT-3.5
  - Personalized roasts and compliments
  - AI-generated Valorant coaching tips
  - User compatibility analysis

- 🎮 **Valorant Integration**
  - Real-time stats tracking
  - Match history analysis
  - Rank display
  - Performance coaching
  - Custom pickup lines

- 📝 **Quote Management**
  - MongoDB-backed quote storage
  - Search functionality
  - Quote statistics
  - Author tracking

- 👥 **User Management**
  - Chat history tracking
  - User behavior analysis
  - Moderation tools
  - Ignored users management

## Prerequisites

- Python 3.8 or higher
- MongoDB
- Twitch Developer Account
- OpenAI API Key
- Riot Games API Key

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone https://github.com/VolicTV/VolicBot.git
   cd VolicBot
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   Create a `config.py` file:
   ```python
   # Twitch Configuration
   TWITCH_OAUTH_TOKEN = 'your_oauth_token'
   TWITCH_CLIENT_ID = 'your_client_id'
   TWITCH_CLIENT_SECRET = 'your_client_secret'
   TWITCH_CHANNEL = 'your_channel_name'
   
   # API Keys
   OPENAI_API_KEY = 'your_openai_api_key'
   RIOT_API_KEY = 'your_riot_api_key'
   
   # Database
   MONGO_URI = 'your_mongodb_connection_string'
   ```

3. **Database Setup**
   - Install and start MongoDB
   - The bot will automatically create required collections
   - Initial quote migration: `python SingleScripts/migrate_quotes.py`

4. **Launch**
   ```bash
   python bot.py
   ```

## Available Commands

### Quote Management
- `!quote` - Get a random quote
- `!quotesearch <term>` - Search quotes
- `!quotecount` - Show quote statistics
- `!lastquote` - Display most recent quote

### AI Interactions
- `!airesponse <prompt>` - Get AI response
- `!roast <username>` - Generate playful roast
- `!compliment <username>` - Generate compliment
- `!rizz <username>` - Generate pickup line
- `!compatibility <user1> <user2>` - Check user compatibility

### Valorant Features
- `!setriotid <riot_id>` - Set Riot ID
- `!valorantstats` - View overall stats
- `!valomatch` - Last match details
- `!valomatches` - Match history
- `!valocoach` - Get coaching tips
- `!rank` - Display current rank

### Moderation
- `!ignore <username>` - Add user to ignore list
- `!unignore <username>` - Remove from ignore list
- `!ignorelist` - View ignored users

### General
- `!about` - Bot information
- `!commands` - List all commands

## Development

### Project Structure

```
VolicAI/
├── api/ # API integrations
├── commands/ # Command implementations
├── utils/ # Utility functions
├── User/ # User management
├── SingleScripts/ # Standalone scripts
├── bot.py # Main bot logic
├── config.py # Configuration
└── requirements.txt # Dependencies

```

## Component Explanations

1. **bot.py**: The main script that runs the bot. It handles the connection to Twitch and manages command processing.
2. **config.py**: Stores API keys, channel name, and other configuration settings. Keeps sensitive information separate from the main code.
3. **requirements.txt**: Lists all Python packages the project depends on.
4. **api/quote_manager.py**: Contains the QuoteManager class for managing quotes, including loading, saving, and retrieving quotes.
5. **fetch_all_quotes.py**: A separate script to fetch all quotes from Stream Elements and save them to a CSV file.

### Logging
- All bot actions are logged in `logs/bot.log`
- Command usage is tracked in `logs/commands.log`
- API interactions are logged in `logs/api.log`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Troubleshooting

Common issues and solutions:
- **MongoDB Connection**: Ensure MongoDB is running and URI is correct
- **API Rate Limits**: Check Twitch/Riot API quota usage
- **Missing Quotes**: Run `python SingleScripts/fetch_all_quotes.py`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- GitHub Issues: Bug reports and feature requests
- Discord: Join our community for support
- Email: Contact VolicTV directly

## Acknowledgments

- TwitchIO team
- OpenAI
- Riot Games API
- MongoDB team
