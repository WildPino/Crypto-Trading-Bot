# Crypto Trading Bot

This is an automated cryptocurrency trading bot that analyzes the market and executes buy/sell orders. The bot is designed to optimize trading strategies by continuously learning from past trades and market conditions.

## Features

Automated trading on KuCoin

Adaptive risk management

Continuous learning and strategy improvement

Compatible with Linux, macOS, and Windows

## Disclaimer

This bot is an experimental project and should not be used for real financial investments without proper risk assessment. Use at your own discretion.

## How to use

### Configure KuCoin API
exchange = ccxt.kucoin({
    'apiKey': 'XXXXXX',
    'secret': 'XXXXXXX',
    'password': 'XXXXX',
})

### You can change the crypto that you want to follow
cryptos = ['BTC/USDT', 'ETH/USDT', 'LINK/USDT', 'TON/USDT', 'XLM/USDT', 'DOT/USDT', 'UNI/USDT', 'ICP/USDT', 'APT/USDT', 'AAVE/USDT', 'POL/USDT', 'VIRTUAL/USDT', 'ARB/USDT', 'FIL/USDT', 'ATOM/USDT', 'OP/USDT', 'TIA/USDT', 'IMX/USDT', 'INJ/USDT', 'GRT/USDT', 'WLD/USDT', 'JASMY/USDT', 'RUNE/USDT', 'RAY/USDT', 'FLR/USDT', 'QNT/USDT', 'KCS/USDT', 'CRV/USDT', 'ENS/USDT', 'AR/USDT', 'SOL/USDT']

### Change the initial capital
initial_capital = 45 

!!! Be sure to have at least (intital_capital) * (number of cryptos) in your exchange in USTD !!!

