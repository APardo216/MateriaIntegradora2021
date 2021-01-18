import nidaqmx as nd
import time
import math

import numpy
from qtpy import QtCore, QtGui

crayola=[(222,105,0),(51,51,153),(27,167,123),(173,0,0),(230,51,0),(0,105,189),(0,216,160),(214,37,24),(33,35,33),(26,173,224),(205,220,57),(233,30,99),(86,65,140),(86,65,140),(250,122,0),(248,152,200)]
class tarea():

    def __init__(self):
        self.tareasDAQ=[]
        self.actualizarTareas()
        self.datosLeidos=[]
        self.tareaLectura=None
        self.tareaEscritura=None
        self.listaCView=None
        self.sampRate=0
        self.chanNum=0
        self.canales=None

        self.muestrasLeidas=0
        self.muestrasAdquiridas=0
        self.salto=0
        self.freq=0

    def setearTareaLec(self,t,delay):
        self.t_0=t
        self.delay=delay
        self.datosLeidos = [[]]
        for c in self.canales:
            self.datosLeidos.append([])
        self.muestrasLeidas = 0
        self.muestrasAdquiridas = 0


    def calcularSalto(self,freq):
        self.salto=self.sampRate/freq
        self.freq=freq

    def cargarTarea(self,tareaName):
        if not self.tareaLectura == None:
            # quitar el callback de la tarea
            # self.tareaLectura.register_every_n_samples_acquired_into_buffer_event(self.numSamples, None)
            self.tareaLectura.close()
        if not tareaName=='Ninguna':
            ptask = nd.system.storage.persisted_task.PersistedTask(tareaName)
            self.tareaLectura = ptask.load()
            self.canales=nd._task_modules.channel_collection.ChannelCollection(self.tareaLectura._handle)
            #caragr info de tarea samp rate y chan num
            self.sampRate=self.tareaLectura.timing.samp_clk_rate
            self.chanNum=len(self.canales.channel_names)

            self.tareaLectura.in_stream.auto_start = False
            self.mostrarCanales()
        else:
            self.tareaLectura=None
            self.sampRate = 0
            self.chanNum = 0
            self.listaCView.setModel(None)

    def actualizarTareas(self):
        sys=nd.system.system.System()
        tareas=sys.tasks.task_names
        self.tareasDAQ=[[],[]]
        for n in tareas:
            ptask = nd.system.storage.persisted_task.PersistedTask(n)
            t=ptask.load()
            ao=t.ao_channels.channel_names
            ai=t.ai_channels.channel_names
            print(ai)
            print(ao)
            if ai:
                self.tareasDAQ[0].append(n)
            if ao:
                self.tareasDAQ[1].append(n)
            t.close()


    def setRate(self,freq):
        self.rate=freq

    def actualizarDatosLeidos(self):
        list=self.tareaLectura.read(number_of_samples_per_channel=nd.constants.READ_ALL_AVAILABLE)
        maxIndice=len(list[0])
        if time.time()-self.t_0>self.delay:
            if list:
                while True:
                    indice=math.ceil((self.muestrasAdquiridas+1)*self.salto)-self.muestrasLeidas


                    if indice>maxIndice:
                        break
                    #si no agragr datos a lista con el timestamp, restar 1 del indice par aleer list
                    self.muestrasAdquiridas += 1
                    self.datosLeidos[0].append(self.muestrasAdquiridas/self.freq)
                    for i in enumerate(list):
                        self.datosLeidos[i[0]+1].append(list[i[0]][indice-1])


                self.muestrasLeidas+=maxIndice


            return self.muestrasAdquiridas
        else:
            return 0



    def setGrafico(self,grafico):
        self.grafico=grafico

    def mostrarCanales(self):
        datos=[]
        for c in enumerate(self.canales.channel_names):
            datos.append([c[1],crayola[c[0]%len(crayola)],''])

        self.modelo=NumpyModel(datos)
        self.listaCView.setModel(self.modelo)
        header = self.listaCView.horizontalHeader()
        header.sectionPressed.connect(self.modelo.toggleCheckState)




#clase thread q ejecuta la recopilacion de senales en base a la informacion contenida en tarea
from PyQt5.QtCore import QThread, pyqtSignal, Qt


class Lector(QThread):
    #este metodo notifica al main thread de que se necesita alguna respuesta
    notificarCaptura = pyqtSignal(int)

    def __init__(self, tarea, padre,condicion,mutex):
        super(Lector, self).__init__()
        #contiene los datos d ela tarea dew generacion
        self.tarea = tarea
        #indica el estado de la captura
        self.bandera=padre.status
        self.mtx=mutex
        self.cond=condicion
        self.padre=padre


    def run(self):
        #inicia la tarea de generacion

        #mantiene generacion hasta q status sea falso
        inicio=False
        while(self.padre.status):
            self.mtx.lock()
            #leer datos de sesnores
            if inicio:
                numero=self.tarea.actualizarDatosLeidos()
                self.notificarCaptura.emit(numero)


            #indicar al main thread q debe redibujar el plot
            self.cond.wait(self.mtx)
            self.mtx.unlock()
            inicio=True




class NumpyModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data
        self.test=[]
        for c in data[0]:
            self.test.append(True)
        self.header_icon = None
        self.setHeaderIcon()

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if (index.column() == 2):
            value = ''
        elif (index.column() == 1):
            g=self._data[index.row()][index.column()]
            value=str(g[0])+','+str(g[1])+','+str(g[2])
        else:
            value = QtCore.QVariant(self._data[index.row()][index.column()])
        if role == QtCore.Qt.EditRole:
            return value
        elif role == QtCore.Qt.DisplayRole:
            return value
        elif role==Qt.DecorationRole:
            if index.column()==1:
                g = self._data[index.row()][index.column()]
                return QtGui.QColor(g[0],g[1],g[2])

        elif role == QtCore.Qt.CheckStateRole:
            if index.column() == 2:
                if self.test[index.row()]:
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        return QtCore.QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole and index.column() == 2:
            if value == Qt.Checked:
                self.test[index.row()] = True
            else:
                self.test[index.row()] = False
            self.setHeaderIcon()

        elif role == Qt.EditRole and index.column() != 2:
            row = index.row()
            col = index.column()
            if value.isdigit():
                self._array[row, col] = value

        return True

    def flags(self, index):
        if not index.isValid():
            return None

        if index.column() == 2:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def headerData(self, index, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DecorationRole:
            if index == 2:
                return QtCore.QVariant(
                    QtGui.QPixmap(self.header_icon).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if index ==0:
                return QtCore.QVariant('Nombre')
            elif index==1:
                return QtCore.QVariant('Color')
            else:
                return QtCore.QVariant('Habilitado')

        return QtCore.QVariant()

    def setHeaderIcon(self):
        if all(self.test):
            self.header_icon = 'res/checked.png'
        elif not any(self.test):
            self.header_icon = 'res/unchecked.png'
        else:
            self.header_icon = 'res/intermediate.png'
        self.headerDataChanged.emit(Qt.Horizontal, 3, 3)

    def toggleCheckState(self, index):
        if index == 2:
            if not any(self.test):
                for p in enumerate(self.test):
                    self.test[p[0]]=True

            else:
                for p in enumerate(self.test):
                    self.test[p[0]] = False

            topLeft = self.index(0, 2)
            bottomRight = self.index(self.rowCount(0), 2)
            self.dataChanged.emit(topLeft, bottomRight)
            self.setHeaderIcon()

