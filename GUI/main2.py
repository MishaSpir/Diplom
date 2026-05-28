import sys
from PyQt5.QtWidgets import QApplication
from PyQt5 import uic
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo  
from PyQt5.QtCore import QIODevice, QTimer
import pyqtgraph as pg
import numpy as np
from scipy import signal
import time

# Константы
GRAPH_LENGTH_POINTS = 1000
UPDATE_INTERVAL_MS = 1000
MAX_PENDING = 100

# Параметры фильтра
CUTOFF_FREQ = 200
SAMPLING_RATE = 10000

buffer = bytearray()
listX = np.arange(GRAPH_LENGTH_POINTS, dtype=np.int32)  # int для X (индексы)
listY_raw = np.zeros(GRAPH_LENGTH_POINTS, dtype=np.int32)  # int для АЦП
listY_filtered = np.zeros(GRAPH_LENGTH_POINTS, dtype=np.float64)  # float ТОЛЬКО для фильтра
listY2 = np.zeros(GRAPH_LENGTH_POINTS, dtype=np.int32)  # int для второго канала

pending_data_raw = []  # Храним как int
pending_data2 = []     # Храним как int

graph_timer = None

OnPlot2_flag = False
OnPlot2Filter_flag = False

def init_lowpass_filter(cutoff_freq, sampling_rate, order=2):
    """Инициализация LOWPASS фильтра Баттерворта"""
    nyquist = sampling_rate / 2
    normalized_cutoff = cutoff_freq / nyquist
    
    if normalized_cutoff >= 1.0:
        print(f"Предупреждение: частота среза {cutoff_freq} Гц слишком высока")
        print(f"Устанавливаю {nyquist * 0.9} Гц")
        normalized_cutoff = 0.9
    
    b, a = signal.butter(order, normalized_cutoff, btype='low')
    zi = signal.lfilter_zi(b, a) * 0
    
    return b, a, zi

# Инициализируем фильтр
b, a, filter_state = init_lowpass_filter(CUTOFF_FREQ, SAMPLING_RATE, order=4)

