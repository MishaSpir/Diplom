# GPIO

HAL_GPIO_WritePin(GPIOB, GPIO_PIN_2, 0);

```cpp
// Установка в 1 (SET)
HAL_GPIO_WritePin(GPIOE, GPIO_PIN_3, 1);
// или так
GPIOE->BSRR = GPIO_PIN_3;      // Установить пин 3 в 1
GPIOE->BSRR = (1 << 3);        // То же самое

// Сброс в 0 (RESET) 
HAL_GPIO_WritePin(GPIOE, GPIO_PIN_3, 0);
// или так
GPIOE->BSRR = (GPIO_PIN_3 << 16);  // Сбросить пин 3 в 0
GPIOE->BSRR = (1 << (3 + 16));     // Альтернативный способ
```
# TIME
 HAL_Delay(1000);
 HAL_GetTick();
 
# TIMERS
```cpp

  HAL_TIM_Base_Start(&htim3);	// просто таймер для получения значений счетчика
__HAL_TIM_SET_PRESCALER(&htim3,7);
__HAL_TIM_SET_AUTORELOAD(&htim3,999);
__HAL_TIM_GET_COUNTER(&htim3);

  
  HAL_TIM_Base_Start_IT(&htim3);// прерывание по update
  HAL_TIM_Base_Stop_IT(&htim3);// остановка прерывания по update
  void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim){
	    if(htim->Instance == TIM6){
                HAL_GPIO_TogglePin(GPIOE, GPIO_PIN_3);
        }
  }// функция-обработчик прерываний
  
  
  HAL_TIM_PWM_Start(&htim3,TIM_CHANNEL_1);
  HAL_TIM_SET_COMPARE(&htim3,TIM_CHANNEL_1,499);
  

```

# UART


```
uint8_t tx_buffer[] = "Hello World\n\r";
uint8_t tx_buffer2[] = {0x00,0x01,0x02,0xFF,0x0A};
uint8_t msg[64];
uint32_t number= 56789;
float pi = 3.14;



HAL_UART_Transmit(&huart1, tx_buffer, (sizeof tx_buffer/sizeof tx_buffer[0]),0xFFFF);
HAL_UART_Transmit(&huart1, tx_buffer2, (sizeof tx_buffer2/sizeof tx_buffer2[0]),0xFFFF);
HAL_UART_Transmit(&huart1, msg, sprintf((char*)msg,"Test"),0xFFFF);
HAL_UART_Transmit(&huart1, msg, sprintf((char*)msg,"%ld",number),0xFFFF);
HAL_UART_Transmit(&huart1, msg, sprintf((char*)msg,"%.2f",pi),0xFFFF);
HAL_Delay(1000);
```
# ADC

```
		HAL_ADC_Start(&hadc1);                 //запуск преобразования сигнала АЦП1
		HAL_ADC_PollForConversion(&hadc1,100); //дожидаемся окончания преобразования 100мс
		adc_value = HAL_ADC_GetValue(&hadc1);  //получаем значение с 12-ти битного АЦП1
		HAL_ADC_Stop(&hadc1);

		HAL_ADC_Start_DMA(&hadc1, (uint32_t*) adc_value, 2); // в массив загружаем данные с 2х каналов
```