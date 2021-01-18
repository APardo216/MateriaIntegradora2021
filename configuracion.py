import sys, subprocess, os
from tarea import *


try:
    import nidaqmx as dq
except NotImplementedError as nie:
    dq = None

class configuracion():

    def __init__(self, botonNiDaq, warningLabel,tareasDAQbox,tareasGenbox,tarea,etiquetaRate, etiquetaChan,actuador,etiquetaGRate,etiquetaGChan,
                 oleajeChan,vientoChan,frqBox ):
        if dq is None:
            botonNiDaq.setEnabled(False)
        else:
            warningLabel.setHidden(True)
        #metodo de llamada a controlador nidaqmx
        botonNiDaq.clicked.connect(lambda:
                                    subprocess.Popen([r'{0}\National Instruments\MAX\NIMax.exe'.format(
                                        os.environ['ProgramFiles(x86)'])]))
        #propiedades de clase
        self.freqBox=frqBox
        self.oleajeChan=oleajeChan
        self.vientoChan=vientoChan
        self.tareasDAQBox=tareasDAQbox
        self.tareasGenBox=tareasGenbox
        self.infoRate=etiquetaRate
        self.infoChan=etiquetaChan
        self.infoGRate=etiquetaGRate
        self.infoGChan=etiquetaGChan
        #self.oleajeSign=oleajeSign
        #self.vientoSign=vientoSign
        #crea objeto generador
        self.actuadores=actuador
        # crear objeto tareas
        self.tareas = tarea
        tareasDAQbox.addItem('Ninguna')
        tareasGenbox.addItem('Ninguna')
        for i in self.tareas.tareasDAQ[0]:
            tareasDAQbox.addItem(i)
        for i in self.tareas.tareasDAQ[1]:
            tareasGenbox.addItem(i)

        # oleajeSign.addItem('Sinusoidal')
        # vientoSign.addItem('Aleatoria')
        # vientoSign.addItem('Sinusoidal')
        # oleajeSign.addItem('Aleatoria')

        #trigger de cambio de opcion seleccionada para adq
        tareasDAQbox.currentTextChanged.connect(self.cambioComboDaq)
        #trigger de cambio de gen seleccionada
        tareasGenbox.currentTextChanged.connect(self.cambioComboGen)
        #trigger de cambio de canal de generacion
        oleajeChan.currentTextChanged.connect(lambda: self.cambioGenChan('oleaje'))
        vientoChan.currentTextChanged.connect(lambda: self.cambioGenChan('viento'))


    def getTareaActual(self):
        seleccionadas=[]
        seleccionadas.append(str(self.tareasDAQBox.currentText()))
        seleccionadas.append(str(self.tareasGenBox.currentText()))
        return seleccionadas

    def cambioComboDaq(self):
        self.tareas.cargarTarea(str(self.tareasDAQBox.currentText()))
        #mostrar datos de tarea en interfaz
        if self.tareas.sampRate==0:
            strRate="N/A"
            strChan="N/A"
        else:
            strRate=str(self.tareas.sampRate)
            strChan=str(self.tareas.chanNum)
            #setea el maximo sampling rate para las pruebas
            self.freqBox.setMaximum(self.tareas.sampRate)

        self.infoRate.setText("Frecuencia de muestreo: "+strRate+" [S/s]")
        self.infoChan.setText("Canales: "+strChan)

    # se debe llamar cuando se cambie la tarea de generacion
    def cambioComboGen(self):
        #cargar la tarea de generacion en el objeto contenedor
        self.actuadores.cargarTarea(str(self.tareasGenBox.currentText()))
        # mostrar datos de tarea en interfaz
        if self.actuadores.sampRate == 0:
            self.oleajeChan.clear()
            self.vientoChan.clear()
            strRate = "N/A"
            strChan = "N/A"
        else:
            self.oleajeChan.addItem('Ninguno')
            self.vientoChan.addItem('Ninguno')
            for c in self.actuadores.canales.channel_names:
                self.oleajeChan.addItem(c)
                self.vientoChan.addItem(c)
            strRate = str(self.actuadores.sampRate)
            strChan = str(self.actuadores.chanNum)
        self.infoGRate.setText("Frecuencia de muestreo: " + strRate + " [S/s]")
        self.infoGChan.setText("Canales: " + strChan)

        #se llama cuando se cambia la opcion de canal
    def cambioGenChan(self,comboBox):
        if comboBox=='oleaje':
            opcionElegida=self.oleajeChan.currentText()
            if (not opcionElegida=='Ninguno') and self.vientoChan.currentText()==opcionElegida:
                self.vientoChan.setCurrentIndex(0)
        else:
            opcionElegida = self.vientoChan.currentText()
            if (not opcionElegida == 'Ninguno') and self.oleajeChan.currentText() == opcionElegida:
                self.oleajeChan.setCurrentIndex(0)






