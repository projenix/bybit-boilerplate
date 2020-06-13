#import math
import numpy as np
import math

def klineToHlc3(klines):
	data = []
	for line in klines:
		lineAvg = (float(line[2]) + float(line[3]) + float(line[4])) / 3  # close,highest,lowest - all data is good to use.
		#lineAvg = float(line[2])
		data.append(lineAvg)
	return data

def removeSpikes(data):
	n = len(data)
	for i in range(1, n-2):
		normal = (data[i-1] + data[i+1]) / 2 # This only makes sense if data[i] is a spike
		if abs(data[i] - data[i-1]) > 0.01 * data[i-1] and abs(data[i] - data[i+1]) > 0.01 * data[i+1]: # If spike is more than 1% from the local context
			data[i] = (data[i] + normal) / 2 # Very conservative smoothening for now - This can get a lot more aggressive
	return data
