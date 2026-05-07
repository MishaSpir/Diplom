import sys
from PyQt5.QtWidgets import QApplication, QWidget  
from PyQt5 import uic, QtCore
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo  
from PyQt5.QtCore import QIODevice
from pyqtgraph import PlotWidget
import pyqtgraph as pg

update_counter = 0
GRAPH_UPDATE_INTERVAL = 100  # Обновлять график каждые 100 значений
buffer = ""  # Глобальный буфер для неполных строк
flag  = True  

listX = []
for x in range(100):
    listX.append(x)
listY = []
for y in range(100):
    listY.append(0)    

listX2 = []
for x2 in range(100):
    listX2.append(x2)
listY2 = []
for y2 in range(100):
    listY2.append(y2)
       

if __name__ == '__main__':
    # Объект приложения
    app = QApplication(sys.argv)
    # интерфейс 
    # ui = uic.loadUi("design.ui")
    ui = uic.loadUi("design_2_graph.ui")
    ui.setWindowTitle("Serial GUI")
    
    # Объект порта
    serial = QSerialPort()
    serial.setBaudRate(115200)
    portList = []
    ports = QSerialPortInfo().availablePorts()
    for port in ports:
        portList.append(port.portName())
    print(portList)

    # добавляем в ГУЙ в ComList список портов
    ui.ComList.addItems(portList)
    def test():
        print("test")

    def OnOpen():
        gui_port_name = ui.ComList.currentText()
        if not gui_port_name:
            print("No COMs are available")
            return
        
        serial.setPortName(gui_port_name)
        if serial.open(QIODevice.ReadWrite):
            print("OnOpen",ui.ComList.currentText())
        else: 
            print("Can`t open the port")    

    def OnClose():
        serial.close()
        print("OnClose",ui.ComList.currentText())   


    def RefreshGraph2():
        global flag
        # flag = True
        print("refresh")
        flag = True          
    
    def OnRead():
        global buffer
        global update_counter

        while serial.bytesAvailable():
            # Читаем ВСЕ доступные данные как байты
            data = serial.readAll()
            # Декодируем и добавляем в буфер
            buffer += str(data, 'latin-1')

            # Разбиваем по '\n' и обрабатываем только полные строки
            lines = buffer.split('\n')

            # Последний элемент - неполная строка (если нет '\n' в конце)
            buffer = lines[-1]

            # Обрабатываем все полные строки
            for line in lines[:-1]:
                line = line.strip()
                if line:  # Не пустая строка
                    try:
                        value = int(line)
                        # Обновляем GUI
                        ui.progressBar.setValue(value)
                        ui.adcLbl.setText(str(value))
                        print(value)  # Теперь будет правильно!

                        # Обновляем график 
                        global update_counter, listY, listY2,flag
                        listY.append(value)
                        listY.pop(0)
                        update_counter += 1
                        if update_counter >= GRAPH_UPDATE_INTERVAL:
                            update_counter = 0
                            listY = listY[1:]
                            listY.append(value)
                            # print(listY)
                            ui.graph.clear()
                            ui.graph.plot(listX,listY,pen=pen)
                            if flag:
                                listY2 = listY
                                ui.graph2.clear()
                                ui.graph2.plot(listX,listY2,pen=pen)
                                flag = False
                        
                    except ValueError:
                     print(f"Ошибка преобразования: {line}")
        # # Читаем ВСЕ доступные данные, а не одну строку
        # while serial.bytesAvailable():
        #     rx = serial.readLine()
        #     if rx:  # Если есть данные
        #         try:
        #             rxstr = str(rx, 'latin-1').strip()
        #             if rxstr:  # Не обрабатываем пустые строки
        #                 value = int(rxstr)
        #                 ui.progressBar.setValue(value)
        #                 ui.adcLbl.setText(rxstr)

        #                 # Обновляем график (но не каждые 10 мс!)
        #                 # update_graph(value)
        #                 print(value)
        #                 # ui.adcLbl.setText(rxstr)
        #                 global listY
        #                 global listX
        #                 # listY = listY[1:]
        #                 # listY.append(value)
        #                 # # print(listY)
        #                 # ui.graph.clear()
        #                 # ui.graph.plot(listX,listY,pen=pen)
        #                 update_counter +=1
        #                 if update_counter >= GRAPH_UPDATE_INTERVAL:
        #                     update_counter = 0
        #                     listY = listY[1:]
        #                     listY.append(value)
        #                     # print(listY)
        #                     ui.graph.clear()
        #                     ui.graph.plot(listX,listY,pen=pen)
        #         except ValueError:
        #             pass  # Игнорируем нечисловые данные    
         
            

    serial.readyRead.connect(OnRead) #когда пришли данные вызовится фунукция OnRead
    ui.ComList.currentIndexChanged.connect(test)
    ui.openBtn.clicked.connect(OnOpen)
    ui.closeBtn.clicked.connect(OnClose)
    ui.rfrshBtn.clicked.connect(RefreshGraph2)

    # plot_graph = pg.PlotWidget()
    # ui.graph.setCentralWidget(plot_graph)
    ui.graph.setBackground("w")
    # pen = pg.mkPen(color=(255, 0, 0))
    pen = pg.mkPen(color=(0, 0, 255), width=2, style=QtCore.Qt.DashLine)
    ui.graph.showGrid(x=True, y=True)
    ui.graph.plot(listX,listY,pen=pen)

    #Для второго графика 
    ui.graph2.setBackground("w")
    # pen = pg.mkPen(color=(255, 0, 0))
    pen2 = pg.mkPen(color=(0, 0, 255), width=2, style=QtCore.Qt.DashLine)
    ui.graph2.showGrid(x=True, y=True)
    ui.graph2.plot(listX2,listY2,pen=pen)



    ui.show()
    sys.exit(app.exec_()) 