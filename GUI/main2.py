import sys
from PyQt5.QtWidgets import QApplication
from PyQt5 import uic
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo  
from PyQt5.QtCore import QIODevice, QTimer
import pyqtgraph as pg
import numpy as np
from scipy import signal
import time
from scipy.ndimage import uniform_filter1d
from scipy.fft import fft, fftfreq

# Константы
GRAPH_LENGTH_POINTS = 1000 # кол-во точек 
UPDATE_INTERVAL_MS = 100  # интервал обновления графика 
MAX_PENDING = 100
kexp = 0.01
avrg = 25

# Параметры фильтра
CUTOFF_FREQ = 200   # частота среза 
SAMPLING_RATE = 10000 # частота дискретизации

buffer = bytearray()
# listX = np.arange(GRAPH_LENGTH_POINTS, dtype=np.int32)  # int для X (индексы)
listX = np.linspace(0.0, (GRAPH_LENGTH_POINTS*0.1) - 0.1, GRAPH_LENGTH_POINTS, dtype=np.float32)
listY_raw = np.zeros(GRAPH_LENGTH_POINTS, dtype=np.int32)  # int для АЦП
listY_filtered = np.zeros(GRAPH_LENGTH_POINTS, dtype=np.float64)  # float ТОЛЬКО для фильтра
listY2_filtered = np.zeros(GRAPH_LENGTH_POINTS, dtype=np.float64)  # float ТОЛЬКО для фильтра
listY2 = np.zeros(GRAPH_LENGTH_POINTS, dtype=np.int32)  # int для второго канала

listY_filtered_for_test = []


pending_data_raw = []  # Храним как int
pending_data2 = []     # Храним как int

graph_timer = None
distance_timer = None
DISTANCE_UPDATE_INTERVAL = 500

OnPlot1_flag = False
OnPlot2_flag = False
OnPlot1Filter_flag = False
OnPlot2Filter_flag = False
distance_channel = False
Inverse1Flag = False


