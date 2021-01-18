# -*- coding: utf-8 -*-
from PyQt5.QtCore import QWaitCondition, QMutex
from PyQt5.QtWidgets import QMessageBox
from qtpy import QtGui

from actuador import *
from tarea import *
import time

class captura():
    def __init__(self,startButton,medicionGraph,statusBar,repetirBox,duracionBox,muestrasBox,delayBox,config,graficos):
        self.startBtn=startButton
        self.startBtn.clicked.connect(self.manejarCaptura)
        self.graficoMedicion=medicionGraph
        self.logger=None
        self.barraEstado=statusBar
        self.repetirBox=repetirBox
        self.duracionBox=duracionBox
        self.muestrasBox=muestrasBox
        self.delayBox=delayBox
        self.configuracion=config
        self.graficos=graficos
        self.oleajeChan=None
        self.vientoChan=None
        self.guardarBtn=None
        self.descartBtn=None
        self.padre=None
        ##
        self.numSamples=5000
        self.totalLeidos=0
        self.status=False
        self.iteracion=0
        ##crea las funciones callback de lectura y escritura
        mL.bindear(self.callbackLectura)

    def manejarCaptura(self):
        #establece las variables necesarias para la captura
        if not self.status:
            self.numVeces=self.repetirBox.value()
            self.muestras=self.muestrasBox.value()
            self.periodoMuestreo=self.duracionBox.value()
            self.delay=self.delayBox.value()
            self.tareasSeleccionadas=self.configuracion.getTareaActual()
            habilitadas=[]
            for i in enumerate(self.tareasSeleccionadas):
                if i[1]=='Ninguna':
                    habilitadas.append(i[0])

            if habilitadas:
                if 0 in habilitadas and 1 in habilitadas:
                    self.callbackAdvertencia("No se ha seleccionado una tarea de captura ni de generación.")
                elif 0 in habilitadas:
                    self.callbackAdvertencia("No se ha seleccionado una tarea de captura de datos.")
                elif 1 in habilitadas:
                    self.callbackAdvertencia("No se ha seleccionado una tarea de generación de datos.")

                return
            if self.vientoChan.currentText()=='Ninguno' or self.oleajeChan.currentText()=='Ninguno':
                self.callbackAdvertencia("No se ha seleccionado un canal para la generación de senales.")
                return

            self.padre.actualizarStatusLabel('Listo')
            self.logger.append('Inicio de Test')
            self.startBtn.setIcon(QtGui.QIcon("res/stop.png"))
            self.startBtn.setText('Detener')


            self.iniciarCaptura()
        else:
            self.muestras=0

    def setCallbackAdvertencia(self,callback):
        self.callbackAdvertencia=callback

    def iniciarCaptura(self):
        self.t_0=time.time()
        self.iteracion+=1
        self.logger.append('Iteración '+str(self.iteracion)+'/'+str(self.numVeces))
        #indica que ha inicido la captura de datos
        self.status=True
        self.totalLeidos=0
        #crea thread para generacion de datos (siempre primero)
        self.mutex = QMutex()
        self.cond = QWaitCondition()
        self.configuracion.actuadores.setParametrosActuadores()
        self.generador=Generador(self.configuracion.actuadores,self,self.cond,self.mutex)
        self.generador.notificarCaptura.connect(self.manejarGeneracionEvent)
        self.generador.start()
        #establece threads para la captura de datos (debe setear un delay)
        ###iniciar tarea captura setear condiciones
        self.configuracion.tareas.setearTareaLec(self.t_0, self.delay)
        self.configuracion.tareas.calcularSalto(self.periodoMuestreo)

        self.graficos.limpiarGrafico()
        self.graficos.setMaximoPuntos(self.periodoMuestreo)
        self.graficos.startPloteo()

        self.mutexL = QMutex()
        self.condL = QWaitCondition()
        self.lector = Lector(self.configuracion.tareas, self, self.condL, self.mutexL)
        self.lector.notificarCaptura.connect(self.manejarLecturaEvent)
        self.lector.finished.connect(self.finThreadLectura)
        self.lector.start()


        self.configuracion.tareas.tareaLectura.register_every_n_samples_acquired_into_buffer_event(self.numSamples, callback)
        self.configuracion.tareas.tareaLectura.start()


        # self.configuracion.tareas.iniciarTareaLectura( self.duracion, self.numVeces,self.cond)
        # # ojo al orden de esta linea deberia ir primero
        # self.graficos.startPloteo()
        # # llamar al thread de actuadores

        # self.graficoMedicion.plotItem.plot([1, 2, 3, 4, 5, 6, 7, 8], [34, 34, 23, 22, 56, 34, 23, 32])

    def actualizarBarraEstado(self,muestras):
        if self.muestras>0:
            total=self.numVeces*self.muestras
            delta=100/total
            valor=math.floor(delta*((self.iteracion-1)*self.muestras+muestras))
            self.barraEstado.setValue(valor)
            self.logger.append(str(muestras)+' muestras colectadas')

    def finalizarCaptura(self):
        self.configuracion.tareas.tareaLectura.register_every_n_samples_acquired_into_buffer_event(self.numSamples,None)
        print('Finalizó lectura')
        if self.iteracion<self.numVeces:
            self.iniciarCaptura()
        else:
            self.iteracion=0
            self.logger.append('Captura finalizada.')
            self.guardarBtn.setDisabled(False)
            self.descartBtn.setDisabled(False)
            self.barraEstado.setValue(100)
            self.startBtn.setIcon(QtGui.QIcon("res/play.png"))
            self.startBtn.setText('Iniciar Test')

    def manejarGeneracionEvent(self,flag):
        #decidir q hacer en caso de una notificacion del generador
        if flag:
            self.graficos.actualizarGraficoEsc()
        else:
            print('finalizo worker de generacion')

    def manejarLecturaEvent(self,muestrasLeidas):
        #decidir q hacer en caso de una notificacion del lector
        self.graficos.actualizarGraficoLectura()
        self.actualizarBarraEstado(muestrasLeidas)
        if muestrasLeidas>=self.muestras:
            self.configuracion.tareas.tareaLectura.stop()
            self.status=False
            self.condL.wakeAll()
            self.cond.wakeAll()

    def finThreadLectura(self):
        self.finalizarCaptura()




    def callbackLectura(self):
        if not self.graficos.ploteando:
            self.condL.wakeAll()
        self.cond.wakeAll()


class manejadorL():
    def bindear(self,callback):
        self.cal=callback
    def exec(self):
        self.cal()
mL=manejadorL()

def callback(task_handle, every_n_samples_event_type, number_of_samples, callback_data=None):
    mL.exec()
    return 0