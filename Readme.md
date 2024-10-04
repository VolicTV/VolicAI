
## Component Explanations

1. **bot.py**: The main script that runs the bot. It handles the connection to Twitch and manages command processing.
2. **config.py**: Stores API keys, channel name, and other configuration settings. Keeps sensitive information separate from the main code.
3. **requirements.txt**: Lists all Python packages the project depends on.
4. **api/**: Contains scripts for interacting with different APIs (Twitch, Stream Elements, Google Sheets).
5. **commands/**: Contains scripts for the bot's commands, separated into basic and advanced commands.
6. **utils/**: Contains utility functions, such as logging, used throughout the project.

## Setup Instructions

1. **Set Up Your Environment**
   - Ensure Python is installed on your machine.
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
   - Copy `config.py.example` to `config.py` (if provided).
   - Edit `config.py` with your Twitch API credentials, bot token, and other necessary settings.

4. **Running the Bot**
   - Execute the main script:
     ```
     python bot.py
     ```

## Adding Commands

To add new commands:
1. Create a new function in either `basic_commands.py` or `advanced_commands.py`.
2. Register the command in `bot.py`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.