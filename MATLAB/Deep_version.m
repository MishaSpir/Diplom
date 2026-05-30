clc;
close all;
clear;

% Параметры
Fs = 10000;                  
t = (0:1/Fs:0.200)';
F = 155;  % изменено с 300 на 155
W2 = 2*pi*F;

% Генерация сигнала
noise = 0.0005 * (mod(0:length(t)-1, 500) + 1)';
Sin = 0.2 * sin(W2*t);  % Am2/5 = 0.2
Sig = Sin + noise;

% Фильтр экспоненциальный
k = 0.008;
filVal = zeros(size(Sig));
filVal(1) = Sig(1);
for i = 2:length(t)
    filVal(i) = filVal(i-1) + (Sig(i) - filVal(i-1)) * k;
end

%% УЛУЧШЕННЫЙ АЛГОРИТМ ПОДСЧЕТА ЧАСТОТЫ

% 1. Находим все пересечения (и сверху-вниз, и снизу-вверх)
crossings_down = [];  % переход сверху вниз
crossings_up = [];    % переход снизу вверх

for i = 1:length(Sig)-1
    if Sig(i) > filVal(i) && Sig(i+1) <= filVal(i+1)
        crossings_down = [crossings_down; i];
    elseif Sig(i) < filVal(i) && Sig(i+1) >= filVal(i+1)
        crossings_up = [crossings_up; i];
    end
end

% 2. Объединяем все пересечения
all_crossings = sort([crossings_down; crossings_up]);
all_crossings_times = t(all_crossings);

% 3. Автоматическое определение установившегося режима
% Находим момент, когда разница между сигналом и фильтром стабилизируется
diff_signal = abs(Sig - filVal);
window_size = 1000; % окно для поиска стабилизации
moving_std = movstd(diff_signal, window_size);
[~, stable_start_idx] = min(moving_std(window_size:end));
stable_start_idx = stable_start_idx + window_size - 1;
stable_start_time = t(stable_start_idx);

% 4. Берем только пересечения в установившемся режиме
stable_crossings = all_crossings_times(all_crossings_times > stable_start_time);
stable_crossings = stable_crossings(1:end-1); % убираем последнее

% 5. Расчет частоты по периодам
if length(stable_crossings) >= 3
    % Получаем полные периоды (каждые 2 пересечения = 1 период)
    periods = [];
    for i = 1:2:length(stable_crossings)-1
        if i+1 <= length(stable_crossings)
            periods = [periods; stable_crossings(i+1) - stable_crossings(i)];
        end
    end
    
    avg_period = mean(periods);
    F_found_improved = 1 / avg_period;
    
    % Альтернативный расчет через количество пересечений
    total_time = stable_crossings(end) - stable_crossings(1);
    F_found_from_count = (length(stable_crossings) - 1) / (2 * total_time);
else
    F_found_improved = 0;
    F_found_from_count = 0;
end

%% СРАВНЕНИЕ С ВАШИМ МЕТОДОМ

% ВАШ МЕТОД (оригинальный)
flag = 0;
count = 0;
count_one_period = 0;
for i = 1:length(Sig)
    if Sig(i) > filVal(i)
        if flag == 0
            count = count + 1;
            if i < 500
                count_one_period = count_one_period + 1;
            end
        end
        flag = 1;
    else
        flag = 0;
    end
end

F_found_old = count_one_period / 0.05;
F_found2_old = count / (4*0.05);

%% ВИЗУАЛИЗАЦИЯ

figure('Position', [100, 100, 1200, 800]);

% График 1: Сигнал и фильтр
subplot(3,2,1);
plot(t*1000, Sig, 'b', 'LineWidth', 1); hold on;
plot(t*1000, filVal, 'r', 'LineWidth', 1.5);
plot(t(crossings_down)*1000, Sig(crossings_down), 'go', 'MarkerSize', 8, 'MarkerFaceColor', 'g');
plot(t(crossings_up)*1000, Sig(crossings_up), 'mo', 'MarkerSize', 8, 'MarkerFaceColor', 'm');
plot([stable_start_time*1000, stable_start_time*1000], [-0.5, 0.5], 'k--', 'LineWidth', 2);
grid on;
xlabel('Время (мс)');
ylabel('Амплитуда');
title('Сигнал и фильтр с пересечениями');
legend('Сигнал', 'Фильтр', 'Переход ↓', 'Переход ↑', 'Начало стаб. режима', 'Location', 'best');
xlim([0, 200]);

