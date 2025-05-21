# PollsterBot - A Reddit Polling Data Bot

PollsterBot is a Python-based Reddit bot that fetches and posts polling data from Huffington Post in response to user comments.

## Functionality

PollsterBot monitors specific subreddits for comments that mention its name ("Pollster_Bot") along with one or more U.S. state names or abbreviations. When triggered, it fetches the latest presidential polling data for the specified state(s) from the Huffington Post API and posts this information as a reply to the triggering comment.

-   **Trigger**: Keywords like "Pollster_Bot" followed by state names (e.g., "Pollster_Bot California Texas").
-   **Data Source**: Polling data is retrieved from [Huffington Post Pollster API](http://elections.huffingtonpost.com/pollster/api).
-   **Monitored Subreddits**: The bot can be configured to monitor a list of subreddits. This is defined in `data/subs.json`.

## Project Structure

```
.
├── PollsterBot.py        # Main bot logic and entry point.
├── Daemon.py             # Handles running the bot as a daemon process.
├── data/                 # Directory for JSON configuration files.
│   ├── huffingtonCharts.json # (Potentially, based on initial file scan - purpose to be verified)
│   ├── keywords.json       # Keywords that trigger the bot.
│   ├── login_credentials.json # Reddit API login credentials (IMPORTANT: Keep this secure).
│   ├── phrases.json        # Greetings and other bot phrases.
│   ├── states.json         # Mapping of state names to abbreviations.
│   └── subs.json           # List of subreddits to monitor.
├── PollsterBotLog.txt    # Log file for bot activities.
├── requirements.txt      # Python dependencies for the project.
└── README.md             # This file.
```

## Setup and Usage

1.  **Clone the repository:**
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd <repository_directory>
    ```

2.  **Install dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    python -m venv env # Or python3 -m venv env
    source env/bin/activate # On Windows: env\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Configure the bot:**
    *   Navigate to the `data/` directory.
    *   **Crucially, update `login_credentials.json`** with your Reddit bot's username and password. You'll need to register an application on Reddit to get API credentials if you don't have them.
        ```json
        {
            "user": "YOUR_BOT_USERNAME",
            "password": "YOUR_BOT_PASSWORD"
        }
        ```
    *   Modify `subs.json` to list the subreddits you want the bot to monitor.
    *   Review and update `keywords.json`, `phrases.json`, and `states.json` as needed.

4.  **Running the bot:**
    The bot uses `Daemon.py` to run as a background process.
    *   To start the bot:
        ```bash
        python PollsterBot.py start
        ```
    *   To stop the bot:
        ```bash
        python PollsterBot.py stop
        ```
    *   To restart the bot:
        ```bash
        python PollsterBot.py restart
        ```
    Logs will be written to `PollsterBotLog.txt`.

**Important Security Note:** Ensure that your `data/login_credentials.json` file is kept secure and is NOT committed to public repositories if you fork or clone this project for your own use. Consider adding `data/login_credentials.json` to your `.gitignore` file if it's not already there.

## Dependencies

The main dependencies for this project are:

*   **PRAW (Python Reddit API Wrapper)**: Used for interacting with the Reddit API.
*   **requests**: Used for making HTTP requests to the Huffington Post API.

These and other necessary packages are listed in `requirements.txt` and can be installed as described in the setup instructions.

## Contributing & Issues

If you encounter any bugs or have suggestions for improvement, please feel free to open an issue on the project's GitHub page (if applicable).

Contributions are welcome! If you'd like to contribute:
1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes.
4.  Submit a pull request with a clear description of your changes.
