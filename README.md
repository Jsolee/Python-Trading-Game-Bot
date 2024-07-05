# Trading Bot

Welcome to the Trading Bot project! This bot is designed to simulate a stock trading environment where you can buy, sell, and manage a portfolio of stocks. It's built with Python and integrates with the Telegram API for an interactive trading experience.

## Features

- **Buy Stocks**: Purchase stocks to add to your portfolio.
- **Sell Stocks**: Sell stocks from your portfolio.
- **View Portfolio**: Check the current status of your portfolio, including stock holdings and available balance.
- **Check Stock Prices**: Get real-time prices of stocks.
- **Surrender**: Reset your portfolio and start over.

## Getting Started

To get started with the Trading Bot, you need to have Python installed on your system. Additionally, you'll need to install several dependencies, including `python-telegram-bot`, `requests`, and `pandas` for data handling and visualization.

### Prerequisites

- Python 3.6 or higher
- pip for installing Python packages

### Installation

1. Clone the repository to your local machine:
```bash
git clone https://github.com/yourusername/trading-bot.git
```

2. Navigate to the cloned directory:
```bash
cd trading-bot
```

3. Install the required Python packages:
```bash
pip install -r requirements.txt
```

4. Create a .env file in the root directory and add your Telegram Bot Token and Alpha Vantage API Key:

```
TELEGRAM_TOKEN=your_telegram_bot_token
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
```

### Usage

To run the bot, execute the following command in the terminal:
```bash
python trading_bot.py
```

Once the bot is running, you can interact with it by sending commands through a Telegram chat.

### Commands

- `/start` - Initialize the bot and display the welcome message.
- `/buy SYMBOL AMOUNT` - Buy a specific amount of stock.
- `/sell SYMBOL AMOUNT` - Sell a specific amount of stock.
- `/portfolio` - View your current portfolio.
- `/price SYMBOL` - Check the current price of a stock.
- `/surrender` - Reset your portfolio and balance.

## Contributing

Contributions are welcome! If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

## License

Distributed under the MIT License. See LICENSE for more information.