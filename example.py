#!/usr/bin/env python3

import ccxt.async_support as ccxt
import asyncio

import sys, getopt, time
from datetime import datetime
from lib import inputs
from lib import indicators
from lib import util
from config import config


market = 'BTC/USD'

exchange = ccxt.bybit () # default id
id = 'bybit'
mm = eval ('ccxt.%s ()' % id)
bybit = getattr (ccxt, 'bybit') ()

# from variable id
exchange_id = 'bybit'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
	'apiKey': config.apiKey,
	'secret': config.secret,
	'timeout': 30000,
		'enableRateLimit': True
	})


inputs = inputs.Inputs(exchange, market)




print('last price: {0}'.format(inputs.lastPrice))


print('Total balance: {0}'. format(inputs.totalBalance))


print('Trades analysis: {0}'.format(inputs.tradesAnalysis))






