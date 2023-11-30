
#gateway adress  10.100.19.254 volt


from pylab import *
import random
import numpy
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys
import socket
import os
import winsound
frequency = 2500
duration = 1000
from PyQt5.QtWidgets import QAction, QMenu, QFrame, QMainWindow, QApplication, QPushButton, QWidget, QGridLayout, QLabel, QLineEdit, QGroupBox, QComboBox, QCheckBox, QRadioButton, QVBoxLayout
from PyQt5.QtCore import Qt, QEvent, QTimer
from datetime import datetime
from PyQt5.QtGui import QPixmap, QPalette
from time import sleep
import getpass
felhasznalonev = getpass.getuser()


import pypyodbc
# Adatbázis kapcsolódási információk
server = 'DESKTOP-MQABLW\SQLEXPRESS'
database = 'spektro'
username = 'Andris'
password = 'g7sUkRVYvS6oErb'
# Adatbázis csatlakozás létrehozása
connection = pypyodbc.connect(f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}')




#Frekvenciát . al lehet küldeni !!! (PONT)

tesztAllapot = False

class Window(QMainWindow):
    def __init__(self):
        
        super().__init__() 
        
        labelWidth = 150  # Feliratok szélseeége
        frameWidth = 400  # Beállítási ablak szélessége
        wid = QFrame()  #kellet, mert self-re nem engedte ráhúzni a layoutot!
        fullGrid = QGridLayout()  # ebbe rakodom bele a csoportokat
        
        self.setWindowTitle("Spektrumanalizátor GUI")
        

        #self.set_tooltips()    
        self.createMenuBar() 
        self.connectToDevice()
        self.startPlotData()
        #kezelőelem csoportok létrehozása 
        deviceFrame = self.műszerCsatlakozásElemekFelvétele(labelWidth)   
        deviceFrame.setFixedWidth(frameWidth)
        deviceFrame.setMinimumHeight(170)
        frekiFrame = self.frekvenciaElemekFelvétele(labelWidth)
        frekiFrame.setFixedWidth(frameWidth)
        frekiFrame.setMinimumHeight(225)
        traceFrame = self.traceElemekFelvétele(labelWidth)
        traceFrame.setFixedWidth(frameWidth)
        traceFrame.setMinimumHeight(175)
        amplFrame= self.amplitudoElemekFelvétele(labelWidth)
        amplFrame.setFixedWidth(frameWidth)
        amplFrame.setMinimumHeight(140)
        graphFrame = self.graphPlotInit()
        #kezelőelem csoportok gridhez adása, elhelyezése
        fullGrid.addWidget(graphFrame, 0, 1, 4, 1)
        fullGrid.addWidget(deviceFrame, 0, 0)
        fullGrid.addWidget(frekiFrame, 1,0)
        fullGrid.addWidget(traceFrame, 2,0)
        fullGrid.addWidget(amplFrame, 3, 0)
        
        wid.setLayout(fullGrid)
        self.setCentralWidget(wid)
        



        #self.set_tooltips()  még nincs kész

        #Eventek widgethez kötése
        #self.reset_button.clicked.connect(self.send_reset)
        #self.test_connection.clicked.connect(self.send_idn)
        self.set_frequency_button.clicked.connect(self.set_frequency)
        self.clear_frequency_lines.clicked.connect(self.clear_frequency_edit_lines)
        self.trace_1_change.currentIndexChanged.connect(self.trace1_index_changed)
        self.trace_1_change.activated.connect(self.trace1_index_changed)
        self.trace_2_change.currentIndexChanged.connect(self.trace2_index_changed)
        self.trace_2_change.activated.connect(self.trace2_index_changed)
        self.trace_3_change.currentIndexChanged.connect(self.trace3_index_changed)
        self.trace_3_change.activated.connect(self.trace3_index_changed)
        self.set_attenuation_and_scale_button.clicked.connect(self.set_sclae_and_attenuation)
        self.set_attenuation_auto.stateChanged.connect(self.auto_attenuation)    
        self.trace_reset_button.clicked.connect(self.trace_reset)

        self.radiobuttonStartStop.clicked.connect(self.disableCenterSpan)
        self.radiobuttonCenterSpan.clicked.connect(self.disableStartStop)
        self.connectButton.clicked.connect(self.connectToDevice)
        self.plotButton.clicked.connect(self.startPlotData)
        self.saveAction.triggered.connect(self.saveConfig)
        self.resetAction.triggered.connect(self.send_reset)
        #self.resetMenu.addAction(self.resetAction)

    def műszerCsatlakozásElemekFelvétele(self, labelwidth):

        groupbox = QGroupBox(" Műszer csatlakozás ")
        self.ipAddressLabel = QLabel(" Műszer IP-címe", self)
        self.ipAddressEdit = QLineEdit('10.100.16.77', self)        
        self.portLabel = QLabel(" Portszám")
        self.portEdit = QLineEdit('5025', self)
    
        self.connectButton = QPushButton("Csatlakozás a műszerhez", self)
        self.plotButton = QPushButton("Megjelenítés indítása", self)

        grid = QGridLayout()
        grid.addWidget(self.ipAddressLabel, 0, 0)
        grid.addWidget(self.ipAddressEdit, 0, 1)
        grid.addWidget(self.portLabel, 1, 0)
        grid.addWidget(self.portEdit, 1, 1)
        grid.addWidget(self.connectButton, 2, 0, 1, 2)
        grid.addWidget(self.plotButton,3,0,1,2 )

        groupbox.setLayout(grid)
        return groupbox    
    


    def connectToDevice(self):
        ip = "10.100.16.77"
        print(type(ip))
        port = 5025
        self.device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.device.connect((ip, port))
        self.device.send("*IDN?\n\r".encode())
        self.idn=self.device.recv(1024).decode()
        self.setWindowTitle(f"Spektrumanalizátor GUI - {self.idn[:]}")
        print("csatlakozott")
        
        






    def graphPlotInit(self):
            self.graphWidget = pg.PlotWidget()
            self.graphWidget.setTitle("Valós idejű spektrumkép")
            self.graphWidget.setLabel('left', 'Teljesítmény [dBm]')
            self.graphWidget.setLabel('bottom', 'Frekvencia [Hz]')
            self.graphWidget.showGrid(x=True, y=True)
            self.graphWidget.addLegend()
            self.pen1 = pg.mkPen(color=(255, 255, 0), width=2)
            self.pen2 = pg.mkPen(color=(0, 255, 255), width=2)
            self.pen3 = pg.mkPen(color=(255, 0, 255), width=2)
            groupbox = QGroupBox()
            grid = QGridLayout()
            grid.addWidget(self.graphWidget)
            groupbox.setLayout(grid)
            return groupbox
    def startPlotData(self):
          
            self.timer2 =QTimer()
            self.timer2.setInterval(200)
            self.timer2.timeout.connect(self.clearPlotData)
            self.timer2.start()
            self.timer1 = QTimer()
            self.timer1.setInterval(100)
            if(not tesztAllapot): self.timer1.timeout.connect(self.graphPlotData)
            self.timer1.start()
            
            
    def graphPlotData(self):
        '''
        trace adatokat kérése, start-stop meghatározása, plotting
        '''
  

     
        list1 = self.query(1)
    
        self.device.send("FREQ:STAR?\n\r".encode())
        sleep(0.1)
        start = float(self.device.recv(58).decode())
        
        sleep(0.1)
        self.device.send("FREQ:STOP?\n\r".encode())
        sleep(0.1)
        stop = float(self.device.recv(58).decode())

        self.graphWidget.setXRange(start, stop, padding= 0.007 )

        xTengely = numpy.arange(start, stop, (stop-start)/601)
        
        #print(yTengely, len(yTengely))
        #print(xTengely, len(xTengely))
      
 
        # setting cursor to the line1
        
        
    def updatePlotData(self):
            list1 = self.query(1)
                   
            if self.trace_1_change.currentText() == "Blank":
                list1 = []
         
            try:
                self.device.send("*CLS\n\r".encode())
                sleep(0.1)
                self.device.send("FREQ:STAR?\n\r".encode())
                sleep(0.1)
                start = float(self.device.recv(58).decode())
                sleep(0.1)
                self.device.send("FREQ:STOP?\n\r".encode())
                sleep(0.1)
                stop = float(self.device.recv(58).decode())
                
                xTengely = numpy.arange(start, stop, (stop-start)/601)
                yTengely = list
            except:
                print("Start-stop hiba")
           # try:
            #    self.data_line1 =self.graphWidget.plot(xTengely, list1, name = "Trace1",pen = self.pen1)
             #   self.data_line2 =self.graphWidget.plot(xTengely, list2, name = "Trace2", pen = self.pen2)
              #  self.data_line3 =self.graphWidget.plot(xTengely, list3, name = "Trace3", pen = self.pen3)
               # maximum = max(list1,key=lambda x:float(x))
        

            #except:
             #   print('Képfirssítési hiba')

                

    def query(self, number, buffersize = 7846):
        #601 pont belefér a 8192 méretű bufferbe
           try:
            self.device.send(f"TRAC? TRACE{number}\n\r".encode())
            seged = str(self.device.recv(buffersize))
            ido_belyeg = datetime.now()           
            cursor = connection.cursor()
            sql_insert = "INSERT INTO Adatok (ID, Nyers_adat, Időbélyeg, Mérést_végző_felhasználó) VALUES (?, ?, ?, ?)"
            values = (1, seged, ido_belyeg, username)  # Az értékek tuple formában
            cursor.execute(sql_insert, values)
            connection.commit()
            connection.close()        
           except:
            winsound.Beep(frequency, duration)
            os.execl(sys.executable, sys.executable, *sys.argv)


    def clearPlotData(self):
        self.graphWidget.clear()
    def set_tooltips(self):
        
        #self.reset_button.setToolTip("Reseteli a spektrumanalizátort")
        #self.test_connection.setToolTip("Spektrumanalizátor adatainak lekérdezése")
        self.start_frequency_edit.setToolTip("Adj meg egy kezdő frekvenciát mértékegységgel! Pl.: 460MHz (MIN: 3Hz MAX: 26.5GHz)")
        self.stop_frequency_edit.setToolTip("Adj meg egy stop frekvenciát mértékegységgel! Pl.: 3GHz (MAX:26.5GHz)")
        self.center_frequency_edit.setToolTip("Adj meg egy center frekvenciát mértékegységgel! Pl.: 93100KHz")
        self.span_frequency_edit.setToolTip("Adj meg egy span frekvenciát mértékegységgel! Pl.: 150MHz (MIN: 100Hz MAX: 13.25GHz)")
        self.clear_frequency_lines.setToolTip("Törli a frekvencia megadására szolgáló sorok tartalmát.")
        self.set_frequency_button.setToolTip("Először a törlés gombbal állítsd alaphelyzetbe a frekvencia megadására szolgáló sorokat, majd adj meg egy start-stop vagy center-span párost.")
        self.set_attenuation_and_scale_button.setToolTip("Beállítja a megadott Scale és Attenuaition értéket")
    
  
    def frekvenciaElemekFelvétele(self, labelWidth):
        
        self.start_frequency_edit=QLineEdit(self) #start freki megadása pl.: 460MHz
        #self.start_frequency_edit.setFixedWidth(labelWidth)
        self.stop_frequency_edit=QLineEdit(self)  #
        #self.stop_frequency_edit.setFixedWidth(labelWidth)
        self.center_frequency_edit=QLineEdit(self)
        self.center_frequency_edit.setDisabled(True)
        #self.center_frequency_edit.setFixedWidth(labelWidth)
        self.span_frequency_edit=QLineEdit(self)
        self.span_frequency_edit.setDisabled(True)
        #self.span_frequency_edit.setFixedWidth(labelWidth)
        self.set_frequency_button=QPushButton('Frekvencia beállítása', self)  #gomb megnyomásával beolvassa az előző 4 sor adatait, és beállítja az alapján a kívánt értékeket, majd a gépből visszaolvassa, és feltölti a sorokat
        self.clear_frequency_lines=QPushButton("Hozzáadás", self) # gomb megnyomása törli az előző 4 LineEdit widget tartalmát
        self.start_frequency_label=QLabel(" Start", self)
        #self.start_frequency_label.setFixedWidth(labelWidth)
        self.stop_frequency_label=QLabel(" Stop",self)
        #self.stop_frequency_label.setFixedWidth(labelWidth)
        self.center_frequency_label=QLabel(" Határérték", self)
        #self.center_frequency_label.setFixedWidth(labelWidth)
        self.span_frequency_label=QLabel(" Email cím", self)
        #self.span_frequency_label.setFixedWidth(labelWidth)
        mertekegységek= ['HZ', 'kHz', 'MHz', 'GHz', 'dBm']
        self.radiobuttonStartStop = QRadioButton(self)
        self.radiobuttonStartStop.setChecked(True)
        self.radiobuttonCenterSpan = QRadioButton(self)
        self.mertekegysegSTAR = QComboBox(self)
        self.mertekegysegSTAR.addItems(mertekegységek)
        self.mertekegysegSTAR.setCurrentIndex(2)
        self.mertekegysegSTOP = QComboBox(self)
        self.mertekegysegSTOP.addItems(mertekegységek)
        self.mertekegysegSTOP.setCurrentIndex(2)
        self.mertekegysegCENT = QComboBox(self)
        self.mertekegysegCENT.addItems(mertekegységek)
        self.mertekegysegCENT.setCurrentIndex(2)
        self.mertekegysegSPAN = QComboBox(self)
        self.mertekegysegSPAN.setDisabled(True)
        self.mertekegysegSPAN.addItems(mertekegységek)
        self.mertekegysegSPAN.setCurrentIndex(2)
        self.mertekegysegCENT.setDisabled(True)

        groupbox=QGroupBox(" Határérték beállítások ")
        frekigrid=QGridLayout()
        frekigrid.addWidget(self.radiobuttonStartStop, 0, 0, 2,1)
        frekigrid.addWidget(self.radiobuttonCenterSpan, 2, 0, 2, 1)
        frekigrid.addWidget(self.mertekegysegSTAR, 0, 4)
        frekigrid.addWidget(self.mertekegysegSTOP, 1, 4)
        frekigrid.addWidget(self.mertekegysegCENT, 2, 4)
        frekigrid.addWidget(self.mertekegysegSPAN, 3, 4)
        frekigrid.addWidget(self.start_frequency_label, 0,1)
        frekigrid.addWidget(self.stop_frequency_label, 1, 1)
        frekigrid.addWidget(self.center_frequency_label, 2, 1)
        frekigrid.addWidget(self.span_frequency_label, 3, 1)
        frekigrid.addWidget(self.start_frequency_edit, 0, 2)
        frekigrid.addWidget(self.stop_frequency_edit, 1, 2)
        frekigrid.addWidget(self.center_frequency_edit, 2, 2)
        frekigrid.addWidget(self.span_frequency_edit, 3, 2)
        frekigrid.addWidget(self.clear_frequency_lines, 4, 0, 1, 2)
        frekigrid.addWidget(self.set_frequency_button, 4, 2, 1,3)
        
        groupbox.setLayout(frekigrid)
        return groupbox
    
    
    def traceElemekFelvétele(self, labelWidth):
        self.trace_1_label=QLabel(" Trace 1", self)
        self.trace_1_label.setFixedWidth(50)
        self.trace_2_label=QLabel(" Trace 2", self)
        self.trace_2_label.setFixedWidth(50)
        self.trace_3_label=QLabel(" Trace 3", self)
        self.trace_3_label.setFixedWidth(50)
        self.trace_1_change=QComboBox(self)  #ide még be kell állítani a 4 választást
        self.trace_1_change.addItems(["Clear Write", "Max Hold", "Min hold", "View", "Blank"])
        self.trace_2_change=QComboBox(self)
        self.trace_2_change.addItems(["Blank","Clear Write", "Max Hold", "Min hold", "View"])
        self.trace_3_change=QComboBox(self)
        self.trace_3_change.addItems(["Blank","Clear Write", "Max Hold", "Min hold", "View"])
        self.trace_reset_button=QPushButton("Alaphelyzet", self)  #Trace alaphelyzetbe állítása: WRIT, BLAN, BLAN

        groupbox = QGroupBox(" Trace beállítások ")
        traceGrid = QGridLayout()
        
        traceGrid.addWidget(self.trace_1_label, 0,0)
        traceGrid.addWidget(self.trace_2_label, 1, 0)
        traceGrid.addWidget(self.trace_3_label, 2,0)
        traceGrid.addWidget(self.trace_reset_button, 3, 0, 1, 2)
        traceGrid.addWidget(self.trace_1_change, 0, 1)
        traceGrid.addWidget(self.trace_2_change, 1, 1)
        traceGrid.addWidget(self.trace_3_change, 2, 1)
        
        groupbox.setLayout(traceGrid)
        return groupbox
        
    def amplitudoElemekFelvétele(self, labelWidth):
        self.scale_label=QLabel(" Scale", self)
        self.scale_label_mert=QLabel(" dB", self)
        self.scale_label_mert.setStyleSheet("""QLabel{font-size: 12px; color: orange; border-left: 0px solid orange;}""")
        self.scale_edit=QLineEdit(self)
        self.attenuation_label=QLabel(" Csillapítás")
        self.attenuation_label_mert=QLabel(" dB", self)
        self.attenuation_label_mert.setStyleSheet("""QLabel{font-size: 12px; color: orange; border-left: 0px solid orange;}""")
        #self.attenuation_auto_label("AUTO")  kell ez egyáltalán? vagy tudok a pipának nevet adni????
        self.attenuation_edit=QLineEdit(self)
        self.set_attenuation_and_scale_button=QPushButton("Beállít", self )
        self.set_attenuation_auto=QCheckBox("Auto", self)
        self.set_attenuation_auto.setChecked(True)
        
        groupbox = QGroupBox(" Amplitúdó beállítások ")
        amplGrid = QGridLayout()
        
        amplGrid.addWidget(self.scale_label, 0, 0)
        amplGrid.addWidget(self.scale_edit, 0, 1, 1, 2)
        amplGrid.addWidget(self.scale_label_mert, 0, 3)
        amplGrid.addWidget(self.attenuation_label, 1, 0)
        amplGrid.addWidget(self.set_attenuation_auto, 1, 1)
        amplGrid.addWidget(self.attenuation_edit, 1, 2)
        amplGrid.addWidget(self.attenuation_label_mert, 1, 3)
        amplGrid.addWidget(self.set_attenuation_and_scale_button, 2, 0, 1, 4)
        
        groupbox.setLayout(amplGrid)
        return groupbox

    def createMenuBar(self):
        menuBar = self.menuBar()
        fileMenu = QMenu("Fájl", self)
        self.saveAction = QAction()
        self.saveAction.setObjectName("saveAction")
        self.saveAction.setText('Mentés')
        self.saveAction.setShortcut("Ctrl+S")
        fileMenu.addAction(self.saveAction)
        menuBar.addMenu(fileMenu) 

        toolMenu = QMenu("Eszközök", self)
        self.resetAction = QAction()
        self.resetAction.setObjectName("resetAction")
        self.resetAction.setText('Műszer alaphelyzetbe állítása')
        self.resetAction.setShortcut("Ctrl+Shift+S")
        toolMenu.addAction(self.resetAction)
        menuBar.addMenu(toolMenu) 
        
        
        infoMenu = QMenu("Információ", self)
        menuBar.addMenu(infoMenu)
        
        
    def set_frequency(self):  #start-stop vagy center-span párost fogad csak el.
        start=self.start_frequency_edit.text()
        stop=self.stop_frequency_edit.text()
        center=self.center_frequency_edit.text()
        span=self.span_frequency_edit.text()
        startMérték=self.mertekegysegSTAR.currentText()
        stopMérték=self.mertekegysegSTOP.currentText()
        centerMérték=self.mertekegysegCENT.currentText()
        spanMérték=self.mertekegysegSPAN.currentText()
        
        if self.radiobuttonStartStop.isChecked():
            self.device.send(f"FREQ:STAR {start}{startMérték}\n\r".encode())
            sleep(0.1)
            self.device.send(f"FREQ:STOP {stop}{stopMérték}\n\r".encode())
            sleep(0.1)
            
        elif self.radiobuttonCenterSpan.isChecked():
            self.device.send(f"FREQ:CENT {center}{centerMérték}\n\r".encode())
            sleep(0.1)
            self.device.send(f"FREQ:SPAN {span}{spanMérték}\n\r".encode())
            sleep(0.1)

    def clear_frequency_edit_lines(self):
        self.start_frequency_edit.clear()
        self.stop_frequency_edit.clear()
        self.center_frequency_edit.clear()
        self.span_frequency_edit.clear()
    def saveConfig(self):
        print("Mentve lenne ha meg lenne írva")  #HOLNAP
    def send_reset(self):
        self.device.send("*RST\n\r".encode())
    def send_idn(self):
        self.device.send("*IDN?\n\r".encode())
        sleep(0.1)
        answer=self.device.recv(1024).decode()
        self.test_connection.setText(f"Szia! én az {answer[:-1]} nevű gépe vagyok.")
    
    def trace1_index_changed(self, index):
        if index == 0:
            self.device.send("TRAC1:MODE WRIT\n\r".encode())
        elif index== 1:
            self.device.send("TRAC1:MODE MAXH\n\r".encode())
        elif index == 2:
            self.device.send("TRAC1:MODE MINH\n\r".encode())
        elif index==3:
            self.device.send("TRAC1:MODE VIEW\n\r".encode())
        else:
            self.device.send("TRAC1:MODE BLAN\n\r".encode())
        
    def trace2_index_changed(self, index):
        if index == 0:
            self.device.send("TRAC2:MODE BLAN\n\r".encode())
        elif index== 1:
            self.device.send("TRAC2:MODE WRIT\n\r".encode())
        elif index == 2:
            self.device.send("TRAC2:MODE MAXH\n\r".encode())
        elif index==3:
            self.device.send("TRAC2:MODE MINH\n\r".encode())
        else:
            self.device.send("TRAC2:MODE VIEW\n\r".encode())
            
    def trace3_index_changed(self, index):
        if index == 0:
            self.device.send("TRAC3:MODE BLAN\n\r".encode())
        elif index== 1:
            self.device.send("TRAC3:MODE WRIT\n\r".encode())
        elif index == 2:
            self.device.send("TRAC3:MODE MAXH\n\r".encode())
        elif index==3:
            self.device.send("TRAC3:MODE MINH\n\r".encode())
        else:
            self.device.send("TRAC3:MODE VIEW\n\r".encode())
            
    def set_sclae_and_attenuation(self):
        scale = self.scale_edit.text()
        self.device.send(f"DISP:WIND:TRAC:Y:SCAL:PDIV {scale}\n\r".encode())
        att = self.attenuation_edit.text()
        if len(att)==0:
            self.set_attenuation_auto.setChecked(True)
        else:
            self.set_attenuation_auto.setChecked(False)
            self.device.send(f"POW:ATT {att}\n\r".encode()) 
    
    def auto_attenuation (self, tick):
        if tick == 2:
            self.device.send(f"POW:ATT:AUTO ON\n\r".encode()) 
            import smtplib
            email_address ="mandras2001@gmail.com"
            password = "jelszo"
            msg = ""

            with smtplib.SMTP('smtp.gmail.com',587) as server:
             server.starttls()
            server.login(email_address, password)
            server.send_message(msg)
    
        elif tick == 0:
            self.device.send(f"POW:ATT:AUTO OFF\n\r".encode()) 
            att=self.attenuation_edit.text()
            self.device.send(f"POW:ATT {att}\n\r".encode())
        
    def trace_reset(self):
        self.trace_1_change.setCurrentIndex(0)
        self.device.send("TRAC1:MODE WRIT\n\r".encode())
        sleep(0.1)
        self.trace_3_change.setCurrentIndex(0)
        self.device.send("TRAC2:MODE BLAN\n\r".encode())
        sleep(0.1)
        self.trace_2_change.setCurrentIndex(0)
        self.device.send("TRAC3:MODE BLAN\n\r".encode())

    def disableStartStop(self, active):
        if active == True:
            self.start_frequency_edit.setDisabled(True)
            self.stop_frequency_edit.setDisabled(True)
            self.center_frequency_edit.setDisabled(False)
            self.span_frequency_edit.setDisabled(False)
            self.mertekegysegSTAR.setDisabled(True)
            self.mertekegysegSTOP.setDisabled(True)
            self.mertekegysegCENT.setDisabled(False)
            self.mertekegysegSPAN.setDisabled(False)
        else:
            pass
    
    def disableCenterSpan(self, active):
        if active == True:
            self.start_frequency_edit.setDisabled(False)
            self.stop_frequency_edit.setDisabled(False)
            self.center_frequency_edit.setDisabled(True)
            self.span_frequency_edit.setDisabled(True)
            self.mertekegysegSTAR.setDisabled(False)
            self.mertekegysegSTOP.setDisabled(False)
            self.mertekegysegSPAN.setDisabled(True)
            self.mertekegysegCENT.setDisabled(True)

    
