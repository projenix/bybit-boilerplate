
import asyncio
import ccxt.async_support as ccxt

import time
from datetime import datetime
from config import config
from lib import util
import numpy as np

#import statistics 
#import statsmodels
#import math


class BasicInputs:
	def __init__(self, exchange, market):
		self.market = market
		self.baseCurrency = self.market.split('/')[0]
		self.quoteCurrency = self.market.split('/')[1]
		self.exchange = exchange
		self.candles = dict()
		self.hlc3 = dict()
		asyncio.get_event_loop().run_until_complete(self.pullData()) # All the I/O is done here - This is a blocking call that waits for all the non-blocking async loading to finish before we continue.

		# Data processing:
		self.freeBalance = self.getFreeBalance()
		self.usedBalance = self.getUsedBalance()
		self.totalBalance = self.getTotalBalance()
		self.realizedPnl = self.balances['info']['result'][self.baseCurrency]['realised_pnl']
		self.unrealizedPnl = self.balances['info']['result'][self.baseCurrency]['unrealised_pnl']
		self.amountPrecision = self.marketStructure['precision']['amount']
		self.pricePrecision = self.marketStructure['precision']['price'] 
		self.lastPrice = self.trades[-1]['price']
		self.meanCost = self.lastPrice * (1 + (self.unrealizedPnl/100))
		self.bestAsk = float(self.orderBook['asks'][0][0])
		self.bestBid = float(self.orderBook['bids'][0][0])
		self.midPrice = (self.bestAsk + self.bestBid) / 2

		
	async def pullData(self): # This pulls the data asynchronously from the exchange
		await self.exchange.load_markets()
		self.marketStructure = await self.getMarketStructure()
		self.balances = await self.getBalances()
		self.orders = await self.exchange.fetch_orders()
		self.trades = await self.getTrades()
		

		for timeFrame in config.timeFrames :
			self.candles[timeFrame] = await self.getOhclv(timeFrame)

		# Comment this out if you don't need it:
		self.orderBook = await self.getOrderBook()
		await self.exchange.close()



	async def getMarketStructure(self):
		await self.exchange.load_markets()
		marketStructure = self.exchange.markets[self.market]
		return marketStructure

	async def getBalances (self):
		return await self.exchange.fetchBalance (params = {})

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

	async def getOhclv(self, timeFrame):
		return await self.exchange.fetch_ohlcv (self.market, timeFrame, limit=200)

	async def getOrderBook(self):
		return await self.exchange.fetch_order_book (self.market) 

	async def getTrades(self):
		# async fetchTrades (symbol, since = undefined, limit = undefined, params = {})
		return await self.exchange.fetch_trades (self.market)
		



##############################################################################

	
class Inputs(BasicInputs): # Specialiszed child class of Inputs
	def __init__(self, exchange, market):
		BasicInputs.__init__(self, exchange, market)
		# Todo: add more features here.
		#self.orderBook = self.getOrderBook()
		self.bestAsk = float(self.orderBook['asks'][0][0])
		self.bestBid = float(self.orderBook['bids'][0][0])
		self.midPrice = (self.bestAsk + self.bestBid) / 2

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

