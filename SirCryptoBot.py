import ccxt
import time
import os
import psutil
import json
import requests
import sys
from datetime import datetime
import shutil
import re


# Configure KuCoin API
exchange = ccxt.kucoin({
    'apiKey': 'XXXXXXX',
    'secret': 'XXXXXXX',
    'password': 'XXXXXXX',
})


#['BTC/USDT', 'ETH/USDT', 'LINK/USDT', 'TON/USDT', 'XLM/USDT', 'DOT/USDT', 'UNI/USDT', 'ICP/USDT', 'APT/USDT', 'AAVE/USDT', 'POL/USDT', 'VIRTUAL/USDT', 'ARB/USDT', 'FIL/USDT', 'ATOM/USDT', 'OP/USDT', 'TIA/USDT', 'IMX/USDT', 'INJ/USDT', 'GRT/USDT', 'WLD/USDT', 'JASMY/USDT', 'RUNE/USDT', 'RAY/USDT', 'BRETT/USDT', 'FLR/USDT', 'QNT/USDT', 'KCS/USDT', 'CRV/USDT', 'ENS/USDT', 'AR/USDT', 'AIOZ/USDT', 'AERO/USDT']

exchange.options['defaultType'] = 'spot'

# Global variables
cryptos = ['BTC/USDT', 'ETH/USDT', 'LINK/USDT', 'TON/USDT', 'XLM/USDT', 'DOT/USDT', 'UNI/USDT', 'ICP/USDT', 'APT/USDT', 'AAVE/USDT', 'POL/USDT', 'VIRTUAL/USDT', 'ARB/USDT', 'FIL/USDT', 'ATOM/USDT', 'OP/USDT', 'TIA/USDT', 'IMX/USDT', 'INJ/USDT', 'GRT/USDT', 'WLD/USDT', 'JASMY/USDT', 'RUNE/USDT', 'RAY/USDT', 'FLR/USDT', 'QNT/USDT', 'KCS/USDT', 'CRV/USDT', 'ENS/USDT', 'AR/USDT', 'SOL/USDT']
initial_capital = 45 #Change this
base_investment_percentage = 0.2 #You can change this
take_profit = 1.025
buy_on_drop = 0.95
minimum_investment_percentage = 0.01
minimum_investment = 0.1
margin_tolerance = 0.001  
fear_and_greed_index = None
funds_secured = True

state_file = "bot_state.json"
stop_file = "stop.txt"
reserved_funds_file = "reserved_funds.json"
backup_folder = "E:\\data"
global_log_file = "global_log.txt"

last_update_time = time.time()
update_interval = 24 * 60 * 60

def write_global_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(global_log_file, "a") as file:
        file.write(f"[{timestamp}] {message}\n")
    print(f"[GLOBAL] {message}")

def load_total_removed(state_file):
    try:
        with open(state_file, 'r') as file:
            data = json.load(file)
            return data.get('total_removed', 0)
    except (FileNotFoundError, json.JSONDecodeError):
        write_global_log("Error loading total_removed from state file. Setting to 0.")
        return 0

total_removed = load_total_removed(state_file)

def save_state(state):
    with open(state_file, "w") as file:
        json.dump(state, file, indent=4)
    print("State saved.")
    
def backup_state_file():
    if not os.path.exists(state_file):
        print("Error: The file bot_state.json does not exist.")
        return

    if not os.path.exists(backup_folder):
        print(f"The folder {backup_folder} doesn't exist. Initializing...")
        os.makedirs(backup_folder) 

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_folder, f"bot_state_backup_{timestamp}.json")

    try:
        shutil.copy2(state_file, backup_file)
        print(f"Backup created successfully: {backup_file}")
    except Exception as e:
        print(f"Error during backup: {e}")

def load_state():
    if os.path.exists(state_file):
        with open(state_file, "r") as file:
            return json.load(file)
    return {
        symbol: {
            'capital': initial_capital,
            'last_order_price': None,
            'unsold_orders': [],
            'paused': False,
            'current_investment_percentage': base_investment_percentage,
            'order_count': 0,
            'rincaro_count': 0
        } for symbol in cryptos
    }

