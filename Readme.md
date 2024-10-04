# Twitch Quote Bot

A Twitch bot for managing and retrieving quotes using TwitchIO.

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
│ ├── quote_manager.py # Quote management functions
│ └── stream_elements.py # Stream Elements API interaction (if needed)
│
└── fetch_all_quotes.py # Script to fetch all quotes from Stream Elements

```

## Component Explanations

1. **bot.py**: The main script that runs the bot. It handles the connection to Twitch and manages command processing.
2. **config.py**: Stores API keys, channel name, and other configuration settings. Keeps sensitive information separate from the main code.
3. **requirements.txt**: Lists all Python packages the project depends on.
4. **api/quote_manager.py**: Contains the QuoteManager class for managing quotes, including loading, saving, and retrieving quotes.
5. **fetch_all_quotes.py**: A separate script to fetch all quotes from Stream Elements and save them to a CSV file.

## Setup Instructions

1. **Set Up Your Environment**
   - Ensure Python 3.7 or higher is installed on your machine.
   - Create a virtual environment for the project:
     ```
     python -m venv venv
     source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
     ```

2. **Install Dependencies**
   - Install required packages:
     ```
     pip install -r requirements.txt
     ```

3. **Configuration**
   - Create a `config.py` file with your Twitch API credentials, bot token, and channel name.

4. **Fetching Quotes**
   - Run the fetch_all_quotes.py script to populate your initial quotes database:
     ```
     python fetch_all_quotes.py
     ```

5. **Running the Bot**
   - Execute the main script:
     ```
     python bot.py
     ```

## Available Commands

- `!quote`: Retrieves a random quote.
- `!quoteid <id>`: Retrieves a specific quote by its ID.
- `!quotesearch <term>`: Searches for quotes containing the specified term.

## Adding New Commands

To add new commands, modify the `Bot` class in `bot.py`. Use the `@commands.command()` decorator to define new command methods.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.