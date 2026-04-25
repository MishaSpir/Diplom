import sys
from PyQt5.QtWidgets import QApplication, QWidget  
from PyQt5 import uic  
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo  
from PyQt5.QtCore import QIODevice



if __name__ == '__main__':
    # Объект приложения
    app = QApplication(sys.argv)
    # интерфейс 
    ui = uic.loadUi("design.ui")
    ui.setWindowTitle("Serial GUI")
    
    # Объект порта
    serial = QSerialPort()
    serial.setBaudRate(115200)
    portList = []
    ports = QSerialPortInfo().availablePorts()
    for port in ports:
        portList.append(port.portName())
    print(portList)

    ui.ComList.addItems(portList)
    def test():
        print("test")

    def OnOpen():
        serial.setPortName(ui.ComList.currentText())
        serial.open(QIODevice.ReadWrite)
        print("OnOpen",ui.ComList.currentText())

    def OnClose():
        serial.close()
        print("OnClose",ui.ComList.currentText())   

    def OnRead():
        rx = serial.readLine()
        rxstr = str(rx,'utf-8').strip()
        print(rxstr)     

    serial.readyRead.connect(OnRead) #когда пришли данные вызовится фунукция OnRead
    ui.ComList.currentIndexChanged.connect(test)
    ui.openBtn.clicked.connect(OnOpen)
    ui.closeBtn.clicked.connect(OnClose)




    ui.show()
    sys.exit(app.exec_()) 