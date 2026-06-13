DAC_BUFFER_SIZE = 256
SawAmpDac = 3000;
OffsetDac = 1000;
dac_buffer =   zeros(1,DAC_BUFFER_SIZE); 

for  i = 1:DAC_BUFFER_SIZE        % Линейное нарастание от 0 до SawAmpDac
        value = (i * SawAmpDac) / (DAC_BUFFER_SIZE );
        value = value + OffsetDac;
        
        if (value > 4095) 
            value = 4095;
        end    
        if (value < 0) 
            value = 0;
            
        end
        dac_buffer(i) = value;
end

stairs(0:(DAC_BUFFER_SIZE-1), dac_buffer, 'b-', 'LineWidth', 1.5);

t1 = 23.45
t2 = 29.5
f0 = 1/((t2-t1)*1e-3)
f0 = 179
R = ((f0 * 299792458 * 50e-3) / (2*8.38e8)) 
B = (f0 * 299792458 * 0.050) / (2*1.3)