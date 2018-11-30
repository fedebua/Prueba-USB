import numpy as np
import matplotlib.pyplot as plt
import csv


###DEFINICIONES###

f = 50
Amp_int24 = 2**24
sin = []
t = np.linspace(0, 4096,4096)

sin= np.int32( Amp_int24*np.cos(t*f*np.pi) + 2**24 ) 
print(len(sin) )
#sin = np.int32(sin)
#####LO ESCRIBO EN UN ARCHIVO CSV#####
with open('Senoidal.csv', mode='w') as FILE:
	writer = csv.writer(FILE, delimiter=',', quotechar=' ', quoting=csv.QUOTE_ALL)
	writer.writerow(sin)
print("ARCHIVO ESCRITO EXITOSAMENTE")

plt.plot(t, sin )
plt.show()
#print(sin_compleja[0:100])