# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThread, pyqtSignal
from datetime import datetime
from WTtest_ui import *
from configuracion import *
from captura import *
from string import Template
from grafico import  *
import math
from actuador import *

_COLOR_PALETTE_ORANGE = dict(primary='rgb(0, 195, 255)', primaryhex='#00c3ff', hover='rgb(230, 126, 34)', primarylight='rgba(211, 84, 00, 10%)',
                             hoverlight='rgba(230, 126, 34, 20%)',selected='rgb(46, 204, 113)')
# _COLOR_PALETTE_BW = dict(primary='#333333', hover='#666666')
_COLOR_PALETTE_BW = dict(primary='rgb(51, 51, 51)', hover='rgb(102, 102, 102)')

COLOR_PALETTE = _COLOR_PALETTE_ORANGE

class VentanaPrincipal(QtWidgets.QMainWindow, Ui_ventanaPrincipal):
    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        self.setupUi(self)
        with open('style_template.css', 'r', encoding='utf-8') as fh:
            src = Template(fh.read())
            src = src.substitute(COLOR_PALETTE)
            #self.setStyleSheet(src)
        self.progresVal=0
        # crear objeto tareas
        self.tarea = tarea()
        #crea un objeto actuador
        self.actuadores=actuador()
        #self.actuadores.oleajeSign=self.oleajeSign
        #self.actuadores.vientoSign=self.vientoSign
        self.actuadores.oleajeAmpBox=self.oleajeAmp
        self.actuadores.oleajeProfBox=self.profundidadBox
        self.actuadores.vientoAmpBox=self.vientoAmp
        #self.actuadores.vientoFreqBox=self.vientoFreq
        self.actuadores.freqLabel=self.oleajeFreqLabel
        self.actuadores.longLabel=self.oleajeLongLabel
        self.oleajeAmp.valueChanged.connect(self.actuadores.cambioOleaje)
        self.profundidadBox.valueChanged.connect(self.actuadores.cambioOleaje)
        self.actuadores.cambioOleaje()

        # crear un objeto configuracion
        self.config = configuracion(botonNiDaq=self.nidaqmx, warningLabel=self.warningLbl,tareasDAQbox=self.tareasAdq,tareasGenbox=self.tareasGen,tarea=self.tarea,
                                    etiquetaChan=self.infoChan,etiquetaRate=self.infoFreq,actuador=self.actuadores,etiquetaGRate=self.infoGFreq,etiquetaGChan=self.infoGChan,
                                    oleajeChan=self.oleajeChan,vientoChan=self.vientoChan,frqBox=self.duracionBox)
        # crear objeto de graficos
        self.graficos = grafico(self.medidasGraph, self.tarea,graficoOleaje=self.oleajeGraph,graficoViento=self.vientoGraph,actuador=self.actuadores,graficFreq=self.freqDomGraph)

        #crear un objeto captura
        self.captura=captura(startButton=self.start,medicionGraph=self.medidasGraph,config=self.config,statusBar=self.progressBar,repetirBox=self.repetirBox,
                             duracionBox=self.duracionBox,muestrasBox=self.muestrasBox,delayBox=self.delayBox,graficos=self.graficos)
        self.captura.oleajeChan=self.oleajeChan
        self.captura.vientoChan=self.vientoChan
        self.captura.logger=self.logs
        self.captura.setCallbackAdvertencia(self.mostrarAdvertencia)
        self.captura.guardarBtn=self.saveBtn
        self.captura.descartBtn=self.descartBtn
        self.captura.padre=self

        self.tarea.setGrafico(self.graficos)
        self.tarea.listaCView=self.listaCanalesView
        self.saveBtn.clicked.connect(self.guardarDatos)

        ##########################################configurar estilo de graficos de ploteo
        # Add Background colour to white
        self.medidasGraph.setBackground('w')
        self.freqDomGraph.setBackground('w')
        self.oleajeGraph.setBackground('w')
        self.vientoGraph.setBackground('w')
        # Add Title
        #self.medidasGraph.setTitle("Your Title Here", color="b", size="30pt")
        # Add Axis Labels
        styles = {"color": "#00f", "font-size": "15px"}
        self.medidasGraph.setLabel("left", "Aceleración [g]", **styles)
        self.medidasGraph.setLabel("bottom", "Tiempo [s]", **styles)

        self.freqDomGraph.setLabel("left", "Amplitud", **styles)
        self.freqDomGraph.setLabel("bottom", "Frecuencia [Hz]", **styles)

        self.oleajeGraph.setLabel("left", "Altura [cm]", **styles)
        self.oleajeGraph.setLabel("bottom", "Tiempo [s]", **styles)

        self.vientoGraph.setLabel("left", "Aceleración [g]", **styles)
        self.vientoGraph.setLabel("bottom", "Tiempo [s]", **styles)
        # Add legend
        #leyenda=self.medidasGraph.addLegend()
        #self.graficos.leyenda=leyenda
        #self.oleajeGraph.addLegend()
        #self.vientoGraph.addLegend()
        # Add grid
        self.medidasGraph.showGrid(x=True, y=True)
        self.freqDomGraph.showGrid(x=True, y=True)
        self.oleajeGraph.showGrid(x=True, y=True)
        self.vientoGraph.showGrid(x=True, y=True)
        # Set Range
        #self.medidasGraph.setXRange(0, 10, padding=0)
        #self.freqDomGraph.setXRange(0, 10, padding=0)
        #self.oleajeGraph.setXRange(0, 10, padding=0)
        #self.vientoGraph.setXRange(0, 10, padding=0)
        #self.medidasGraph.setYRange(20, 55, padding=0)


    def guardarDatos(self):
        # generar nombre de archivo a guardar
        now = datetime.now()
        date_time = now.strftime("%m-%d-%Y")
        print("date and time:", date_time)
        nombre = QtGui.QFileDialog.getSaveFileName(self, "Guardar como", "dataset-"+date_time, ".csv")
        self.updater = Guardar(self,nombre)
        self.updater.actualizar.connect(self.actualizarProgressBar)
        self.updater.start()
        self.saveBtn.setDisabled(True)
        self.descartBtn.setDisabled(True)

    def actualizarProgressBar(self,valor):
        self.progressBar.setValue(valor)

    def actualizarStatusLabel(self,estado):
        self.estadoLabel.setText(estado)

    def mostrarAdvertencia(self,texto):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Error al iniciar la captura")
        msg.setInformativeText("No se encontró una configuracion DAQ adecuada")
        msg.setWindowTitle("Advertencia")
        msg.setDetailedText(texto)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        self.contenedorPrincipal.setCurrentIndex(2)

class Guardar(QThread):
    actualizar = pyqtSignal(int)
    def __init__(self,padre,nombre):
        super(Guardar, self).__init__()
        self.tarea=padre.tarea
        self.nombre=nombre
        self.padre=padre


    def run(self):

        # condicion de guardado
        if self.nombre[0]:
            archivo = open(self.nombre[0] + self.nombre[1], 'w')
            # preparar buffer de escritura
            datos = ""
            num = len(self.tarea.datosLeidos[0])
            delta = 100/ num
            c=0
            i = 0
            while i < num:
                linea = ""
                for c in self.tarea.datosLeidos:
                    linea = linea + str(c[i]) + ','
                linea = linea[:-1] + "\n"
                datos = datos + linea
                i += 1
                v = math.floor(i * delta)
                if not c==v:
                    self.actualizar.emit(v)
                    c=v

            archivo.write(datos)
            self.actualizar.emit(0)
            archivo.close()
            self.padre.actualizarStatusLabel('Guardado')




if __name__ == "__main__":
    aplicacion = QtWidgets.QApplication([])
    ventana = VentanaPrincipal()
    ventana.show()
    aplicacion.exec_()