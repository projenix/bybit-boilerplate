import math
import statistics

def vwap(klines):  # wma = weighted moving average
    sum = 0
    totalVolume = 0.0000001  # Avoiding division by zero

    for line in klines:
        lineAvg = (float(line[2]) + float(line[3]) + float(line[4])) / 3  # high,low,close - hlc3.
        #volume = math.log(1 + float(line[6]))
        if float(line[5]) == 0: # If there is no volume at all
            volume = 0.00000001 # Avoiding zero values
        else:
            volume = float(line[5])
        sum += lineAvg * volume
        totalVolume = totalVolume + volume
    return sum / totalVolume


def historyWma(history: object) -> float:
    sum = 0
    totalVolume = 0.0000001  # Avoiding division by zero

    for trade in history:
        price = float(trade['price'])
        volume = float(trade['size'])
        sum += price * volume
        totalVolume += volume
    return sum / totalVolume

def watr(klines, minutes=20):  # WATR = Volume Weighted Average True Range / Will base this on the last 20 min (instead of the standard of 14 periods)
    sum = 0
    totalVolume = 0.0000001  # Avoiding division by zero

    for line in klines[len(klines) - minutes:-1]:
        lineAtr = abs(((float(line[3]) - float(line[4])) / float(line[4])) *
                      100)  # highest-lowest / output is in percents.
        volume = float(line[6])
        sum += (
            lineAtr * volume
        )  # This makes us skip empty minutes and very low volume spikes instead of mistaking them for low ATR
        totalVolume += volume
    return sum / totalVolume

def trueRange(klines, period = 20):
    
    return 0

def meanPriceSimple(fills):  # Deprecated
    sum = 0
    volume=0.0000001

    for trade in fills:
        sum += float(trade['price']) * float(trade['size'])
        volume += float(trade['size'])
    return sum / volume

def meanPrice(items, depth, side):  # Volume weighted mean price of historic trades per side up to a certain depth/quantity
    sum = 0
    volume=0.0000001

    for item in items:
        if volume < depth:
            sum += float(item['price']) * float(item['size']) # 1 item is 1 trade
            if side == "BUY":
                sum += float(item['fee'])
            elif side == "SELL":
                sum -= float(item['fee'])

            volume += float(item['size'])
    return sum / volume

def standardDeviation(data, length):
    lastSd = statistics.stdev(data[-length : -1])
    previousSd = + statistics.stdev(data[-2*length : -length])
    combination = (lastSd + 0.7*previousSd)/1.7 # Slight recency bias
    sdProgression = lastSd - previousSd

    return combination + sdProgression # Trend following anticipation (volatility expansion)


############################## EXPERIMENTAL OR DEPRECATED ###################################

def standardDeviationOld(history: object) -> float:
    wma = historyWma(history)
    sum = 0

    for trade in history:
        sum += pow(float(trade['price']) - wma , 2)
        #sum = float(trade['price']) - wma
        #sum = wma
        #print(sum)
    return math.sqrt(sum / len(history))