led_state = 0
last_opamp_sent = 16

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
    ui = uic.loadUi("design_main2_tabs.ui")
    ui.setWindowTitle("Serial GUI")
    
    # Настройка порта
    serial = QSerialPort()
    serial.setBaudRate(1000000)
    
    portList = [port.portName() for port in QSerialPortInfo().availablePorts()]
    ui.ComList.addItems(portList)
    
    # НАСТРОЙКА НИЖНЕГО ГРАФИКА (graph2) - оба сигнала
    ui.graph2.setBackground("w")
    ui.graph2.showGrid(x=True, y=True)
    ui.graph2.setLabel('left', 'Сигналы')
    ui.graph2.setLabel('bottom', 'ms')
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
    ui.graph.setLabel('left', 'Канал 2')
    ui.graph.setLabel('bottom', 'ms')
    ui.graph.setTitle('Второй канал (без фильтра)')
    curve2 = ui.graph.plot(listX, listY2, pen=pen2)
    curve2_filtered = ui.graph.plot(listX, listY2_filtered, pen=pen_filtered)

     # НАСТРОЙКА  ГРАФИКА 3 (test) 
    pen3 = pg.mkPen(color=(255, 0, 0), width=2)
    ui.graphTest.setBackground("w")
    ui.graphTest.showGrid(x=True, y=True)
    ui.graphTest.setLabel('left', 'Канал 2')
    ui.graphTest.setLabel('bottom', 'ms')
    ui.graphTest.setTitle('тестовые данные')
    curve3_raw = ui.graphTest.plot(listX, listY_filtered_for_test, pen=pen_raw)
    curve3_filtered = ui.graphTest.plot(listX, listY_filtered_for_test, pen=pen3)

    # НАСТРОЙКА  ГРАФИКА 4 (test) - второй канал
    pen4 = pg.mkPen(color=(0, 0, 0), width=2)
    ui.widget.setBackground("w")
    ui.widget.showGrid(x=True, y=True)
    ui.widget.setLabel('left', 'Канал 2')
    ui.widget.setLabel('bottom', 'ms')
    ui.widget.setTitle('цифровой компаратор')
    curve4 = ui.widget.plot(listX, listY_filtered_for_test, pen=pen4, 
    # symbol="+",
    # symbolSize=20,
    # symbolBrush="b"
    )


    
    # Для отладки
    update_count = 0
    last_time = time.time()
    
    def update_graph():
        """Обновление графиков"""
        global pending_data_raw, pending_data2, listY_raw, listY_filtered,listY2_filtered, listY2
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
     
        # Обработка второго канала
        if pending_data2:
            n_new = len(pending_data2)

             # Применяем фильтр к каждому новому значению
            filtered_values = []
            for value in pending_data2:
                filtered_val = apply_lowpass_filter(value)  # value уже int
                filtered_values.append(filtered_val)
            
            if n_new >= GRAPH_LENGTH_POINTS:
                listY2 = np.array(pending_data2[-GRAPH_LENGTH_POINTS:], dtype=np.int32)                
                listY2_filtered = np.array(filtered_values[-GRAPH_LENGTH_POINTS:], dtype=np.float64)
                mean_value = np.mean(listY2_filtered)
                if(Inverse1Flag):
                    listY2_filtered = 2 * mean_value - listY2_filtered
            else:
                listY2 = np.roll(listY2, -n_new)
                listY2[-n_new:] = pending_data2
                listY2_filtered = np.roll(listY2_filtered, -n_new)
                listY2_filtered[-n_new:] = filtered_values
            
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
            
            if(OnPlot1_flag):
                curve2.setData(listX, listY2)
            else:
                curve2.setData([],[])
            if(OnPlot1Filter_flag):
                curve2_filtered.setData(listX, listY2_filtered)    
            else:
                curve2_filtered.setData([], [])    
            
            update_count += 1
            if time.time() - last_time >= 1.0:
                print(f"Обновлений/сек: {update_count}, точек в буфере: {len(pending_data_raw)}")
                update_count = 0
                last_time = time.time()
    
    def OnRead():
         global buffer, pending_data_raw, pending_data2, opamp_value
    
         while serial.bytesAvailable():
            data = serial.readAll()
            buffer.extend(data)

            i = 0
            while i < len(buffer):
                # Новый формат: 4 байта данных + 0x0A + 1 байт OPAMP = 6 байт
                # Проверяем, что есть хотя бы 6 байт для полного пакета
                if i + 5 < len(buffer) and buffer[i+4] == 0x0A:
                    # Извлекаем 4 байта данных (ADC значения)
                    data_packet = buffer[i:i+4]

                    # Извлекаем OPAMP значение (байт после 0x0A)
                    opamp_byte = buffer[i+5] if i+5 < len(buffer) else None

                    # Удаляем весь пакет из буфера (4 + 1 + 1 = 6 байт)
                    buffer = buffer[i+6:]  # пропускаем 4 байта + 0x0A + 1 байт OPAMP

                    if len(data_packet) >= 4:
                        # Читаем ADC значения
                        adc_1 = (data_packet[0] << 8) | data_packet[1]
                        adc_2 = (data_packet[2] << 8) | data_packet[3]

                        # Сохраняем ADC данные
                        pending_data_raw.append(adc_1)
                        pending_data2.append(adc_2)

                        # Сохраняем OPAMP значение (если есть)
                        if opamp_byte is not None:
                            opamp_value = opamp_byte
                            # print(f"OPAMP коэффициент: {opamp_value}")
                            if(opamp_value != last_opamp_sent):
                                SerialSend(last_opamp_sent)  



                    i = 0  # Начинаем поиск сначала
                else:
                    i += 1

            # Защита от переполнения буфера
            if len(buffer) > 5000:
                buffer = buffer[-5000:]
    
    def OnOpen():
        global graph_timer,distance_timer, filter_state, opamp_value, last_opamp_sent

        opamp_value = 0
        last_opamp_sent = 16  # начальное значение усиления
        
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
                print(f"Таймер 1 запущен, интервал {UPDATE_INTERVAL_MS} мс")

            if distance_timer is None:
                distance_timer = QTimer()
                distance_timer.timeout.connect(TestBtn)
                distance_timer.start(DISTANCE_UPDATE_INTERVAL)
                print(f"Таймер 2 запущен, интервал {DISTANCE_UPDATE_INTERVAL} мс")    
        else:
            print("Can't open the port")
    
    def OnClose():
        global graph_timer,distance_timer
        
        if graph_timer:
            graph_timer.stop()
            graph_timer = None

        if distance_timer:
            distance_timer.stop()
            distance_timer = None    
        serial.close()
        print("Port closed")

    def OnPlot2():
        global OnPlot2_flag
        OnPlot2_flag = not OnPlot2_flag

    def OnPlot1():
        global OnPlot1_flag
        OnPlot1_flag = not OnPlot1_flag    

    def OnPlot2Filter():
        global OnPlot2Filter_flag
        OnPlot2Filter_flag = not OnPlot2Filter_flag  

    def OnPlot1Filter():
        global OnPlot1Filter_flag
        OnPlot1Filter_flag = not OnPlot1Filter_flag 

    def LED_toggle(val):
        if val:
            led_state = 1
        else:
            led_state = 0    
        print(led_state)
        SerialSend(led_state)

    def OpAmp_cnahge(val):
        global last_opamp_sent
        val = pow(2,val)
        if val > 16:
            val = 16
        last_opamp_sent = val
        SerialSend(val)    

        
   

    def SerialSend(data): # int
        tx_send_buf = bytearray()    
        tx_send_buf.append(0x24)           # Команда/маркер начала
        tx_send_buf.append(data & 0xFF)    # Данные (обрезаем до 1 байта)
        tx_send_buf.append(0x0A)           # Терминатор \n
        serial.write(tx_send_buf)
        print(f"Отправлено: {tx_send_buf.hex().upper()}")

    def UpdateIntervalChange(val):
        global UPDATE_INTERVAL_MS,graph_timer
        UPDATE_INTERVAL_MS = val * 100
        if graph_timer is not None:
                graph_timer.stop()           # Останавливаем
                graph_timer.start(UPDATE_INTERVAL_MS)  # Запускаем с новым интервалом
    
    def UpdatePortList():
        global portList
        portList = []
        ui.ComList.clear()
        portList = [port.portName() for port in QSerialPortInfo().availablePorts()]    
        ui.ComList.addItems(portList)

    def changeChannel():
        global distance_channel
        distance_channel = not distance_channel

    def Inverse1():
        global Inverse1Flag 
        Inverse1Flag = not Inverse1Flag


    def TestBtn():
        global listY_filtered_for_test, kexp,avrg,opamp_value
        ui.gainLabel.setText("Current gain = " + str(opamp_value))
        if(distance_channel):
            listY_filtered_for_test = listY_filtered
            ui.chan_label.setText("Channel 2")
            
        else:
            listY_filtered_for_test = listY2_filtered
            ui.chan_label.setText("Channel 1")
        curve3_raw.setData(listX, listY_filtered_for_test)
        
        listY_fil = exponential_filter(listY_filtered_for_test,kexp) 
        # listY_fil = moving_average_filter(listY_fil,avrg)
        # listY_fil = moving_average_filter(listY_fil, 100)

        # shift = 100 // 2  # 25 (int)

        # Сдвиг в ПРОТИВОПОЛОЖНУЮ сторону (меняем знак)
        # Было: -shift (влево)
        # Стало: +shift (вправо)
        # listY_fil_shifted = np.roll(listY_fil, shift)  # Убрали минус

        # Заполняем начало, а не конец
        # listY_fil_shifted[:shift] = listY_fil_shifted[shift]  # или listY_fil_shifted[shift+1]

        # curve3_filtered.setData(listX[100:], listY_fil[100:])
        shift = 30
        listY_fil_shifted = listY_fil[shift:]  # Удаляем первые 10 элементов

        # Если нужно сохранить длину массива, добавляем нули в конец
        listY_fil_shifted = np.append(listY_fil[shift:], np.zeros(shift))
        curve3_filtered.setData(listX[:len(listY_fil_shifted)-shift],listY_fil_shifted[:len(listY_fil_shifted)-shift])
        

        comp, F1, F2 = frequency_detection(listY_filtered_for_test, listY_fil_shifted)
        F1  = frequency_detection_simple(listY_filtered_for_test,listY_fil_shifted)
        curve4.setData(listX, comp)
        ui.lcdF1.display(F1)
        if(F1<40):
            kexp = 0.007
            # subexp = (-150)
        elif(F1>40 and F1<120):
            kexp = 0.01
            subexp = 50
        else:
            kexp = 0.025
            subexp = 100
            avrg = 2
        fs = 10000  # частота дискретизации
        # freq_fft, freqs, mags = frequency_detection_fft(listY_fil, fs)
        f,m = frequency_detection_fft_peaks(listY_filtered_for_test,fs,3)
        ui.lcdF2.display(kexp)
        # print(freqs)
        # curve4.setData(f, m)

    def exponential_filter(signal, k=0.08):
       
        signal = np.asarray(signal)
        n = len(signal)
        filVal = np.zeros(n, dtype=np.float64)

        # Первое значение равно первому отсчёту сигнала
        filVal[0] = signal[0]

        # Основной цикл
        for i in range(1, n):
            filVal[i] = signal[i] * k + filVal[i-1] * (1 - k)

        return filVal

    def moving_average_filter(signal, window_size=150):
        signal = np.asarray(signal)
        n = len(signal)
        aaf_sig = np.zeros(n, dtype=np.float64)

        for i in range(window_size, n):
            # Суммируем window_size предыдущих значений
            for j in range(window_size):
                aaf_sig[i] += signal[i - j]

            # Делим на размер окна
            aaf_sig[i] /= window_size

            # Дублируем значение в начало окна (как в MATLAB)
            aaf_sig[i - window_size + 1] = aaf_sig[i]

        return aaf_sig        
    
    def frequency_detection(signal, filtered_signal, threshold=None, time_span=0.05):
        signal = np.asarray(signal)

        if threshold is None:
            threshold = np.asarray(filtered_signal)
        elif isinstance(threshold, (int, float)):
            threshold = np.full_like(signal, threshold)

        n = len(signal)
        comp = np.zeros(n, dtype=np.int8)

        flag = 0
        count = 0
        count_one_period = 0

        for i in range(n):
            if signal[i] > threshold[i]:
                comp[i] = 1
                if flag == 0:
                    count += 1
                    if i < 500:  # Первые 500 отсчётов
                        count_one_period = count
                        count_one_period = count_one_period - 1
                flag = 1
            else:
                comp[i] = 0
                flag = 0

        # Расчёт частоты
        # Предполагается, что time_span = длительность сигнала (в секундах)
        # count_one_period - количество переходов за первый период (~50 мс)
        # count - количество переходов за всю длительность (4*0.05 = 0.2 сек)

        F_found = count_one_period / time_span if time_span > 0 else 0
        F_found2 = count / (2 * time_span) if time_span > 0 else 0

        return comp, F_found, count_one_period
    
    def frequency_detection_simple(signal, threshold, fs=10000):
        """
        Простая версия определения частоты по пересечениям

        Возвращает частоту по количеству пересечений
        """
        signal = np.asarray(signal)
        threshold = np.asarray(threshold)

        # Находим пересечения
        crossings = []
        for i in range(len(signal) - 1):
            if (signal[i] > threshold[i] and signal[i+1] <= threshold[i+1]) or \
               (signal[i] < threshold[i] and signal[i+1] >= threshold[i+1]):
                crossings.append(i)

        if len(crossings) < 3:
            return 0

        # Переводим в секунды
        crossings_time = np.array(crossings) / fs

        # Берем только установившийся режим (пропускаем первые 20%)
        start_idx = len(crossings_time) // 5
        stable_crossings = crossings_time[start_idx:-1]

        if len(stable_crossings) < 2:
            return 0

        # Расчёт частоты
        total_time = stable_crossings[-1] - stable_crossings[0]
        frequency = (len(stable_crossings) - 1) / (2 * total_time)

        return frequency
    
    def frequency_detection_fft_peaks(signal, fs=10000, n_peaks=20):
        """
        Определение нескольких частот через БПФ (всегда возвращает n_peaks значений)

        Возвращает:
        - frequencies: массив частот пиков (всегда длины n_peaks)
        - magnitudes: массив амплитуд пиков (всегда длины n_peaks)
        """
        signal = np.asarray(signal)
        signal = signal - np.mean(signal)

        n = len(signal)
        yf = fft(signal)
        frequencies = fftfreq(n, 1/fs)

        # Берём положительные частоты
        positive_idx = frequencies > 0
        freqs = frequencies[positive_idx]
        mags = np.abs(yf[positive_idx])

        # Ищем пики
        from scipy.signal import find_peaks
        peaks, properties = find_peaks(mags, height=np.max(mags) * 0.1, distance=5)

        # Инициализируем результаты нулями
        result_freqs = np.zeros(n_peaks)
        result_mags = np.zeros(n_peaks)

        if len(peaks) > 0:
            # Сортируем по амплитуде
            peak_heights = properties['peak_heights']
            sorted_idx = np.argsort(peak_heights)[::-1]

            # Берём до n_peaks пиков
            n_peaks_actual = min(n_peaks, len(sorted_idx))
            result_freqs[:n_peaks_actual] = freqs[peaks[sorted_idx[:n_peaks_actual]]]
            result_mags[:n_peaks_actual] = peak_heights[sorted_idx[:n_peaks_actual]]

        return result_freqs, result_mags
    # Подключение сигналов
    serial.readyRead.connect(OnRead)
    ui.openBtn.clicked.connect(OnOpen)
    ui.closeBtn.clicked.connect(OnClose)
    ui.updatePortList.clicked.connect(UpdatePortList)
    ui.testBtn.clicked.connect(TestBtn)
    ui.LED_btn.clicked.connect(LED_toggle)
    ui.changeChannel.clicked.connect(changeChannel)
    ui.inverse1.clicked.connect(Inverse1)
    ui.OpAmpSlider.valueChanged.connect(OpAmp_cnahge)
    ui.graphUpdateSlider.valueChanged.connect(UpdateIntervalChange)

    


    ui.gaph2_on.clicked.connect(OnPlot2)
    ui.gaph1_on.clicked.connect(OnPlot1)
    ui.graph2_filter_on.clicked.connect(OnPlot2Filter) 
    ui.graph1_filter_on.clicked.connect(OnPlot1Filter)
    
    ui.show()
    sys.exit(app.exec_())