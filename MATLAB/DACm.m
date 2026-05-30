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