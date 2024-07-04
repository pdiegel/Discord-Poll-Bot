# Discord Poll Bot

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Commands](#commands)
- [Contributing](#contributing)
- [License](#license)

## Introduction

The Discord Poll Bot is designed to address the limitations of built-in Discord polls, which restrict the poll duration to a maximum of one week and limit the number of options to ten. This bot allows you to create polls with an indefinite duration and without a limit on the number of options, providing greater flexibility and utility for your Discord server.

## Features

- Create polls with an indefinite duration
- No limit on the number of options
- Vote casting through button interactions
- Anonymous voting
- Real-time vote counting
- Admins can delete polls using the poll ID

## Installation

### Prerequisites

- [Python](https://www.python.org/) (v3.7 or higher)
- Required Python packages listed in `requirements.txt`

### Steps

1. Clone the repository:

    ```sh
    git clone https://github.com/pdiegel/Discord-Poll-Bot.git
    ```

2. Navigate to the project directory:

    ```sh
    cd Discord-Poll-Bot
    ```

3. Install the required Python packages:

    ```sh
    pip install -r requirements.txt
    ```

## Configuration

1. Create a `.env` file in the root directory of the project.
2. Add your Discord bot token to the `.env` file:

    ```env
    BOT_TOKEN=your_discord_bot_token
    ```

## Usage

1. Ensure you have a `.env` file in the root directory with the following content:

    ```env
    BOT_TOKEN=your_discord_bot_token
    ```

2. Start the bot:

    ```sh
    python bot.py
    ```

3. Invite the bot to your Discord server.
4. Use the bot commands to create and manage polls.

## Commands

### /createpoll

This command creates a poll using a question string and an options string. The options string should be a comma-delimited set of poll options. If there are less than 2 options, the bot will raise a warning.

#### Example

```sh
/createpoll "What's your favorite color?" "Red,Blue,Green"
```

### /deletepoll

This command deletes a poll using the Poll ID. If the poll ID is found, it will create a modal for deletion confirmation and then delete the poll.

#### Example

```sh
/deletepoll 12345
```

Each Poll ID is shown at the end of each poll message from the bot.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add some feature'`).
5. Push to the branch (`git push origin feature/your-feature`).
6. Open a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
