import serial
import time
import numpy as np
################### HASTA ACA ANDA ################
ser = serial.Serial()
ser.baudrate = 9600
ser.port = 'COM9'

ser.close()
ser.open()
#print("cant open port ")
i = 0
while 1:
	data = ser.read(4)
	num = data[0] + data[1] * 2**8 + data[2] * 2**16 + data[3] * 2**24  
	print( num )    
ser.close() # Only executes