def main():
 
    app = QApplication(sys.argv)
    ablak=Window()
    
    style = ("""
        QWidget{
            background-color: #202020;
        }
        QComboBox{
            border: 3px solid orange;
            border-top-left-radius: 10px;
            background: #202020;
            padding: 1px 23px 1px 3px;
            min-width: 6em;
            color: orange;
            font-size: 12px;
        }
        QComboBox::disabled{
            border-color: 3px solid #404040;
            background-color: #202020;
            color: #404040;  
        }
        QComboBox:hover{
            border-color: chocolate;
        }

        QListView {
            background-color: #202020;
            color: orange;
        }
        QLineEdit{
            border: 3px solid orange;
            color: orange;
            border-top-left-radius: 10px;
            border-bottom-right-radius: 10px;
            font-size: 12px;
        }
        QLineEdit::disabled{
            border: 3px solid #404040;
            color: orange;
            border-top-left-radius: 10px;
            border-bottom-right-radius: 10px;
            font-size: 12px;
        }
        QCheckBox{
            color: orange;
            font-size: 12px;
        }
        QCheckBox::indicator:checked {
            background-color: orange;
            border-style: solid;
        }


        QCheckBox::indicator:unchecked {
            background-color: #202020;
            border-color: orange;
            border-style: solid;
            border-width: 2;
        }

        QCheckBox::disabled{
            color: #404040;
        }
        QCheckBox::indicator:disabled {
            background-color: #202020;
            border-color: #404040;
            border-style: solid;
        }
        QMenu{
            color: orange;
        }
        QMenu::item:selected{
            color: chocolate;
            background-color: #202020;
        }
        QMenuBar{
            background-color: transparent;
            color: orange;
        }
        QMenuBar::item:selected{
            color: chocolate;
            background-color: #202020;
        }
        QMenuBar::item:pressed{
            color: chocolate;
            background-color: #404040;
        }
        QAction{
            color: red;
        }
        
        QRadioButton::indicator:checked {
            background-color: orange;
            border-style: solid;
            border-radius: 10px;

        }

        QRadioButton::indicator:unchecked {
            background-color: #202020;
            border-color: orange;
            border-style: solid;
            border-width: 2;
            border-radius: 10px;
        }
        QRadioButton:unchecked{
            color: black;
        }
        QPushButton{
            background-color: orange;
            min-height: 20px;
            max-height: 20px;
            border-style: outset;
            border-radius: 10px;
            font-size: 12px;
        }
        QPushButton:hover{
            background-color: chocolate;
            color: white;
        }
        QPushButton:pressed{
            background-color: #ffcc99;
            color: #202020;
        }
        QLabel{
            color: orange;
            font-size: 12px;
            border-left: 1px solid orange;
        }
        QGroupBox{
            color: orange;
            font-size: 14px;
            border: 1px solid orange;
            border-radius: 10px;
        }
        QGroupBox::title{
            color: rgb(255, 255, 255);
            subcontrol-origin: margin;
            border-top-left-radius: 10px;
            border-bottom-right-radius: 10px;
            background-color: orange;
            color: black;
            }
        
    """)
    ablak.setStyleSheet(style)
    ablak.showMaximized()
    ablak.show()
    sys.exit(app.exec())
main()

