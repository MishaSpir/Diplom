################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (10.3-2021.10)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../ST7735/lcd.c \
../ST7735/logo_128_160.c \
../ST7735/logo_160_80.c \
../ST7735/skrdg.c \
../ST7735/skrudge.c \
../ST7735/st7735.c \
../ST7735/st7735_reg.c \
../ST7735/test.c 

OBJS += \
./ST7735/lcd.o \
./ST7735/logo_128_160.o \
./ST7735/logo_160_80.o \
./ST7735/skrdg.o \
./ST7735/skrudge.o \
./ST7735/st7735.o \
./ST7735/st7735_reg.o \
./ST7735/test.o 

C_DEPS += \
./ST7735/lcd.d \
./ST7735/logo_128_160.d \
./ST7735/logo_160_80.d \
./ST7735/skrdg.d \
./ST7735/skrudge.d \
./ST7735/st7735.d \
./ST7735/st7735_reg.d \
./ST7735/test.d 


# Each subdirectory must supply rules for building sources it contributes
ST7735/%.o ST7735/%.su: ../ST7735/%.c ST7735/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m7 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32H743xx -c -I../Core/Inc -I../Drivers/STM32H7xx_HAL_Driver/Inc -I../Drivers/STM32H7xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32H7xx/Include -I../Drivers/CMSIS/Include -I"D:/RADIK/Diplom/STM32H743/LCD_test/ST7735" -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv5-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-ST7735

clean-ST7735:
	-$(RM) ./ST7735/lcd.d ./ST7735/lcd.o ./ST7735/lcd.su ./ST7735/logo_128_160.d ./ST7735/logo_128_160.o ./ST7735/logo_128_160.su ./ST7735/logo_160_80.d ./ST7735/logo_160_80.o ./ST7735/logo_160_80.su ./ST7735/skrdg.d ./ST7735/skrdg.o ./ST7735/skrdg.su ./ST7735/skrudge.d ./ST7735/skrudge.o ./ST7735/skrudge.su ./ST7735/st7735.d ./ST7735/st7735.o ./ST7735/st7735.su ./ST7735/st7735_reg.d ./ST7735/st7735_reg.o ./ST7735/st7735_reg.su ./ST7735/test.d ./ST7735/test.o ./ST7735/test.su

.PHONY: clean-ST7735

