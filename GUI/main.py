import sys
from PyQt5.QtWidgets import QApplication, QWidget  
from PyQt5 import uic, QtCore
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo  
from PyQt5.QtCore import QIODevice
from pyqtgraph import PlotWidget
import pyqtgraph as pg

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

update_counter = 0
GRAPH_UPDATE_INTERVAL = 100  # Обновлять график каждые 100 значений
GRAPH_LENGTH_POINTS = 200
buffer = ""  # Глобальный буфер для неполных строк
flag  = True  

listX = []
for x in range(GRAPH_LENGTH_POINTS):
    listX.append(x)
listY = []
for y in range(GRAPH_LENGTH_POINTS):
    listY.append(0)    

listX2 = []
for x2 in range(GRAPH_LENGTH_POINTS):
    listX2.append(x2)
listY2 = []
for y2 in range(GRAPH_LENGTH_POINTS):
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


  

    def apply_lowpass_filter(data, cutoff_freq, sampling_rate, filter_type='butter', order=2):
        """
        Применяет Low-Pass фильтр к данным.

        Параметры:
        - data: входной сигнал (массив NumPy или список)
        - cutoff_freq: частота среза фильтра (в Гц)
        - sampling_rate: частота дискретизации сигнала (в Гц)
        - filter_type: тип фильтра ('butter' для Баттерворта, 'cheby' для Чебышёва)
        - order: порядок фильтра (рекомендуется 2-16, как в WaveForms)

        Возвращает:
        - отфильтрованный сигнал (массив NumPy)
        """
        # Нормализуем частоту среза (частота Найквиста = sampling_rate / 2)
        nyquist_freq = 0.5 * sampling_rate
        normalized_cutoff = cutoff_freq / nyquist_freq

        # Проектируем фильтр
        if filter_type == 'butter':
            b, a = signal.butter(order, normalized_cutoff, btype='low')
        elif filter_type == 'cheby':
            # Для Чебышёва нужно указать допустимую неравномерность (rp) в дБ
            rp = 0.5  # Неравномерность в полосе пропускания, 0.5 дБ - хорошее значение по умолчанию
            b, a = signal.cheby1(order, rp, normalized_cutoff, btype='low')
        else:
            raise ValueError("filter_type должен быть 'butter' или 'cheby'")

        # Применяем фильтр с двусторонней фильтрацией (нулевая задержка фазы)
        # Это ключевой момент: filtfilt обрабатывает сигнал дважды (вперёд и назад),
        # что устраняет сдвиг фазы, как и в программных фильтрах WaveForms [citation:5].
        filtered_signal = signal.filtfilt(b, a, data)

        return filtered_signal
    
    def median_filter_3point(data):
        """
        Медианный фильтр с окном из 3 точек
        (аналог MATLAB кода с buf(1,1:3)=0)

        Параметры:
        - data: входной сигнал (ADC_sin)

        Возвращает:
        - middle: отфильтрованный медианным фильтром сигнал
        """
        data = np.asarray(data)
        N = len(data)

        # Инициализация буфера и результата
        buf = np.zeros(3)
        middle = np.zeros(N)
        count = 0  # в Python индексация с 0

        # Медианный фильтр
        for i in range(N):
            # Записываем в буфер (циклический)
            buf[count] = data[i]
            count += 1

            if count > 2:  # если больше 2 (так как индексы 0,1,2)
                count = 0

            # Находим медиану из трех значений
            a = buf[0]
            b = buf[1]
            c = buf[2]

            # Алгоритм поиска медианы
            if (a <= b) and (a <= c):
                if (b <= c):
                    middle[i] = b
                else:
                    middle[i] = c
            elif (b <= a) and (b <= c):
                if (a <= c):
                    middle[i] = a
                else:
                    middle[i] = c
            else:
                if (a <= b):
                    middle[i] = a
                else:
                    middle[i] = b

        return middle

    def running_average_filter(data, k=0.1):
        """
        Экспоненциальный бегущий средний фильтр (running average)
        (аналог MATLAB кода raf_sin)

        Параметры:
        - data: входной сигнал (middle)
        - k: коэффициент сглаживания (0 < k < 1)

        Возвращает:
        - raf_sin: отфильтрованный сигнал
        """
        data = np.asarray(data)
        N = len(data)

        # Инициализация
        raf_sin = np.zeros(N)

        # Первое значение
        raf_sin[0] = (data[0] - raf_sin[0]) * k

        # Основной цикл
        for i in range(1, N):
            raf_sin[i] = raf_sin[i-1] + (data[i] - raf_sin[i-1]) * k

        return raf_sin
    

    def RefreshGraph2():
        global flag,listY2,listY
        listY2 = listY
        aaf = []
        aaf1 = []
        # for i in range(GRAPH_LENGTH_POINTS):
        #     aaf.append(0) 
        # flag = True
        flag = True
        
        # N = len(listY2)  
        NUM_READ = 3
        # aaf = [0] * N

        # ЦИКЛ ФИЛЬТРА 
        # for i in range(NUM_READ, N):  # от NUM_READ до N-1
        #     for j in range(NUM_READ):  # от 0 до 49
        #         aaf[i] = aaf[i] + listY2[i - j]
        #     aaf[i] = aaf[i] / NUM_READ              

        # aaf1 = median_filter_3point(listY2)
        # aaf = running_average_filter(aaf1,0.5)
        aaf = apply_lowpass_filter(listY2,200,1000,'butter',4)


        ui.graph2.clear()
        ui.graph2.plot(listX[NUM_READ:GRAPH_LENGTH_POINTS-1],listY2[NUM_READ:GRAPH_LENGTH_POINTS-1],pen=pen2)      
        ui.graph2.plot(listX[NUM_READ:GRAPH_LENGTH_POINTS-1],aaf[NUM_READ:GRAPH_LENGTH_POINTS-1],pen=pen)

    
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
                        # value = value*2
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
    pen2 = pg.mkPen(color=(255, 0, 0), width=1, style=QtCore.Qt.DashLine)
    ui.graph.showGrid(x=True, y=True)
    ui.graph.plot(listX,listY,pen=pen)

    #Для второго графика 
    ui.graph2.setBackground("w")
    ui.graph2.showGrid(x=True, y=True)
    ui.graph2.plot(listX2,listY2,pen=pen)



    ui.show()
    sys.exit(app.exec_()) 