% График 2: Разность сигнала и фильтра
subplot(3,2,2);
plot(t*1000, Sig - filVal, 'LineWidth', 1);
hold on;
plot([0, 200], [0, 0], 'k--');
plot([stable_start_time*1000, stable_start_time*1000], [-0.5, 0.5], 'r--', 'LineWidth', 2);
grid on;
xlabel('Время (мс)');
ylabel('Разность');
title('Разность сигнал - фильтр (пересечения = нули)');
xlim([0, 200]);

% График 3: Ваш метод (компаратор)
subplot(3,2,3);
comp = zeros(size(Sig));
for i = 1:length(Sig)
    comp(i) = Sig(i) > filVal(i);
end
plot(t*1000, comp, 'LineWidth', 1);
grid on;
xlabel('Время (мс)');
ylabel('Уровень');
title('Ваш метод: компаратор');
ylim([-0.1, 1.1]);
xlim([0, 200]);

% График 4: Начальный участок (детали)
subplot(3,2,4);
plot(t(1:500)*1000, Sig(1:500), 'b', 'LineWidth', 1); hold on;
plot(t(1:500)*1000, filVal(1:500), 'r', 'LineWidth', 1.5);
plot(t(crossings_down(crossings_down<=500))*1000, Sig(crossings_down(crossings_down<=500)), 'go', 'MarkerSize', 8);
plot(t(crossings_up(crossings_up<=500))*1000, Sig(crossings_up(crossings_up<=500)), 'mo', 'MarkerSize', 8);
grid on;
xlabel('Время (мс)');
ylabel('Амплитуда');
title('Начальный участок (0-50 мс)');
legend('Сигнал', 'Фильтр', 'Переход ↓', 'Переход ↑', 'Location', 'best');

% График 5: Стабилизация сигнала
subplot(3,2,5);
plot(t*1000, moving_std, 'LineWidth', 1);
hold on;
plot([stable_start_time*1000, stable_start_time*1000], [0, max(moving_std)], 'r--', 'LineWidth', 2);
grid on;
xlabel('Время (мс)');
ylabel('Скользящее СКО');
title('Автоматическое определение стабилизации');
legend('СКО разности', 'Начало стаб. режима');

% График 6: Результаты
subplot(3,2,6);
axis off;
text(0.05, 0.95, 'СРАВНЕНИЕ РЕЗУЛЬТАТОВ', 'FontSize', 14, 'FontWeight', 'bold');
text(0.05, 0.80, sprintf('Реальная частота: %.2f Гц', F), 'FontSize', 12, 'Color', 'b');
text(0.05, 0.65, sprintf('Ваш метод (F_found): %.2f Гц (ошибка %.2f%%)', ...
    F_found_old, abs(F_found_old-F)/F*100), 'FontSize', 11);
text(0.05, 0.55, sprintf('Ваш метод (F_found2): %.2f Гц (ошибка %.2f%%)', ...
    F_found2_old, abs(F_found2_old-F)/F*100), 'FontSize', 11);
text(0.05, 0.40, sprintf('Улучшенный метод: %.2f Гц (ошибка %.2f%%)', ...
    F_found_improved, abs(F_found_improved-F)/F*100), 'FontSize', 11, 'Color', 'r');
text(0.05, 0.30, sprintf('Метод по количеству: %.2f Гц (ошибка %.2f%%)', ...
    F_found_from_count, abs(F_found_from_count-F)/F*100), 'FontSize', 11, 'Color', 'r');
text(0.05, 0.15, sprintf('Параметры: k=%.3f, Fs=%d Гц', k, Fs), 'FontSize', 10);
text(0.05, 0.05, sprintf('Найдено пересечений: %d (всего), %d (в стаб. режиме)', ...
    length(all_crossings), length(stable_crossings)), 'FontSize', 10);

fprintf('\n=== РЕЗУЛЬТАТЫ АНАЛИЗА ===\n');
fprintf('Реальная частота: %.2f Гц\n', F);
fprintf('Ваш метод F_found: %.2f Гц (ошибка: %.2f%%)\n', F_found_old, abs(F_found_old-F)/F*100);
fprintf('Ваш метод F_found2: %.2f Гц (ошибка: %.2f%%)\n', F_found2_old, abs(F_found2_old-F)/F*100);
fprintf('Улучшенный метод: %.2f Гц (ошибка: %.2f%%)\n', F_found_improved, abs(F_found_improved-F)/F*100);