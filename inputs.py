
import ccxt

import time
from datetime import datetime
from config import config
from mmlib  import indicators
from mmlib import util
import numpy as np

#import statistics 
#import statsmodels
#import math


class BasicInputs: # General inputs
	def __init__(self, exchange, market):
		self.market = market
		self.baseCurrency = self.market.split('/')[0]
		self.quoteCurrency = self.market.split('/')[1]
		self.exchange = exchange 
		self.exchange.load_markets ()
		self.marketStructure = self.getMarketStructure()

		self.balances = self.getBalances()

		self.freeBalance = self.getFreeBalance()
		self.usedBalance = self.getUsedBalance()
		self.totalBalance = self.getTotalBalance()

		self.realizedPnl = self.balances['info']['result'][self.baseCurrency]['realised_pnl']
		self.unrealizedPnl = self.balances['info']['result'][self.baseCurrency]['unrealised_pnl']

		self.amountPrecision = self.marketStructure['precision']['amount']
		self.pricePrecision = self.marketStructure['precision']['price'] 
	
		self.candles = dict()
		self.hlc3 = dict()
		self.trades = self.getTrades()
		self.lastPrice = self.trades[-1]['price']
		self.meanCost = self.lastPrice * (1 + (self.unrealizedPnl/100))
		self.orderBook = self.getOrderBook()

		for timeFrame in config.timeFrames :
			self.candles[timeFrame] = self.getOhclv(timeFrame)
			self.hlc3[timeFrame] = util.klineToData(self.candles[timeFrame])


	def getMarketStructure(self):
		self.exchange.load_markets ()
		marketStructure = self.exchange.markets[self.market]
		return marketStructure

	def getBalances (self):
		return self.exchange.fetchBalance (params = {})

	# Current asset balances:
	def getFreeBalance(self): # This is for all balances, not just current asset (useful for portfolio balancing)
		return self.balances['free'][self.baseCurrency]

	def getUsedBalance(self): 
		return self.balances['used'][self.baseCurrency]

	def getTotalBalance(self): 
		return self.balances['total'][self.baseCurrency]


	# All portfolio balances:
	def getFreeBalances(self): # This is for all balances, not just current asset (useful for portfolio balancing)
		balance = dict()
		for key in self.balances['free'].keys():
			balance[key] = self.balances['free'][key]
		return balance

	def getUsedBalances(self):
		balance = dict()
		for key in self.balances['used'].keys():
			balance[key] = self.balances['used'][key]
		return balance

	def getTotalBalances(self):
		balance = dict()
		for key in self.balances['total'].keys():
			balance[key] = self.balances['total'][key]
		return balance

	def getOhclv(self, timeFrame):
		return self.exchange.fetch_ohlcv (self.market, timeFrame, limit=200)

	def getOrderBook(self):
		return self.exchange.fetch_order_book (self.market) 

	def getTrades(self):
		return self.exchange.fetch_trades (self.market)
		


##############################################################################

	
class Inputs(BasicInputs): # Specialiszed child class of Inputs
	def __init__(self, exchange, market):
		BasicInputs.__init__(self, exchange, market)
		# Todo: add more features here.
		#self.orderBook = self.getOrderBook()
		self.bestAsk = float(self.orderBook['asks'][0][0])
		self.bestBid = float(self.orderBook['bids'][0][0])
		self.midPrice = (self.bestAsk + self.bestBid) / 2
		self.skewedMidPrice = self.getMeanLobPrice(config.lobDepth)

		# Trades/history analysis (past 500 trades - will make this time-limit based later):
		self.tradesAnalysis = self.analyzeTrades()
		self.buyVolume = self.tradesAnalysis['buyVolume']
		self.meanBuyPrice = self.tradesAnalysis['meanBuyCost']
		self.sellVolume = self.tradesAnalysis['sellVolume']
		self.meanSellPrice = self.tradesAnalysis['meanSellCost']

		################################################
		# ADD your TA and feature calculation code here.
		################################################
		
	def analyzeTrades(self):
		analysis = dict()
		analysis['buyVolume'] = 0
		analysis['sellVolume'] = 0
		analysis['meanBuyCost'] = 0
		analysis['meanSellCost'] = 0

		#buyCount = 0
		#sellCount = 0

		totalBuyCost = 0
		totalSellCost = 0

		for trade in self.trades:
			price = trade['price']
			side = trade['side']
			amount = trade['amount']
			cost = trade['cost']

			if side == 'buy':
				#buyCount += 1
				analysis['buyVolume'] += amount
				totalBuyCost += cost

			if side == 'sell':
				#sellCount += 1
				analysis['sellVolume'] += amount
				totalSellCost += cost

		analysis['meanBuyCost'] = totalBuyCost / analysis['buyVolume']
		analysis['meanSellCost'] = totalSellCost / analysis['sellVolume']

		return analysis

