import ccxt
#import sys, getopt, time
#from datetime import datetime

from lib import inputs
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


print('last price')
print(inputs.lastPrice)

print('meanCost')
print(inputs.meanCost)

print('Trades analysis:')
print(inputs.tradesAnalysis)

print('used')
print(inputs.usedBalance)

print('total')
print(inputs.totalBalance)

print('realizedPnl')
print(inputs.realizedPnl)

print('unrealizedPnl')
print(inputs.unrealizedPnl)



