clc;
close all;
clear;
Fs = 10000;                  
%частота дискретизации 10кHz

%далее сымитируем дискретный сигнал
t = 0:1/Fs:0.200;
t = t';
Am2 = 1; F = 175; Phi2 = 0; W2 = 2*pi*F;
noise(1,1:length(t)) = 0;
noise = noise';

for i = 1:length(t)
    noise(i) = 0.0005*(mod(i-1,500)+1);
end    

Sin = Am2/5* sin(W2*t);%третья 
plot (t(1:100)*1000,Sin(1:100)) %По оси X будут отображаться миллисекунды 
figure;
Sig = Sin + noise;          %тот самый сигнал который был "получен с АЦП"
% она же страшная кривая состоящая из суммы синусод,
%имитирующая звуковой сигнал в данном примере 
plot (t*1000,Sig) %По оси X будут отображаться миллисекунды 
figure;
plot (t*1000,noise)




%среднее арифметическое_1
NUM_READ = 150;
aaf_sig = zeros(1,length(t)); % ariphmetic average  filter
for i = NUM_READ : length(t)
    for j = 0 :NUM_READ-1
        aaf_sig(i) = aaf_sig(i) + Sig(i-j);
    end
  
    aaf_sig(i) = aaf_sig(i)/NUM_READ;
    aaf_sig(i-NUM_READ+1)= aaf_sig(i);
end

filVal(1,1:length(t)) = 0;
% фильтр эксп среднее
k = 0.008;
    filVal(1) = (Sig(1) - filVal(1))*k;
    for i = 2:length(t)
      %filVal(i) = (measuredSig(i)*k + (filVal(i-1))*(1-k));  
      filVal(i) = filVal(i-1)+ (Sig(i) - filVal(i-1))*k;  
      
    end

%среднее арифметическое_2
aaf_sig_2 = zeros(1,length(t)); % ariphmetic average  filter
for i = NUM_READ : length(t)
    for j = 0 :NUM_READ-1
        aaf_sig_2(i) = aaf_sig_2(i) + Sig(i-j);
    end
  
    aaf_sig_2(i) = aaf_sig_2(i)/NUM_READ;
    aaf_sig_2(i-NUM_READ+1)= aaf_sig_2(i);
end

filVal_2(1,1:length(t)) = 0;
% фильтр среднее арифметическое + эксп среднее
k = 0.01;
    filVal_2(1) = (aaf_sig(1) - filVal_2(1))*k;
    for i = 2:length(t)
      %filVal(i) = (measuredSig(i)*k + (filVal(i-1))*(1-k));  
      filVal_2(i) = filVal_2(i-1)+ (aaf_sig(i) - filVal_2(i-1))*k;  
      
    end

plot(t*1000,Sig,'LineWidth',1.5), grid on;
hold on;
plot(t*1000,aaf_sig,'LineWidth',1.5), grid on;
hold off;
xlabel('Время');
ylabel('Амплитуда');
title('среднее арифмитеческое');
figure;

plot(t*1000,Sig,'LineWidth',1.5), grid on;
hold on;
plot(t*1000,filVal,'LineWidth',1.5), grid on;
hold off;
xlabel('Время');
ylabel('Амплитуда');
title('экспонен среднее');

figure('Position', [250, 100, 800, 600]);
subplot(3,1,1);
plot(t*1000,Sig,'LineWidth',1.5), grid on;
hold on;
plot(t*1000,aaf_sig,'LineWidth',1.5), grid on;
hold off;
xlabel('Время');
ylabel('Амплитуда');
title(compose('фильтр среднее арифметическое \n NUM READ = %d',NUM_READ));


subplot(3,1,2);
plot(t*1000,Sig,'LineWidth',1.5), grid on;
hold on;
plot(t*1000,filVal_2,'LineWidth',1.5), grid on;
hold off;
xlabel('Время');
ylabel('Амплитуда');
title(compose('фильтр среднее арифметическое + эксп среднее \n F = %d,  k = %.2f',F,k));
hold on;


flag = 0
count = 0
count_one_period = 0
comp(1,1:length(Sig)) = 0;
for i = 1 : length(Sig)
    if Sig(i) > filVal(i)
        comp(i)=1;
        if flag == 0
            count = count +1;
            if i < 500
                count_one_period = count
            end    
        end
        flag = 1;
    else 
        comp(i)=0;
        flag = 0;
    end
         
end

F_found = 1 * count_one_period / 0.05; 
subplot(3,1,3);
plot(t*1000,comp)
title(compose('count = %d, count one period = %d, F found = %.2f',count,count_one_period,F_found));

