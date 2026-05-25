import sys
from PyQt5.QtWidgets import QApplication
from PyQt5 import uic
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo  
from PyQt5.QtCore import QIODevice, QTimer
import pyqtgraph as pg
import numpy as np

# Константы
GRAPH_LENGTH_POINTS = 100
UPDATE_INTERVAL_MS = 30  # Обновление ~33 fps
MAX_PENDING = 1000  # Максимум накопленных данных

buffer = bytearray()
listX = np.arange(GRAPH_LENGTH_POINTS, dtype=np.float64)
listY = np.zeros(GRAPH_LENGTH_POINTS, dtype=np.float64)
pending_data = []
graph_timer = None  # Глобальная переменная

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = uic.loadUi("design_2_graph.ui")
    ui.setWindowTitle("Serial GUI")
    
    # Настройка порта
    serial = QSerialPort()
    serial.setBaudRate(1000000)
    
    portList = [port.portName() for port in QSerialPortInfo().availablePorts()]
    ui.ComList.addItems(portList)
    
    # Настройка графика
    ui.graph.setBackground("w")
    pen = pg.mkPen(color=(0, 0, 255), width=2)
    ui.graph.showGrid(x=True, y=True)
    curve = ui.graph.plot(listX, listY, pen=pen)
    
    def update_graph():
        """Быстрое обновление графика"""
        global pending_data, listY, curve
        
        if pending_data:
            n_new = len(pending_data)
            if n_new >= GRAPH_LENGTH_POINTS:
                listY = np.array(pending_data[-GRAPH_LENGTH_POINTS:])
            else:
                listY = np.roll(listY, -n_new)
                listY[-n_new:] = pending_data
            
            pending_data = []
            curve.setData(listX, listY)
    
    def OnRead():
        global buffer, pending_data, curve
        
        while serial.bytesAvailable():
            data = serial.readAll()
            buffer.extend(data)
            
            i = 0
            while i < len(buffer):
                # Поиск пакета (4 байта данных + 0x0A)
                if i + 4 < len(buffer) and buffer[i+4] == 0x0A:
                    packet = buffer[i:i+4]
                    buffer = buffer[i+5:]  # Удаляем пакет и терминатор
                    
                    if len(packet) >= 4:
                        adc_1 = (packet[0] << 8) | packet[1]
                        pending_data.append(float(adc_1))
                        
                        # Если накопилось много данных, обновляем график
                        if len(pending_data) >= MAX_PENDING:
                            update_graph()
                    
                    i = 0
                else:
                    i += 1
            
            # Защита от переполнения
            if len(buffer) > 5000:
                buffer = buffer[-5000:]
    
    def OnOpen():
        global graph_timer
        
        gui_port_name = ui.ComList.currentText()
        if not gui_port_name:
            print("No COMs are available")
            return
        
        serial.setPortName(gui_port_name)
        if serial.open(QIODevice.ReadWrite):
            print(f"Opened {gui_port_name}")
            # Запускаем таймер обновления
            if graph_timer is None:
                graph_timer = QTimer()
                graph_timer.timeout.connect(update_graph)
                graph_timer.start(UPDATE_INTERVAL_MS)
        else:
            print("Can't open the port")
    
    def OnClose():
        global graph_timer
        
        if graph_timer:
            graph_timer.stop()
            graph_timer = None
        serial.close()
        print("Port closed")
    
    # Подключение сигналов
    serial.readyRead.connect(OnRead)
    ui.openBtn.clicked.connect(OnOpen)
    ui.closeBtn.clicked.connect(OnClose)
    
    ui.show()
    sys.exit(app.exec_())