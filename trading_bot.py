import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
import requests
import os
from dotenv import load_dotenv
from pytz import timezone
from typing import Optional

load_dotenv()  # Load environment variables from .env file

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN_TRADINGBOT')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Initialize portfolios and balances
portfolios = {}
balances = {}
STARTING_BALANCE = 10000.0  # Starting amount for each user

# Define states
BUY, SELL, ASK_AMOUNT, PRICE = range(4)

def display_buttons(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("🛒 Buy Stocks", callback_data='buy'), InlineKeyboardButton("💰 Sell Stocks", callback_data='sell')],
        [InlineKeyboardButton("📈 View Portfolio", callback_data='portfolio'), InlineKeyboardButton("🔍 Check Price", callback_data='price')],
        [InlineKeyboardButton("🏳️ Surrender", callback_data='surrender')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)

def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user.username
    if user not in balances:
        balances[user] = STARTING_BALANCE
        portfolios[user] = {}
    message = (
        "🎉 *Welcome to the Trading Game!* 🎉\n\n"
        "Use the following commands to play:\n"
        "/buy `SYMBOL AMOUNT` - Buy stocks\n"
        "/sell `SYMBOL AMOUNT` - Sell stocks\n"
        "/portfolio - View your portfolio\n"
        "/price `SYMBOL` - Get the price of a stock\n"
        "/surrender - Reset your portfolio\n\n"
        "💼 Start trading and grow your wealth! 💰"
    )
    update.message.reply_text(message, parse_mode='Markdown')
    display_buttons(update, context)

def surrender(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user.username
    if user in balances:
        balances[user] = STARTING_BALANCE
        portfolios[user] = {}
        update.message.reply_text('You have surrendered. Your portfolio is now empty, and your balance has been reset. 😞')
    else:
        update.message.reply_text('You do not have a portfolio to surrender.')
    display_buttons(update, context)

def get_stock_price(symbol: str) -> Optional[float]:
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=1min&apikey={ALPHA_VANTAGE_API_KEY}'
    response = requests.get(url)
    data = response.json()
    try:
        last_refresh = data['Meta Data']['3. Last Refreshed']
        last_close = data['Time Series (1min)'][last_refresh]['4. close']
        return float(last_close)
    except KeyError:
        return None

def get_stock_data(symbol: str) -> Optional[pd.DataFrame]:
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=1min&apikey={ALPHA_VANTAGE_API_KEY}'
    response = requests.get(url)
    data = response.json()
    try:
        times = []
        prices = []
        for time, info in data['Time Series (1min)'].items():
            times.append(datetime.strptime(time, '%Y-%m-%d %H:%M:%S'))
            prices.append(float(info['4. close']))
        df = pd.DataFrame({'Time': times, 'Price': prices})
        df.sort_values('Time', inplace=True)
        return df
    except KeyError:
        return None

def plot_stock_chart(symbol: str, df: pd.DataFrame) -> str:
    plt.style.use('ggplot')
    
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot the price data
    ax.plot(df['Time'], df['Price'], label=symbol, color='tab:blue', linewidth=2)
    
    # Customize the grid and background
    ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
    ax.set_facecolor('#f7f7f9')
    
    # Format the date axis to show in Spain time zone
    spain_tz = timezone('Europe/Madrid')
    df['Time'] = df['Time'].dt.tz_localize('UTC').dt.tz_convert(spain_tz)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=spain_tz))
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
    fig.autofmt_xdate()
    
    # Add labels and title
    ax.set_xlabel('Time (Spain)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Price (USD)', fontsize=14, fontweight='bold')
    ax.set_title(f'{symbol} Price Chart', fontsize=16, fontweight='bold')

    # Add a legend
    ax.legend(fontsize=12)

    # Customize the tick parameters
    ax.tick_params(axis='x', rotation=45)
    ax.tick_params(axis='both', which='major', labelsize=12)

    # Save the plot
    file_path = f'{symbol}_chart.png'
    plt.savefig(file_path, bbox_inches='tight')
    plt.close(fig)
    
    return file_path

def price(update: Update, context: CallbackContext) -> None:
    args = context.args if context.args else []
    symbol = args[0] if args else context.user_data.get('symbol')
    if not symbol:
        update.message.reply_text('Usage: /price SYMBOL')
        display_buttons(update, context)
        return
    price = get_stock_price(symbol)
    if price is None:
        update.message.reply_text('Invalid stock symbol. ❌')
        display_buttons(update, context)
        return
    df = get_stock_data(symbol)
    if df is not None:
        file_path = plot_stock_chart(symbol, df)
        caption = f'The current price of {symbol} is ${price:.2f}.'
        update.message.reply_photo(photo=open(file_path, 'rb'), caption=caption)
        os.remove(file_path)
    else:
        update.message.reply_text(f'The current price of {symbol} is ${price:.2f}.')
    display_buttons(update, context)  # Display buttons again

