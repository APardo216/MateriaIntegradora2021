import math
from time import sleep
import numpy as np
from scipy.fft import rfft, rfftfreq
from PyQt5 import QtWidgets, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
from random import randint

class grafico():
    def __init__(self,graficoLec,tarea,graficoOleaje,graficoViento,actuador,graficFreq):
        self.graficoLectura=graficoLec
        self.graficoFreq=graficFreq
        self.tarea=tarea
        self.graficoOlj=graficoOleaje
        self.graficoVnt=graficoViento
        self.actuadores=actuador
        self.lineas=[]
        self.lineasFreq=[]
        self.lineaOleaje=None
        self.lineaViento=None
        self.setActuadoresPlot()
        self.ploteando=False
        self.maximoPuntos=0
        self.leyenda = None

    def setMaximoPuntos(self,freq):
        #para 5s de muetsra de datos necesitamos x puntos
        self.maximoPuntos=math.ceil(5*freq)

    def startPloteo(self):
        #definir el numero de lineas a plotear en base a la tarea de lectura seleccionada tarea
        canales=self.tarea.canales
        self.deltaT=1.0/self.tarea.sampRate
        self.indicesPlot=[]
        self.leyenda=self.graficoLectura.addLegend()
        for c in enumerate(canales):
            if self.tarea.modelo.test[c[0]]:
                self.indicesPlot.append(c[0])
                p=self.tarea.modelo._data[c[0]][1]
                pen = pg.mkPen(color=(p[0], p[1], p[2]))
                self.lineas.append(self.graficoLectura.plotItem.plot(pen=pen,name=self.tarea.modelo._data[c[0]][0]))
                self.lineasFreq.append(self.graficoFreq.plotItem.plot(pen=pen))

    def setActuadoresPlot(self):
        pen = pg.mkPen(color="b")
        pen2= pg.mkPen(color="g")
        self.lineaOleaje=self.graficoOlj.plotItem.plot(pen=pen)
        self.lineaViento=self.graficoVnt.plotItem.plot(pen=pen2)


    def actualizarGraficoLectura(self):
        #preparar datos a plotear

        self.ploteando=True

        tamano = len(self.tarea.datosLeidos[0])
        if tamano>self.maximoPuntos:
            liminferior=tamano-self.maximoPuntos-1
        elif tamano:
            liminferior=0
        else:
            self.ploteando = False
            return

        datos=[]

        for c in enumerate(self.tarea.datosLeidos):
            datos.append(self.tarea.datosLeidos[c[0]][liminferior:])


        for p in enumerate(self.lineas):
            # print(p)
            p[1].setData(datos[0], datos[self.indicesPlot[p[0]]+1])
            yf = rfft(datos[self.indicesPlot[p[0]]+1])
            xf = rfftfreq(len(datos[0]), 1 / self.tarea.freq)
            self.lineasFreq[p[0]].setData(xf,np.abs(yf))
        #plotear ffts


        self.ploteando = False



    def limpiarGrafico(self):
        self.lineas = []
        self.lineasFreq=[]
        #self.graficoVnt.clear()
        #self.graficoOlj.clear()
        self.graficoLectura.clear()
        self.graficoFreq.clear()
        if self.leyenda!=None:
            self.leyenda.scene().removeItem(self.leyenda)


    def actualizarGraficoEsc(self):
        self.lineaViento.setData(self.actuadores.datosEscritos[0],self.actuadores.datosEscritos[1])
        self.lineaOleaje.setData(self.actuadores.datosEscritos[0],self.actuadores.datosEscritos[2])