def handle_critical_error(error_message):
    """Handles critical errors, saves the state, and restarts the bot after 10 minutes."""
    write_global_log(f"Critical error: {error_message}")
    save_state(crypto_states)
    write_global_log("Restarting bot in 10 minutes...")
    time.sleep(600)
    os.execl(sys.executable, sys.executable, *sys.argv)  # Restart the current process
       
def fetch_fear_and_greed_index():
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data and 'data' in data and len(data['data']) > 0:
            return int(data['data'][0]['value'])
        else:
            raise ValueError("Index data not available.")
    except requests.exceptions.RequestException as e:
        print(f"HTTP request error: {e}")
        return None
    except ValueError as e:
        print(f"Data error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
        
def calculate_buy_on_drop(fear_and_greed_index):
    if fear_and_greed_index is None:
        write_global_log("Warning: Fear and Greed Index is None. Using default buy_on_drop value.")
        return 0.95 
    
    min_index = 1
    max_index = 100
    min_buy_on_drop = 0.88
    max_buy_on_drop = 0.99
    return (min_buy_on_drop + (max_buy_on_drop - min_buy_on_drop) * ((fear_and_greed_index - min_index) / (max_index - min_index)))
    
def update_buy_on_drop():
    global buy_on_drop, fear_and_greed_index, take_profit 
    
    index = fetch_fear_and_greed_index()
    if index is not None:
        fear_and_greed_index = index  
        buy_on_drop = calculate_buy_on_drop(index)  
        take_profit = buy_on_drop + 0.085
        if take_profit < 1.01:
            take_profit = 1.01
        print(f"Index: {index}, new buy_on_drop: {buy_on_drop:.2f}, new take_profit: {take_profit:.2f}")
    else:
        print("Error retrieving the index.")
        buy_on_drop = 0.95
        take_profit = 1.025

def fetch_minimum_order_sizes():
    try:
        url = "https://api.kucoin.com/api/v1/symbols"
        response = requests.get(url, timeout=10) 
        response.raise_for_status()
        data = response.json()
        min_sizes = {}
        for pair in data['data']:
            symbol = f"{pair['baseCurrency']}/{pair['quoteCurrency']}"
            min_sizes[symbol] = {
                'baseMinSize': float(pair['baseMinSize']),
                'quoteMinSize': float(pair['quoteMinSize'])
            }
        return min_sizes
    except requests.exceptions.RequestException as e:
        write_global_log(f"Error fetching minimum order sizes: {e}")
        handle_critical_error(f"Error fetching minimum order sizes: {e}")
        return {}

minimum_order_sizes = fetch_minimum_order_sizes()
crypto_states = load_state()

def write_log(symbol, message):
    log_file = f"{symbol.replace('/', '_')}_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as file:
        file.write(f"[{timestamp}] {message}\n")
    print(f"[{symbol}] {message}")

def set_process_priority():
    try:
        process = psutil.Process(os.getpid())
        process.nice(psutil.HIGH_PRIORITY_CLASS)
        write_global_log("Priority set to High.")
    except Exception as e:
        write_global_log(f"Error in setting the priority of the job: {e}")

def place_order(symbol, side, amount, price=None):
    try:
        if side == 'buy':
            adjusted_price = price * (1 + margin_tolerance) if price else None
            order = exchange.create_limit_buy_order(symbol, amount, adjusted_price)
            write_log(symbol, f"PURCHASE placed: {amount:.6f} {symbol.split('/')[0]} at {adjusted_price:.6f} USDT.")
            return order
        elif side == 'sell':
            adjusted_price = price * (1 - margin_tolerance) if price else None
            order = exchange.create_limit_sell_order(symbol, amount, adjusted_price)
            write_log(symbol, f"SALE placed: {amount:.6f} {symbol.split('/')[0]} at {adjusted_price:.6f} USDT.")
            return order
    except Exception as e:
        write_log(symbol, f"Error placing the order: {e}")
        return None

def secure_funds(state_file):
    with open(state_file, 'r') as file:
        data = json.load(file)

    total_removed = 0

    for crypto, values in data.items():
        if isinstance(values, dict) and 'capital' in values:
            values['capital'] -= 0.01
            total_removed += 0.01

    if 'total_removed' in data:
        data['total_removed'] += total_removed
    else:
        data['total_removed'] = total_removed

    with open(state_file, 'w') as file:
        json.dump(data, file, indent=4)

    print(f"Capital updated and {total_removed} removed. Total removed so far: {data['total_removed']}")

last_logged_message = {}

def trading_logic(symbol):
    min_sizes = fetch_minimum_order_sizes()
    state = crypto_states[symbol]

    state['rincaro_level'] = state.get('rincaro_level', 0)

    if state['paused']:
        return

    capital = state['capital']
    current_percentage = state['current_investment_percentage']

    try:
        ticker = exchange.fetch_ticker(symbol, {'timeout': 10})
        current_price = ticker['last']

        min_size = min_sizes.get(symbol)
        if not min_size:
            write_log(symbol, "Minimum values not available for this pair.")
            return

        base_min_size = min_size['baseMinSize']
        quote_min_size = min_size['quoteMinSize']

        if not state['unsold_orders']:
            order_size = (capital * current_percentage) / current_price
            if order_size < base_min_size or (order_size * current_price) < quote_min_size:
                log_message = "Insufficient funds for a new purchase."
                if last_logged_message.get(symbol) != log_message:
                    write_log(symbol, log_message)
                    last_logged_message[symbol] = log_message
                return

            cost = order_size * current_price
            state['capital'] -= cost
            state['order_count'] += 1
            order = place_order(symbol, 'buy', order_size, current_price)
            if order:
                state['unsold_orders'].append({'price': current_price, 'amount': order_size, 'id': order['id'], 'is_rincaro': False})
                write_log(symbol, f"Purchase Order {state['order_count']}: {order_size:.6f} at {current_price:.6f} USDT.")
                print(f"[{symbol}] Remaining capital after purchase: {state['capital']:.6f} USDT.")
                write_log(symbol, f"Remaining capital after purchase: {state['capital']:.6f} USDT.")
                last_logged_message[symbol] = None
            else:
                if exchange.last_error and '200004' in exchange.last_error:
                    write_log(symbol, "Insufficient balance error: Canceling your last purchase.")
                    state['capital'] += cost
                    state['order_count'] -= 1 
                    if state['unsold_orders']:
                        state['unsold_orders'].pop() 
                    last_logged_message[symbol] = None

        for order in state['unsold_orders'][:]:
            if current_price >= order['price'] * take_profit:
                revenue = order['amount'] * current_price
                state['capital'] += revenue
                place_order(symbol, 'sell', order['amount'], current_price)
                state['unsold_orders'].remove(order)

                if not order.get('is_rincaro', False):
                    state['sales_streak'] = state.get('sales_streak', 0) + 1
                    if state['sales_streak'] > 20:
                        state['sales_streak'] = 20
                    state['current_investment_percentage'] = min(
                        base_investment_percentage + 0.005 * state['sales_streak'], 0.2
                    )
                else:
                    state['sales_streak'] = 0 
                    state['rincaro_level'] = max(state['rincaro_level'] - 1, 0)

                write_log(symbol, f"Sale Order {state['order_count']}: Profit {revenue:.6f} USDT.")
                print(f"[{symbol}] Remaining capital after sale: {state['capital']:.6f} USDT. " + str(take_profit) + " -BoD updated," + str(fear_and_greed_index) + "-FaG index")
                write_log(symbol, f"Remaining capital after sale: {state['capital']:.6f} USDT.")
                last_logged_message[symbol] = None  

        if state['unsold_orders']:
            last_order = state['unsold_orders'][-1]
            if current_price <= last_order['price'] * buy_on_drop:
                state['rincaro_level'] = state.get('rincaro_level', 0) + 1
                current_percentage = max(
                    minimum_investment_percentage,
                    base_investment_percentage - 0.005 * state['rincaro_level']
                )
                order_size = (capital * current_percentage) / current_price
                if order_size < base_min_size or (order_size * current_price) < quote_min_size:
                    log_message = "Insufficient funds for a new order."
                    if last_logged_message.get(symbol) != log_message:
                        write_log(symbol, log_message)
                        last_logged_message[symbol] = log_message
                    return

                cost = order_size * current_price
                state['capital'] -= cost
                new_order = place_order(symbol, 'buy', order_size, current_price)
                if new_order:
                    state['unsold_orders'].append({'price': current_price, 'amount': order_size, 'id': new_order['id'], 'is_rincaro': True})
                    state['sales_streak'] = 0  
                    state['current_investment_percentage'] = base_investment_percentage 
                    write_log(symbol, f"Order price increase {state['order_count']} N. {state['rincaro_level']}: {order_size:.6f} at {current_price:.6f} USDT.")
                    print(f"[{symbol}] Remaining capital after the increase: {state['capital']:.6f} USDT. " + str(buy_on_drop) + " -BoD updated," + str(fear_and_greed_index) + "-FaG index")
                    write_log(symbol, f"Remaining capital after the increase: {state['capital']:.6f} USDT.")
                    last_logged_message[symbol] = None  
                else:
                    if exchange.last_error and '200004' in exchange.last_error:
                        write_log(symbol, "Insufficient balance error: Cancellation of the last new purchase order.")
                        state['capital'] += cost  
                        state['rincaro_level'] = max(state['rincaro_level'] - 1, 0) 
                        if state['unsold_orders']:
                            state['unsold_orders'].pop() 
                        last_logged_message[symbol] = None  

    except Exception as e:
        write_log(symbol, f"Error: {e}")



def report_profit_or_loss():
    total_capital = 0
    for state in crypto_states.values():
        if isinstance(state, dict) and 'capital' in state:
            total_capital += state['capital']
        else:
            write_global_log(f"Warning: Invalid state structure detected: {state}")

    total_initial = initial_capital * len(cryptos)
    profit_or_loss = total_capital - total_initial
    p_o_l_plus_secured = profit_or_loss + total_removed
    write_global_log(f"Current Profit/Loss: {profit_or_loss:.6f} USDT.")
    print("Total :", p_o_l_plus_secured, "USDT")
    print(f"[PROFIT/LOSS] {profit_or_loss:.6f} USDT.")
    
#mariotto
try:
    set_process_priority()
    start_time = time.time()
    secure_time = time.time()
    CMM_time = time.time()
    backup_time = time.time()
    report_interval = 600  # 10 minutes
    CMM_interval = 600*3  # 30 minutes
    secure_interval = 86400 #24 hours
    backup_interval = 86400 #24 hours
    
    fetch_fear_and_greed_index()
    calculate_buy_on_drop(fear_and_greed_index)
    update_buy_on_drop()
    write_global_log("Starting the trading bot.")

    while True:
        if os.path.exists(stop_file):
            write_global_log("Stop file detected. Bot shutdown.")
            save_state(crypto_states)
            break
        
        save_state(crypto_states)
        
        if time.time() - last_update_time >= update_interval:
            write_global_log("Updating minimum order sizes...")
            minimum_order_sizes = fetch_minimum_order_sizes()
            last_update_time = time.time()
            write_global_log("Minimum order sizes updated successfully.")

        for symbol in cryptos:
            trading_logic(symbol)

        if time.time() - start_time >= report_interval:
            report_profit_or_loss()
            start_time = time.time()
        
        if time.time() - CMM_time >= CMM_interval:
            fetch_fear_and_greed_index()
            calculate_buy_on_drop(fear_and_greed_index)
            update_buy_on_drop()
            CMM_time = time.time()
            
        if time.time() - backup_time >= backup_interval:
            backup_state_file()
            backup_time = time.time()
            
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        if 13 <= current_hour < 18:
            funds_secured = False

        if 1 <= current_hour < 11:
            funds_secured = False
        
        if (current_hour == 12 and 0 <= current_minute < 1) and funds_secured == False:
            secure_funds(state_file)
            write_global_log("Restarting bot in 10 seconds...")
            time.sleep(10) 
            os.execl(sys.executable, sys.executable, *sys.argv)
            funds_secured = True

        time.sleep(2)

except Exception as e:
    handle_critical_error(str(e))
