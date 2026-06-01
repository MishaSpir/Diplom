
# Создание bytearray

```python
# Пустой bytearray
b = bytearray()                    # bytearray(b'')

# Из строки (с указанием кодировки)
b = bytearray("Hello", 'utf-8')    # bytearray(b'Hello')

# Из списка байт (0-255)
b = bytearray([0x24, 0x01, 0x0A])  # bytearray(b'$\x01\n')

# Указание длины (заполнено нулями)
b = bytearray(10)                  # bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

# Из существующего байтового объекта
b = bytearray(b'\x24\x01\x0A')



### 1. Добавление и удаление элементов
python

b = bytearray([0x01, 0x02, 0x03])
# append(value) - добавляет байт в конец (0-255)
b.append(0x04)                     # bytearray(b'\x01\x02\x03\x04')
# extend(iterable) - добавляет последовательность
b.extend([0x05, 0x06])             # bytearray(b'\x01\x02\x03\x04\x05\x06')
# insert(index, value) - вставляет байт на позицию
b.insert(0, 0x00)                  # bytearray(b'\x00\x01\x02\x03\x04\x05\x06')
# pop(index=-1) - удаляет и возвращает байт
value = b.pop()                    # удалит последний
value = b.pop(0)                   # удалит первый
# remove(value) - удаляет первое вхождение
b.remove(0x03)                     # удалит байт 0x03
# clear() - очищает весь массив
b.clear()                          # bytearray(b'')

### 2. Поиск и замена

python

b = bytearray(b'Hello World')
# find(sub) - поиск подстроки (возвращает индекс)
pos = b.find(b'World')             # 6
pos = b.find(b'x')                 # -1 (не найдено)
# index(sub) - поиск (вызывает ValueError если не найдено)
try:
    pos = b.index(b'World')        # 6
except ValueError:
    pass
# count(sub) - подсчёт вхождений
cnt = b.count(b'l')                # 3
# replace(old, new) - замена
b.replace(b'l', b'L')              # bytearray(b'HeLLo WorLd')
# startswith(prefix) - начинается ли с подстроки
if b.startswith(b'Hello'):         # True
    pass
# endswith(suffix) - заканчивается ли на подстроку
if b.endswith(b'World'):           # True
    pass

### 3. Изменение и преобразование

python

b = bytearray(b'Hello')
# Изменение по индексу
b[0] = 0x48                        # 'H' -> 'H' (тот же)
b[1] = 0x69                        # 'e' -> 'i' (bytearray(b'Hillo'))
# Срезы (изменение диапазона)
b[1:3] = b'aa'                     # bytearray(b'Haalo')
b[1:4] = b'xyz'                    # bytearray(b'Hxyz')
# capitalize() - первая буква заглавная
b = bytearray(b'hello world')
b = b.capitalize()                 # bytearray(b'Hello world')
# upper() / lower() - верхний/нижний регистр
b.upper()                          # bytearray(b'HELLO WORLD')
b.lower()                          # bytearray(b'hello world')
# hex() - преобразование в HEX строку
hex_str = b.hex()                  # '48656c6c6f'
hex_str = b.hex(' ')               # '48 65 6c 6c 6f' (с разделителем)
# fromhex() - создание из HEX строки
b = bytearray.fromhex('48 65 6c 6c 6f')  # bytearray(b'Hello')

### 4. Срезы и копирование

python

b = bytearray(b'Hello World')
# Срез (создаёт новый bytearray)
b2 = b[0:5]                        # bytearray(b'Hello')
# copy() - копирование
b_copy = b.copy()                  # полная копия
# Другие способы копирования
b_copy = b[:]                      # срез всей строки
b_copy = bytearray(b)              # через конструктор

### 5. Информация о байтах

python

b = bytearray(b'Hello')
# len() - длина
length = len(b)                    # 5
# Проверка вхождения
if 0x48 in b:                      # True (H)
    pass
# Сумма всех байт
total = sum(b)                     # 72+101+108+108+111 = 500
# Максимальный/минимальный байт
max_byte = max(b)                  # 111 ('o')
min_byte = min(b)                  # 72 ('H')
```


```python 
## Практические примеры для работы с UART

### Отправка команды на STM32

python

def send_command(cmd, param):
    """Отправка команды на STM32"""
    # Создаём пакет
    packet = bytearray()
    packet.append(0x24)            # Стартовый байт
    packet.append(cmd)             # Команда
    packet.extend(param.to_bytes(2, 'big'))  # 16-битный параметр
    packet.append(0x0A)            # Терминатор
    
    # Или короче:
    packet = bytearray([0x24, cmd]) + param.to_bytes(2, 'big') + bytearray([0x0A])
    
    serial.write(packet)
    print(f"Отправлено: {packet.hex().upper()}")
# Использование
send_command(0x01, 500)  # Команда 1, параметр 500

### Поиск пакетов в буфере

python

def find_packets(buffer):
    """Поиск пакетов в буфере с разделителем 0x0A"""
    packets = []
    
    while True:
        # Ищем терминатор
        pos = buffer.find(b'\x0A')
        if pos == -1:
            break
        
        # Извлекаем пакет
        packet = buffer[:pos]
        packets.append(packet)
        
        # Удаляем из буфера
        buffer = buffer[pos+1:]
    
    return packets, buffer
# Использование
buffer = bytearray()
packets, buffer = find_packets(buffer)

### Разбор пакета

python

def parse_packet(packet):
    """Разбор пакета из STM32 (4 байта + терминатор)"""
    if len(packet) >= 4:
        # Вариант 1: через срезы
        adc_1 = (packet[0] << 8) | packet[1]
        adc_2 = (packet[2] << 8) | packet[3]
        
        # Вариант 2: через int.from_bytes
        # adc_1 = int.from_bytes(packet[0:2], 'big')
        # adc_2 = int.from_bytes(packet[2:4], 'big')
        
        return adc_1, adc_2
    return None, None
# Использование
packet = bytearray([0x12, 0x34, 0x56, 0x78])
val1, val2 = parse_packet(packet)
print(f"ADC1: {val1}, ADC2: {val2}")  # ADC1: 4660, ADC2: 22136

### Обработка последовательного порта

python

def read_serial():
    """Чтение данных из serial порта"""
    global buffer
    
    while serial.bytesAvailable():
        data = serial.readAll()
        buffer.extend(data)
        
        # Поиск пакетов
        packets, buffer = find_packets(buffer)
        
        for packet in packets:
            if len(packet) >= 4:
                adc_1, adc_2 = parse_packet(packet)
                process_data(adc_1, adc_2)
        
        # Защита от переполнения
        MAX_BUFFER_SIZE = 5000
        if len(buffer) > MAX_BUFFER_SIZE:
            buffer = buffer[-MAX_BUFFER_SIZE:]
```
