
import asyncio
import ccxt.async_support as ccxt

import time
from datetime import datetime
from config import config
from lib import util
from lib  import indicators
import numpy as np

#import statistics 
#import statsmodels
import math


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

		
		self.skewedMidPrice = self.getMeanLobPrice(config.lobDepth)

		# Trades/history analysis (past 500 trades - will make this time limit based later):
		self.tradesAnalysis = self.analyzeTrades()
		self.buyVolume = self.tradesAnalysis['buyVolume']
		self.meanBuyPrice = self.tradesAnalysis['meanBuyCost']
		self.sellVolume = self.tradesAnalysis['sellVolume']
		self.meanSellPrice = self.tradesAnalysis['meanSellCost']

		
		#self.vwap = indicators.vwap(self.candles['1m'][-config.vwmaLength:-1]) # Using n last elements
		self.fastVwap = indicators.vwap(self.candles['1m'][-config.fastVwapLength:-1]) # Same

		self.trueCandles = self.getTrueCandles(self.trades, 10) # <<<<<<<<<<<<<<<<<
		
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

	#######################################################################################################

	# True Candle generation - These are candles that have two additional fields for buy Volume and sell Volume + a period vwap instead of "close", they are backward compatible with regular candles in every way (drop-in replacement).
	def getTrueCandles(self, trades, length=10): # Candle length in seconds - Default is 10s
		tradeCount = len(trades) # This is currently always 500 in Bybit but we don't want to take it for granted in case it changes.
		trueCandles = []
		trades = np.array(trades)
		startTime = int(trades[0]['timestamp']/1000)
		endTime = int(trades[-1]['timestamp']/1000)
		candleCount = int((endTime - startTime) / length) 
		position = 0 # moving pointer/cursor

		#print('start time {0}'.format(startTime))
		#print('end of first candle {0}'.format(startTime+length))



		for i in range(0, candleCount):
			buyVolume = 0
			sellVolume = 0

			buyVwapTotal = 0
			buyCount = 0
			buyVwap = 0

			sellVwapTotal = 0
			sellCount = 0
			sellVwap = 0

			vwapTotal = 0
			vwap = 0

			count = 0

			high = trades[position]['price']
			low = trades[position]['price']
			openPrice = trades[position]['price']

			#print('passe {0}'.format(i))

			for trade in trades[position : -1]: # We are not iterating naively, there is a condition and a break statement below.
				ts = int(trade['timestamp']/1000)
				#print(ts)

				if ts >= startTime + (i * length) and ts < startTime + ((i+1) * length): # We are within a candle/window
					if trade['price'] > high:
						high = trade['price']
					if trade['price'] < low:
						low = trade['price']

					if trade['side'] == 'buy':
						buyVolume += trade['amount']
						buyVwapTotal += trade['amount'] * trade['price']
						vwapTotal += buyVolume * trade['price']
						buyCount += 1
						position += 1
			
					elif trade['side'] == 'sell':
						sellVolume += trade['amount']
						sellVwapTotal += trade['amount'] * trade['price']
						vwapTotal += sellVolume * trade['price']
						sellCount += 1
						position += 1
				else:
					#print('position {0}'.format(position))
					break # We exceeded the boundary of the current TrueCandle

			volume = buyVolume + sellVolume
			if buyVolume >0:
				buyVwap = round(buyVwapTotal / buyVolume , 2)
			if sellVolume>0:
				sellVwap = round(sellVwapTotal / sellVolume , 2)
			if volume >0:
				vwap = round((buyVwapTotal + sellVwapTotal) / (volume) , 2)

			# Contructing the TrueCandle:
			trueCandle = []
			trueCandle.append(startTime + (i * length)) # Timestamp
			trueCandle.append(openPrice) # Open 
			trueCandle.append(high) # High
			trueCandle.append(low) # Low
			trueCandle.append(vwap) # We intentionally use the VWAP here instead of the classic "close" (as opposed to creating a new slot for it).
			trueCandle.append(volume) # Volume
			# The new fields now:
			trueCandle.append(buyVolume) # NB: All volumes are dollar amounts
			trueCandle.append(sellVolume)
			trueCandle.append(buyVwap)
			trueCandle.append(sellVwap)

			trueCandles.append(trueCandle) # Appending to main list

		return trueCandles

	#######################################################################################################



	def getMeanLobPrice(self, depth):
		# Asks:
		totalAsks = 0
		askVolume = 0.0000001 # Avoiding division by zero.

		for ask in self.orderBook["asks"] :
			if float(ask[0]) < self.bestAsk * (1 + depth):
				totalAsks += float(ask[0])*float(ask[1])
				askVolume += float(ask[1])

		averageAsk = totalAsks/askVolume

		# Bids:
		totalBids = 0
		bidVolume = 0.0000001 # Avoiding division by zero.

		for bid in self.orderBook["bids"] :
			if float(bid[0]) > self.bestAsk * (1 - depth):
				totalBids += float(bid[0]) * float(bid[1])
				bidVolume += float(bid[1])

		averageBid = totalBids/bidVolume

		#meanPrice = (averageAsk + averageBid) /2
		#print("Natural/Naive mean price: " + str(meanPrice))

		#skewedMeanPrice = ((averageAsk * bidVolume) + averageBid * askVolume) / (askVolume + bidVolume) 
		#print("Natural mean price:  " + str(skewedMeanPrice))

		skewedMeanPrice = ((averageAsk * math.log(1+bidVolume)) + (averageBid * math.log(1+askVolume))) / (math.log(1+askVolume) + math.log(1+bidVolume))

		return skewedMeanPrice