def apply_lowpass_filter(data_point):
    """Применяет LOWPASS фильтр к одному значению (int -> float)"""
    global filter_state, b, a
    # Фильтр работает с float, поэтому преобразуем
    filtered, filter_state = signal.lfilter(b, a, [float(data_point)], zi=filter_state)
    return filtered[0]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = uic.loadUi("design_main2.ui")
    ui.setWindowTitle("Serial GUI")
    
    # Настройка порта
    serial = QSerialPort()
    serial.setBaudRate(1000000)
    
    portList = [port.portName() for port in QSerialPortInfo().availablePorts()]
    ui.ComList.addItems(portList)
    
    # НАСТРОЙКА НИЖНЕГО ГРАФИКА (graph2) - оба сигнала
    ui.graph2.setBackground("w")
    ui.graph2.showGrid(x=True, y=True)
    ui.graph2.setLabel('left', 'Сигналы', units='ADC')
    ui.graph2.setLabel('bottom', 'Отсчеты')
    ui.graph2.setTitle('Сравнение сигналов: СИНИЙ - фильтрованный, КРАСНЫЙ - сырой')
    
    # Линия для ФИЛЬТРОВАННОГО сигнала (синяя) - float значения
    pen_filtered = pg.mkPen(color=(0, 0, 255), width=5)
    curve_filtered = ui.graph2.plot(listX, listY_filtered, pen=pen_filtered)
    
    # Линия для СЫРОГО сигнала (красная) - int значения
    pen_raw = pg.mkPen(color=(255, 0, 0), width=0.5)
    curve_raw = ui.graph2.plot(listX, listY_raw, pen=pen_raw)
    
    # НАСТРОЙКА ВЕРХНЕГО ГРАФИКА (graph) - второй канал
    ui.graph.setBackground("w")
    pen2 = pg.mkPen(color=(0, 255, 0), width=2)
    ui.graph.showGrid(x=True, y=True)
    ui.graph.setLabel('left', 'Канал 2', units='ADC')
    ui.graph.setLabel('bottom', 'Отсчеты')
    ui.graph.setTitle('Второй канал (без фильтра)')
    curve2 = ui.graph.plot(listX, listY2, pen=pen2)
    
    # Для отладки
    update_count = 0
    last_time = time.time()
    
    def update_graph():
        """Обновление графиков"""
        global pending_data_raw, pending_data2, listY_raw, listY_filtered, listY2
        global update_count, last_time, filter_state
        
        has_data = False
        
        # Обработка данных для первого канала (с фильтром)
        if pending_data_raw:
            n_new = len(pending_data_raw)
            
            # Применяем фильтр к каждому новому значению
            filtered_values = []
            for value in pending_data_raw:
                filtered_val = apply_lowpass_filter(value)  # value уже int
                filtered_values.append(filtered_val)
            
            # Обновляем массив сырых данных (int)
            if n_new >= GRAPH_LENGTH_POINTS:
                listY_raw = np.array(pending_data_raw[-GRAPH_LENGTH_POINTS:], dtype=np.int32)
                listY_filtered = np.array(filtered_values[-GRAPH_LENGTH_POINTS:], dtype=np.float64)
            else:
                listY_raw = np.roll(listY_raw, -n_new)
                listY_raw[-n_new:] = pending_data_raw
                listY_filtered = np.roll(listY_filtered, -n_new)
                listY_filtered[-n_new:] = filtered_values
            
            pending_data_raw = []
            has_data = True
     
        # Обработка второго канала (без фильтра) - int
        if pending_data2:
            n_new = len(pending_data2)
            if n_new >= GRAPH_LENGTH_POINTS:
                listY2 = np.array(pending_data2[-GRAPH_LENGTH_POINTS:], dtype=np.int32)
            else:
                listY2 = np.roll(listY2, -n_new)
                listY2[-n_new:] = pending_data2
            pending_data2 = []
            has_data = True
        
        # Обновляем отображение
        if has_data:
            if(OnPlot2_flag):
                curve_raw.setData(listX, listY_raw)
            else:
                curve_raw.setData([], [])
            if(OnPlot2Filter_flag):
                curve_filtered.setData(listX, listY_filtered)    
            else:
                curve_filtered.setData([], [])
            curve2.setData(listX, listY2)
            
            update_count += 1
            if time.time() - last_time >= 1.0:
                print(f"Обновлений/сек: {update_count}, точек в буфере: {len(pending_data_raw)}")
                update_count = 0
                last_time = time.time()
    
    def OnRead():
        global buffer, pending_data_raw, pending_data2
        
        while serial.bytesAvailable():
            data = serial.readAll()
            buffer.extend(data)
            
            i = 0
            while i < len(buffer):
                if i + 4 < len(buffer) and buffer[i+4] == 0x0A:
                    packet = buffer[i:i+4]
                    buffer = buffer[i+5:]
                    
                    if len(packet) >= 4:
                        # Читаем как int (без преобразования в float)
                        adc_1 = (packet[0] << 8) | packet[1]
                        adc_2 = (packet[2] << 8) | packet[3]
                        
                        # Сохраняем как int
                        pending_data_raw.append(adc_1)
                        pending_data2.append(adc_2)
                    
                    i = 0
                else:
                    i += 1
            
            if len(buffer) > 5000:
                buffer = buffer[-5000:]
    
    def OnOpen():
        global graph_timer, filter_state
        
        gui_port_name = ui.ComList.currentText()
        if not gui_port_name:
            print("No COMs are available")
            return
        
        serial.setPortName(gui_port_name)
        if serial.open(QIODevice.ReadWrite):
            print(f"Opened {gui_port_name}")
            print(f"Фильтр LOWPASS: частота среза = {CUTOFF_FREQ} Гц")
            print(f"Частота дискретизации = {SAMPLING_RATE} Гц")
            print(f"Тип данных АЦП: 16-битные целые числа (0-65535)")
            
            # Сбрасываем состояние фильтра при открытии
            _, _, filter_state = init_lowpass_filter(CUTOFF_FREQ, SAMPLING_RATE, order=4)
            
            if graph_timer is None:
                graph_timer = QTimer()
                graph_timer.timeout.connect(update_graph)
                graph_timer.start(UPDATE_INTERVAL_MS)
                print(f"Таймер запущен, интервал {UPDATE_INTERVAL_MS} мс")
        else:
            print("Can't open the port")
    
    def OnClose():
        global graph_timer
        
        if graph_timer:
            graph_timer.stop()
            graph_timer = None
        serial.close()
        print("Port closed")

    def OnPlot2():
        global OnPlot2_flag
        OnPlot2_flag = not OnPlot2_flag

    def OnPlot2Filter():
        global OnPlot2Filter_flag
        OnPlot2Filter_flag = not OnPlot2Filter_flag        
    
    # Подключение сигналов
    serial.readyRead.connect(OnRead)
    ui.openBtn.clicked.connect(OnOpen)
    ui.closeBtn.clicked.connect(OnClose)

    ui.gaph2_on.clicked.connect(OnPlot2)
    ui.graph2_filter_on.clicked.connect(OnPlot2Filter) 
    
    ui.show()
    sys.exit(app.exec_())