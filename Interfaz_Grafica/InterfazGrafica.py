import numpy as np
import pyqtgraph as pg  
from PyQt5.QtWidgets import QWidget, QPushButton, QAction,QMenuBar,QMenu
from PyQt5 import QtGui,QtCore
import sys
from scipy.fftpack import fft
from scipy import signal

#### PARA LA SENAL DE PRUEBA 
from scipy.io import wavfile
####  PARA LEER EL .WAV DE LA SENAL DE Sweep
from threading import Thread
import serial

import time
######## CONFIG SERIE 
global LEN_VECTOR_SERIE 
global BAUD 
global PORT


LEN_VECTOR_SERIE = 1024 *4
BAUD = 112500
PORT ='COM3'
########################### ERRORES : HAY QUE VER COMO NORMALIZAR LA ESCALA ################
################################  VENTANA PRINCIPAL Y APLICACION ##################################

class Main_window(QtGui.QMainWindow): #### HEREDO LA CLASE QMainWindow

    def __init__ (self,parent =None): 

        

        ##########  CONFIGURACION DE VENTANA ##########    
        super(Main_window,self).__init__(parent)## QMainWindow parent object init
        global  LEN_VECTOR_SERIE
        ########### THREAD SERIAL ###########
        self.thread_signal = True
        self.connected = True
        self.data_vector = []
        self.CHUNK = LEN_VECTOR_SERIE
        self.num = 0
        self.AMPLITUD = 5 ### 5 Volts de amplitud pico a pico maxima
        
        self.data_vector_maxLen = self.CHUNK
        
        ########## CONFIGURACIONES BASICAS DE LA VENTANA
        pg.setConfigOptions(antialias=True)
        
        self.setWindowTitle("Analizador de Fourier")
        self.setGeometry(1,50,1300,720)

        ########## AGREGO EL LAYOUT Y LA GRAFICA DE PYQTGRAPHICS A LA VENTANA 
        self.Main_win = QtGui.QWidget()

        layout = QtGui.QGridLayout()
        self.Main_win.setLayout(layout)

        self.win = pg.GraphicsLayoutWidget()
        font = QtGui.QFont()

        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)

        self.labelTime = QtGui.QLabel("LabelTime")
        self.labelTime.setFont(font)
        
        
        ######## MARKER

        ## radio button 
        
        self.radio_butt_marker = QtGui.QRadioButton('Marker 10Hz p/step')
        self.marker = False
        self.point_marker=[0,0]
        self.radio_butt_marker.toggled.connect(lambda:self.Marker_Activate(self.radio_butt_marker))
        
        ## slider
        
        self.freq_pos=1
        self.slider_marker = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider_marker.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.slider_marker.setMinimum(1)
        self.slider_marker.setMaximum(2048)
        self.slider_marker.setSingleStep(1)
        
        self.slider_marker.valueChanged.connect(self.AdjustFreq)
        self.slider_marker.setMaximumWidth(100) ## para que no reescale la columna 
            
        layout.addWidget(self.win, 0, 1,4,1)## row=0,col=1, ancho de fila=1, ancho de columna=4 

        layout.addWidget(self.labelTime,0,0)
        layout.addWidget(self.radio_butt_marker,1,0,2,1)
        
        layout.addWidget(self.slider_marker,2,0)
        self.setCentralWidget(self.Main_win)
            
        ########## TIMER

        timer = QtCore.QTimer(self) ## actualiza la ventana, maneja los fps
        
        timer.timeout.connect(self.update)## connects the timeout event to the update function
        
        timer.start(30)## sets timer start with 30ms of timeout
        
        ########## MENU ##############
       
        ## Freq Response Show
       
        Freq_Response_Show_On = QAction('Freq_Response_Show_On',self)
        Freq_Response_Show_Off = QAction('Freq_Response_Show_Off',self)
        
        ## acciones de las ventanas
       
        Flattop = QAction('Flattop',self)
        Hamming = QAction('Hamming',self)
        Rectangular = QAction('Rectangular',self)
        Hann = QAction('Hann',self)
        Blackman = QAction('Blackman',self)
        BlackmanHarris = QAction('BlackmanHarris',self)
       
        ## acciones de la calibracion

        Calibrate1Khz = QAction('Calibrate1Khz',self) ## Tono pregrabado para calibrar 
        
        CalibrateOff = QAction('CalibrateOff',self)
        
        ## acciones del marcador

        MarkerOn= QAction('MarkerOn',self)
        MarkerOff= QAction('MarkerOff',self)
        
        ## creo a barra de menu y los submenu
        
        menubar = self.menuBar()
        filemenu = menubar.addMenu("Windows")
        
        ## submenu ventanas
        
        filemenu.addAction(Hamming)
        filemenu.addAction(Flattop)
        filemenu.addAction(Hann)
        filemenu.addAction(Blackman)
        filemenu.addAction(BlackmanHarris)
        filemenu.addAction(Rectangular)
        
        ## triggers de las acciones 
        
        Flattop.triggered.connect(lambda:self.Window('Flattop'))
        Hamming.triggered.connect(lambda:self.Window('Hamming'))
        Hann.triggered.connect(lambda:self.Window('Hann'))
        BlackmanHarris.triggered.connect(lambda:self.Window('BlackmanHarris'))
        Blackman.triggered.connect(lambda:self.Window('Blackman'))
        Rectangular.triggered.connect(lambda:self.Window('Rectangular'))
        

        ## Freq response
        
        self.thread_signal = False
        self.show_response=False
        Freq_Response_Show_On.triggered.connect(lambda: self.Show_response(True))
        Freq_Response_Show_Off.triggered.connect(lambda: self.Show_response(False))
        
        ########## VARIABLES DE LAS VENTANAS
        
        self.windows_choise='Rectangular' ### ESTADO INICIAL, NO APLICA NINGUNA VENTANA
        
        self.flattop_vec = []
        self.hamming_vec = []
        self.hann_vec = []
        self.blackmanHarris_vec = []
        self.blackman_vec = []
        self.cal_signal=False
       
        ########## CONFIGURACIONES DE LOS EJES ################
        
        self.traces =dict()

        wf_xlabels=[(0,'0'),(256,'256'),(512,'512'),(768,'768'),(1024,'1024')
                    ,(1280,'1280'),(1536,'1536'),(1792,'1792'),(2048,'2048'),(2304,'2304')
                    ,(2560,'2560'),(2816,'2816'),(3072,'3072'),(3328,'3328'),(3584,'3584')
                    ,(3840,'3840'),(4608,'4608')
                    ,(4096,'4096')]
        wf_xaxis = pg.AxisItem(orientation='bottom')
        wf_xaxis.setTicks([wf_xlabels])
        wf_xaxis.setLabel(text='Samples')
        # wf_ylabels=[(-5000,'-5000'),(-4000,'-4000'),(-3000,'-3000'),(-2000,'-2000'),
        #         (-1000,'-1000'),(0,'0'),(5000,'5000'),(4000,'4000'),(3000,'3000'),(2000,'-2000'),
        #         (1000,'1000')] ## La escala va desde -1  a  1 volt
                

        wf_ylabels=[(-3,'-3000')
        ,(-2,'-2000'),(-1,'-1000'),(0,'0'),(1,'1000'),(2,'2000')
        ,(3,'3000')] ## La escala va desde -5  a  5 volt
        wf_yaxis = pg.AxisItem(orientation='left')
        wf_yaxis.setTicks([wf_ylabels])
        wf_yaxis.setLabel(text='mV')
        
      
        self.sp_xlabels =[
                (np.log10(10),'10'), (np.log10(100),'.1') ,(np.log10(10000),'10'), (np.log10(1000),'1') 
                ,(np.log10(1),'0'),(np.log10(200),'.2'),(np.log10(300),'.3'),(np.log10(400),'.4'),(np.log10(500),'.5'),(np.log10(600),'.6')
                ,(np.log10(700),'.7'),(np.log10(800),'.8'),(np.log10(900),'.9'),(np.log10(2000),'2'),(np.log10(3000),'3'),(np.log10(4000),'4')
                ,(np.log10(5000),'5'),(np.log10(6000),'6'),(np.log10(7000),'7'),(np.log10(8000),'8'),(np.log10(9000),'9')
                ,(np.log10(11000),'11'),(np.log10(12000),'12'),(np.log10(13000),'13'),(np.log10(15000),'15')
                ,(np.log10(17000),'17'),(np.log10(19000),'19'),(np.log10(21000),'21')]
        
        ######### ESCALA EN dBFS ( 20log() )
        self.sp_ylabels =[ 
                (np.log10(1),'0') ,(20*np.log10(0.1),'-20') ,(20*np.log10(1e-2),'-40'),(20*np.log10(1e-3),'-60'),(20*np.log10(1e-4),'-80')
                ,(20*np.log10(1e-5),'-100'),(20*np.log10(1e-6),'-120'),(20*np.log10(1e-7),'-140'),(20*np.log10(10),'20')
        ]
        self.sp_xaxis=pg.AxisItem(orientation='bottom')
        self.sp_xaxis.setTicks([self.sp_xlabels])
        self.sp_xaxis.setLabel(text='Frequency [KHz]')
        
        self.sp_yaxis=pg.AxisItem(orientation='left')
        self.sp_yaxis.setTicks([self.sp_ylabels])
        self.sp_yaxis.setLabel(text="dBV")
        
        ###  Configuro los subplots
        self.waveform =self.win.addPlot(row=0,col=1,lockAcpect=True,title="Waveform ",axisItems={'bottom':wf_xaxis,'left':wf_yaxis} )
        self.spectrum =self.win.addPlot(row=1,col=1,title="Spectrum ",axisItems={'bottom':self.sp_xaxis ,'left':self.sp_yaxis})
        self.infinite_line_x=pg.InfiniteLine(pos=np.log10(self.freq_pos*10) ,pen='w')
        self.infinite_line_y=pg.InfiniteLine(pos=0 ,angle=0,pen='w')
        
        self.spectrum.addItem(self.infinite_line_x)
        self.spectrum.addItem(self.infinite_line_y)
        
        self.infinite_line_x.hide()
        self.infinite_line_y.hide()

        self.waveform.showGrid(x=True,y=True,alpha=0.3)
        self.spectrum.showGrid(x=True,y=True,alpha=0.3)
        
       

        ### Label para el marcador 
        self.LabelGraph =pg.TextItem("LabelTime",border='y')
        self.spectrum.addItem(self.LabelGraph,'ignoreBounds') ## el ignoreBounds hace que el plot no se reescale con el label
      
        
        self.K_escala = 1
        self.x=np.arange( 0 , self.CHUNK , 1 ) ## eje temporal
        self.f=np.linspace(0, 22000, int(self.CHUNK / 2), endpoint=False) #eje de frecuencias
      
        self.RATE = 44000
        ###### INICIO EL THREAD PARA COMUNICACION SERIE
        Thread(target = self.Init_Serial).start()



    ###### Thread que maneja los datos serie
    def Init_Serial(self): 
        global BAUD
        global PORT
        ser = serial.Serial()
        ser.baudrate = BAUD
        ser.port = PORT

        try:
            ser.open()
            open_right = True     
            self.connected = True  
        except: 
            print("Error al abrir el puerto")
            open_right = False
            self.connected = False
           

        p = 0    
        
        if open_right == True:   
            i = 0
            while 1:
                try: 
                    data = ser.read(4)
                    self.num = data[0]  + data[1] * 2**8 + data[2] * 2**16 + data[3] * 2**24 
                    
                    
                    if len(self.data_vector) < self.data_vector_maxLen :
                        self.num = (self.num - 2**23) * (5.0 / (2**24-1))#Vref=5V y ADC de 24 bits y elimino Offset de 2**23
                        self.data_vector.append(self.num)
                        
                    
                except:
                    break ## si hay un error de lectura salgo y cierro la conexion
            open_right = False
            ser.close() 

    ###### Funciones de posicion para el marcador
    def AdjustFreq(self):
    
        self.freq_pos = self.slider_marker.value()
    ###### Activo o desactivo el marcador
    def Marker_Activate(self,button):
    
        if button.isChecked() == True:
            self.marker = True
            
        else:
            self.marker = False
            
   

    #######  FUNCION DE VENTANAS
    def Window(self,win_name):
        self.windows_choise = win_name
        if(win_name == 'Flattop'):
            self.flattop_vec = signal.flattop(self.CHUNK,sym=False)
            
        if(win_name == 'Hamming'):
            self.hamming_vec = signal.hamming(self.CHUNK,sym=False)
            
        if(win_name == 'Hann'):
            self.hann_vec = signal.hann(self.CHUNK,sym=False)
        
        if(win_name == 'Blackman'):
            self.blackman_vec = signal.blackman(self.CHUNK,sym=False)
        
        if(win_name == 'BlackmanHarris'):
            self.blackmanHarris_vec = signal.blackmanharris(self.CHUNK,sym=False)
                
    ####### FUNCION DE TRAZO 
    def trace(self,name,dataset_x,dataset_y):
        
        if name in self.traces:
            if len(dataset_x) == len(dataset_y):
                
                self.traces[name].setData(dataset_x,dataset_y)
               

            
            
        else:
            if name=='waveform':
                
                self.traces[name]= self.waveform.plot(pen='g',width=3)
                self.waveform.setYRange(-3, 3 , padding=0.005)
                self.waveform.setXRange(0, self.CHUNK,padding=0.005)
                
      
        
            if name=='spectrum':
                
                self.traces[name] = self.spectrum.plot(pen='y',width=5)
                
                self.spectrum.setLogMode(x=True)
               
                self.spectrum.setYRange(-140,20,padding=0.005)
                ### Qt graph usa por defecto la notacion cientifica en escala logaritmica en vez
                ### de usar el numero, entonces lo ajusto para q muestre el numero
               
                self.spectrum.setXRange(
                        np.log10(10),np.log10(self.RATE / 2),padding=0.005)
                
                
    ######## FUNCION DE FRAME UPDATE ( se ejcuta con cada timeout del timer )        
    def update(self):
        ### SENAL
        if( (self.connected == True) and len(self.data_vector) == LEN_VECTOR_SERIE ):

            
            wf_data = self.data_vector ## grafico el vector de datos
           

        
            self.data_vector = [] ## luego de guardar el vector lo reseteo

            if (wf_data != [] ): ## verifico que no este vacio el vector de datos

                
            
                ###### SETEO EL LABEL CON EL VALOR EN mV
               

                wf_string_data = "Vp \n "+'{0:0.2f}'.format( (wf_data[ np.argmax(wf_data) ]*1000) ) + " mV"
            
                self.labelTime.setText( wf_string_data)
            

            ###### APLICO LA VENTANA CORRESPONDIENTE CON SUS FACTORES DE CORRECCION DE AMPLITUD
               
                if(self.windows_choise == 'Flattop'):   
                    wf_data = wf_data * 4.18 * self.flattop_vec

                if(self.windows_choise== 'Hamming'):
                    wf_data = wf_data * 1.85 * self.hamming_vec
                if(self.windows_choise == 'Hann'):
                    wf_data = wf_data * 2 *  self.hann_vec
                if(self.windows_choise == 'Blackman'):
                    wf_data = wf_data * 2.8 * self.blackman_vec
                if(self.windows_choise == 'BlackmanHarris'):
                    wf_data = wf_data * 2.8 * self.blackmanHarris_vec

                
                self.trace( name='waveform' , dataset_x=self.x , dataset_y=wf_data)

                
                ### ESPECTRO
                
                self.sp_data = fft(wf_data)

                self.sp_data = ( np.abs( self.sp_data[ 0 : int(self.CHUNK /2)  ] / ( self.CHUNK) ) ) * 2  
                #print(self.sp_data[np.argmax(self.sp_data)])
                self.sp_data = 20*np.log10(self.sp_data)
                
                ###### MANEJO EL MARKER
                if (self.marker == True) : ### Habilito o deshabilito el marcador
                    K_freq =  48000.0/int(self.CHUNK/2) ## hace que el marcador se mueva 10.76Hz con cada posicion de muestra 
                    
                    sp_string = '{0:0.2f}'.format(self.sp_data[self.freq_pos]) +" dBV"
                    
                    sp_string_freq = '{0:0.2f}'.format(self.freq_pos*K_freq) +" Hz"
                    
                    self.LabelGraph.show()
                    self.LabelGraph.setText("Amp: "+sp_string+ " Freq: "+ sp_string_freq )
                    self.LabelGraph.setPos(np.log10(self.freq_pos*K_freq), self.sp_data[self.freq_pos] )
                    self.infinite_line_x.setValue(np.log10(self.freq_pos*K_freq))
                    self.infinite_line_y.setValue(self.sp_data[self.freq_pos])
                    self.infinite_line_x.show()
                    self.infinite_line_y.show()    
                    
                else:
                    self.LabelGraph.hide()
                    self.infinite_line_x.hide()
                    self.infinite_line_y.hide()    
                
                
                try :
                    self.trace(name='spectrum', dataset_x=self.f , dataset_y=self.sp_data)

                except : print("no muestra el espectro")
                
            

        
        
if __name__ == '__main__':
    
    app = QtGui.QApplication(sys.argv) ##contenedor vacio de aplicacion
    GUI = Main_window()
    GUI.show() ## muestro la ventana
    
    sys.exit(app.exec_()) ## ejecuto la app
    