def buy(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user.username
    symbol = context.user_data['symbol']
    amount = context.user_data['amount']
    amount = int(amount)
    price = get_stock_price(symbol)
    if price is None:
        update.message.reply_text('Invalid stock symbol. ❌')
        display_buttons(update, context)
        return
    total_cost = price * amount
    if balances[user] < total_cost:
        update.message.reply_text('Insufficient balance to complete the purchase. 💸')
        display_buttons(update, context)
        return
    balances[user] -= total_cost
    if symbol in portfolios[user]:
        portfolios[user][symbol] += amount
    else:
        portfolios[user][symbol] = amount
    update.message.reply_text(f'✅ Bought {amount} of {symbol} at ${price:.2f} each. 🛒 New balance: ${balances[user]:.2f}.')
    display_buttons(update, context)

def sell(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user.username
    symbol = context.user_data['symbol']
    amount = context.user_data['amount']
    amount = int(amount)
    if symbol not in portfolios[user] or portfolios[user][symbol] < amount:
        update.message.reply_text('You do not have enough stock to sell. 💸')
        display_buttons(update, context)
        return
    price = get_stock_price(symbol)
    if price is None:
        update.message.reply_text('Invalid stock symbol. ❌')
        display_buttons(update, context)
        return
    total_income = price * amount
    portfolios[user][symbol] -= amount
    if portfolios[user][symbol] == 0:
        del portfolios[user][symbol]
    balances[user] += total_income
    update.message.reply_text(f'✅ Sold {amount} of {symbol} at ${price:.2f} each. New balance: ${balances[user]:.2f}.')
    display_buttons(update, context)

def portfolio(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user.username
    if user not in portfolios or not portfolios[user]:
        update.message.reply_text('Your portfolio is empty. 💸')
        display_buttons(update, context)
        return
    message = '📈 *Your Portfolio:* 📈\n\n'
    total_value = balances[user]
    for symbol, amount in portfolios[user].items():
        price = get_stock_price(symbol)
        if price is not None:
            value = price * amount
            message += f'{symbol}: {amount} shares at ${price:.2f} each. Total value: ${value:.2f}\n'
            total_value += value
    message += f'\n💼 *Total Portfolio Value: ${total_value:.2f}*\n💰 *Available Balance: ${balances[user]:.2f}*'
    update.message.reply_text(message, parse_mode='Markdown')
    display_buttons(update, context)

def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    command = query.data

    if command == 'buy':
        query.edit_message_text(text="Enter the symbol for buying:")
        context.user_data['command'] = 'buy'
        return BUY
    elif command == 'sell':
        query.edit_message_text(text="Enter the symbol for selling:")
        context.user_data['command'] = 'sell'
        return SELL
    elif command == 'portfolio':
        query.edit_message_text(text="Your Portfolio:")
        portfolio(update, context)
        return ConversationHandler.END
    elif command == 'price':
        query.edit_message_text(text="Enter the stock symbol to check price:")
        context.user_data['command'] = 'price'
        return PRICE
    elif command == 'surrender':
        surrender(update, context)
        return ConversationHandler.END

def ask_for_symbol(update: Update, context: CallbackContext) -> int:
    user_text = update.message.text
    command = context.user_data['command']

    context.user_data['symbol'] = user_text

    if command == 'price':
        price(update, context)
        return ConversationHandler.END

    update.message.reply_text("Enter the amount:")
    return ASK_AMOUNT

def process_buy_sell(update: Update, context: CallbackContext) -> int:
    amount = update.message.text
    command = context.user_data['command']

    context.user_data['amount'] = amount

    if command == 'buy':
        buy(update, context)
    elif command == 'sell':
        sell(update, context)

    return ConversationHandler.END

def main() -> None:
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('surrender', surrender),
            CallbackQueryHandler(button),
        ],
        states={
            BUY: [MessageHandler(Filters.text & ~Filters.command, ask_for_symbol)],
            SELL: [MessageHandler(Filters.text & ~Filters.command, ask_for_symbol)],
            ASK_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, process_buy_sell)],
            PRICE: [MessageHandler(Filters.text & ~Filters.command, ask_for_symbol)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('price', price))
    dispatcher.add_handler(CommandHandler('portfolio', portfolio))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
