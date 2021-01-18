#contraparte de tarea para generacion de senales
#esta clase contiene la informacion referente a la tarea de generacion
#es llamada por la clase senal para ejecutar la generacion de senales
import random
import math
import nidaqmx as nd
class actuador():
    def __init__(self):
        #guarda datos a escribir en el buffer del plot
        self.datosEscritos=[[],[],[]]
        #lista de canales para escribir obtenidos en la tarea elegida en config
        self.canales=[]
        #otros datos de la tarea de escritura
        self.tareaEscritura=None
        self.canales=None
        self.sampRate=0
        self.chanNum=0
        self.oleajeAmpBox=None
        self.oleajeProfBox=None

        self.vientoAmpBox=None
        self.vientoFreqBox=None
        self.oleajeSign='Sinusoidal'
        self.vientoSign='Ruido'
        #
        self.freqLabel=None
        self.longLabel=None

    def cambioOleaje(self):
        h=self.oleajeProfBox.value()
        a=self.oleajeAmpBox.value()/100.0
        lamb=(2*3.141592*0.15*h)/(a)
        if (2*3.141592*h/lamb)>1.5:
            e=0.01
            for i in range(1,200):
                c=4*3.141592*h/(i/100.0)
                val=0.30*(math.cosh(c)-1)/(math.sinh(c)+c)
                d=math.fabs(a-val)
                if d<e:
                    lamb=i/100.0
                    e=d
        freq=math.sqrt((9.81/(2*3.141592*lamb))*math.tanh((2*3.141592*h)/lamb))
        self.freqLabel.setText('Frecuencia de ola: '+"{:.2f}".format(freq)+' [Hz]')
        self.longLabel.setText('Longitud de ola: '+"{:.2f}".format(lamb*100)+' [cm]')
        self.oleajeFreq=freq


    def setParametrosActuadores(self):
        self.oleajeAmp=self.oleajeAmpBox.value()
        #self.oleajeFreq=self.oleajeFreqBox.value()

        self.vientoAmp=self.vientoAmpBox.value()
        self.vientoFreq = 1
        #self.vientoFreq=self.vientoFreqBox.value()
        self.datosEscritos = [[], [], []]

    def cargarTarea(self,tareaName):
        if not self.tareaEscritura == None:
            # quitar el callback de la tarea
            # self.tareaLectura.register_every_n_samples_acquired_into_buffer_event(self.numSamples, None)
            self.tareaEscritura.close()
        if not tareaName=='Ninguna':
            ptask = nd.system.storage.persisted_task.PersistedTask(tareaName)
            self.tareaEscritura = ptask.load()
            self.canales=nd._task_modules.channel_collection.ChannelCollection(self.tareaEscritura._handle)
            #caragr info de tarea samp rate y chan num
            self.sampRate=self.tareaEscritura.timing.samp_clk_rate
            self.chanNum=len(self.canales.channel_names)
            # lo siguiente no aplica para escritura investigar el equivalente
            #self.tareaEscritura.in_stream.auto_start = False
            #self.tareaLectura.register_every_n_samples_acquired_into_buffer_event(self.numSamples, callback)
        else:
            self.tareaEscritura=None
            self.sampRate = 0
            self.chanNum = 0

    def sinusoide(self,t,a,w):
        return a*math.sin(2*3.141592*w*t)


    def random(self,a):
        return a*(2*random.random()-1)

#clase thread q ejecuta la generacion de senales en base a la informacion contenida en actuador
from PyQt5.QtCore import QThread, pyqtSignal
import time
class Generador(QThread):
    #este metodo notifica al main thread de que se necesita alguna respuesta
    notificarCaptura = pyqtSignal(int)

    def __init__(self, actuadores, padre,condicion,mutex):
        super(Generador, self).__init__()
        #contiene los datos d ela tarea dew generacion
        self.actuadores = actuadores
        #indica el estado de la captura
        self.bandera=padre.status
        self.mtx=mutex
        self.cond=condicion
        self.padre=padre
        self.oleajeCallback=None
        self.vientoCallback=None

    def run(self):
        #inicia la tarea de generacion
        # self.actuadores.datosEscritos[0] = list(range(100))  # 100 time points
        # self.actuadores.datosEscritos[1] = [randint(0, 100) for _ in range(100)]  # 100 data points
        # self.actuadores.datosEscritos[2] = [randint(0, 100) for _ in range(100)]
        #mantiene generacion hasta q status sea falso
        if self.actuadores.oleajeSign=='Sinusoidal':
            self.oleajeCallback=lambda tiempo: self.actuadores.sinusoide(tiempo,self.actuadores.oleajeAmp,self.actuadores.oleajeFreq)
        else:
            self.oleajeCallback=lambda tiempo: self.actuadores.random(self.actuadores.oleajeAmp)
        if self.actuadores.vientoSign=='Sinusoidal':
            self.vientoCallback=lambda tiempo: self.actuadores.sinusoide(tiempo,self.actuadores.vientoAmp,self.actuadores.vientoFreq)
        else:
            self.vientoCallback=lambda tiempo: self.actuadores.random(self.actuadores.vientoAmp)

        t_0=time.time()
        t_inicial = t_0
        muestras_per_refresh=10
        #counter=0
        while(self.padre.status):
            self.mtx.lock()
            self.notificarCaptura.emit(1)

            #dummy example
            # self.actuadores.datosEscritos[0] = self.actuadores.datosEscritos[0][1:]  # Remove the first y element.
            # self.actuadores.datosEscritos[0].append(self.actuadores.datosEscritos[0][-1] + 1)  # Add a new value 1 higher than the last.
            #
            # self.actuadores.datosEscritos[1] = self.actuadores.datosEscritos[1][1:]  # Remove the first
            # self.actuadores.datosEscritos[2] = self.actuadores.datosEscritos[2][1:]
            # self.actuadores.datosEscritos[2].append(randint(0, 100))
            # self.actuadores.datosEscritos[1].append(randint(0, 100))
            #generar datos
            #counter=counter+1
            #indicar al main thread q debe redibujar el plot
            actual=time.time()
            delta=actual-t_inicial
            t_inicial=actual
            if delta>0.01:
                paso=delta/muestras_per_refresh
                i=0
                while i<muestras_per_refresh:
                    t=actual-t_0+i*paso
                    self.actuadores.datosEscritos[0].append(t)
                    self.actuadores.datosEscritos[1].append(self.vientoCallback(t))
                    self.actuadores.datosEscritos[2].append(self.oleajeCallback(t))
                    i+=1

                if len(self.actuadores.datosEscritos[0])>200:
                    self.actuadores.datosEscritos[0]=self.actuadores.datosEscritos[0][-200:]
                    self.actuadores.datosEscritos[1]=self.actuadores.datosEscritos[1][-200:]
                    self.actuadores.datosEscritos[2]=self.actuadores.datosEscritos[2][-200:]

            self.cond.wait(self.mtx)
            self.mtx.unlock()
        #indicar al main thread q debe inicar la siguiente captura de ser necesario
        self.notificarCaptura.emit(0)