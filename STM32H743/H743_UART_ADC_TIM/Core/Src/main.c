/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dac.h"
#include "dma.h"
#include "opamp.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "stdbool.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define PACKET_PREAMBLE  0x24
#define PACKET_TERMINATOR 0x0A
#define PACKET_SIZE 3
#define DAC_BUFFER_SIZE 256
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
uint64_t last_time = 0;

volatile uint8_t uart_tx_complete = 1;

volatile uint16_t adc_value[2];
uint8_t tx_buffer_adc[5];
bool adc_ready = false;
bool led_flag = false;

uint8_t tx_buffer[] = {0x01,0x02};
uint8_t tx_buffer2[] = {0x03,0x04};
uint8_t tx_combined[sizeof(tx_buffer) + sizeof(tx_buffer2) + 2];

uint8_t rx_buffer[PACKET_SIZE];
uint8_t rx_index = 0;
volatile uint8_t packet_ready = 0;
volatile uint8_t received_data = 0;
volatile uint8_t received_byte = 0;
volatile uint8_t synced = 0;  // Флаг �?инхронизации
uint32_t last_byte_time = 0;

typedef enum {
    WAIT_PREAMBLE,
    WAIT_DATA,
    WAIT_TERMINATOR
} UART_State_t;

uint32_t DAC_in;
uint32_t SawDac;
float SawAmpVol = 1.5;
float OffsetVol = 1.0;
uint32_t SawPeriodMs;    // Период пилы в милли�?екундах
uint32_t SawAmpDac;
uint32_t OffsetDac;
volatile uint16_t dac_buffer[DAC_BUFFER_SIZE];


/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1) {
    	uart_tx_complete = 1;
    }
}

UART_State_t uart_state = WAIT_PREAMBLE;

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if(huart == &huart1)
    {
    	 // Провер�?ем наличие ошибок
    	        if (__HAL_UART_GET_FLAG(huart, UART_FLAG_ORE)) {
    	            __HAL_UART_CLEAR_FLAG(huart, UART_FLAG_ORE);
    	            // Сбро�? �?о�?то�?ни�? при ошибке переполнени�?
    	            uart_state = WAIT_PREAMBLE;
    	            HAL_UART_Receive_IT(&huart1, &received_byte, 1);
    	            return;
    	        }

    	        if (__HAL_UART_GET_FLAG(huart, UART_FLAG_FE)) {
    	            __HAL_UART_CLEAR_FLAG(huart, UART_FLAG_FE);
    	            uart_state = WAIT_PREAMBLE;
    	            HAL_UART_Receive_IT(&huart1, &received_byte, 1);
    	            return;
    	        }

    	        if (__HAL_UART_GET_FLAG(huart, UART_FLAG_NE)) {
    	            __HAL_UART_CLEAR_FLAG(huart, UART_FLAG_NE);
    	            uart_state = WAIT_PREAMBLE;
    	            HAL_UART_Receive_IT(&huart1, &received_byte, 1);
    	            return;
    	        }


        last_byte_time = HAL_GetTick();

        switch (uart_state) {
            case WAIT_PREAMBLE:
                if (received_byte == PACKET_PREAMBLE) {
                    uart_state = WAIT_DATA;
                }
                break;

            case WAIT_DATA:
            	received_data = received_byte;
                uart_state = WAIT_TERMINATOR;
                break;

            case WAIT_TERMINATOR:
                if (received_byte == PACKET_TERMINATOR) {
                    packet_ready = 1;
                } else {
//                    // �?еправильный терминатор - отладочный вывод
//                    char dbg[32];
//                    sprintf(dbg, "Err: 0x%02X (exp 0x0A)\r\n", received_byte);
//                    HAL_UART_Transmit(&huart1, (uint8_t*)dbg, strlen(dbg), 100);
                }
                uart_state = WAIT_PREAMBLE;  // В�?егда �?бро�?
                break;
        }

        HAL_UART_Receive_IT(&huart1, &received_byte, 1);
    }
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
{
    if (hadc->Instance == ADC1) {
        adc_ready = true;  // Сигнал, что еcть новые данные
        led_flag = !led_flag;
//        HAL_GPIO_WritePin(GPIOE, GPIO_PIN_3, led_flag);

    }
}

void CheckUARTTimeout(void)
{
    if (uart_state != WAIT_PREAMBLE && (HAL_GetTick() - last_byte_time > 50)) {
        uart_state = WAIT_PREAMBLE;  // Таймаут
    }
}

void CalculateSawtoothBuffer(void);
void UpdateSawtooth(float , float , float );
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_USART1_UART_Init();
  MX_ADC1_Init();
  MX_TIM6_Init();
  MX_OPAMP1_Init();
  MX_DAC1_Init();
  MX_TIM7_Init();
  MX_OPAMP2_Init();
  /* USER CODE BEGIN 2 */
  HAL_ADCEx_Calibration_Start(&hadc1, ADC_CALIB_OFFSET_LINEARITY, ADC_SINGLE_ENDED);
  HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_value, 2);
  HAL_TIM_Base_Start(&htim6);

  HAL_OPAMP_Stop(&hopamp1);                    // О�?танавливаем е�?ли был запущен
  hopamp1.Init.PgaGain = OPAMP_PGA_GAIN_16_OR_MINUS_15;  // У�?танавливаем у�?иление
  if (HAL_OPAMP_Init(&hopamp1) != HAL_OK)      // Инициализируем �? новыми параметрами
  {
      Error_Handler();
  }
  HAL_OPAMP_Start(&hopamp1);                   // Запу�?каем OPAMP

//------------------------------------------------------------------
  HAL_OPAMP_Stop(&hopamp2);                    // О�?танавливаем е�?ли был запущен
  hopamp2.Init.PgaGain = OPAMP_PGA_GAIN_16_OR_MINUS_15;  // У�?танавливаем у�?иление
  if (HAL_OPAMP_Init(&hopamp2) != HAL_OK)      // Инициализируем �? новыми параметрами
  {
      Error_Handler();
  }
  HAL_OPAMP_Start(&hopamp2);                   // Запу�?каем OPAMP
  tx_buffer_adc[4] = 0x0A; // Терминатор
  HAL_UART_Receive_IT(&huart1, &received_byte, 1);

  DAC_in = 0;
  SawDac = 0;
  CalculateSawtoothBuffer();
  UpdateSawtooth(3.0,0.0,50);
  HAL_DAC_Start_DMA(&hdac1, DAC_CHANNEL_1,(uint32_t*)dac_buffer,DAC_BUFFER_SIZE,DAC_ALIGN_12B_R);
  HAL_TIM_Base_Start(&htim7);
//  HAL_ADCEx_Calibration_Start(&hadc2, ADC_CALIB_OFFSET_LINEARITY, ADC_SINGLE_ENDED);

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */


  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */


		  if (adc_ready){
			  adc_ready = false;
              // Копируем данные �? защитой от прерываний
              __disable_irq();
              uint16_t val1 = adc_value[0];
              uint16_t val2 = adc_value[1];
              __enable_irq();

              // Упаковываем в 4 байта
              tx_buffer_adc[0] = (val1 >> 8) & 0xFF;  // тарший байт канала 1
              tx_buffer_adc[1] = val1 & 0xFF;         // младший байт канала 1
              tx_buffer_adc[2] = (val2 >> 8) & 0xFF;  // тарший байт канала 2
              tx_buffer_adc[3] = val2 & 0xFF;         // младший байт канала 2


              // Отправл�?ем, е�?ли UART �?вободен
              if (uart_tx_complete) {
                 uart_tx_complete = 0;
                 HAL_UART_Transmit_IT(&huart1, tx_buffer_adc, 5);
             }
		  }

		  if(packet_ready){
		  		  packet_ready = 0;
//		  	 	  HAL_UART_Transmit_IT(&huart1,  (uint8_t *)received_data, 1);
		  	 if (received_data == 0x01) {
		  		 HAL_GPIO_WritePin(GPIOE, GPIO_PIN_3, GPIO_PIN_SET);
		  	 } else if (received_data == 0x00) {
		  	     HAL_GPIO_WritePin(GPIOE, GPIO_PIN_3, GPIO_PIN_RESET);
		  	 }
		  	 if(received_data > 0x01){
		  		 switch (received_data){
		  		 	 case 0x02:
		  		 		 HAL_OPAMP_Stop(&hopamp1);
		  		 		 HAL_OPAMP_Stop(&hopamp2);
		  		 		 hopamp1.Init.PgaGain = OPAMP_PGA_GAIN_2_OR_MINUS_1;
		  		 		 hopamp2.Init.PgaGain = OPAMP_PGA_GAIN_2_OR_MINUS_1;
		  		 		 break;
		  		 	 case 0x04:
		  		 		 HAL_OPAMP_Stop(&hopamp1);
		  		 		 HAL_OPAMP_Stop(&hopamp2);
		  		 		 hopamp1.Init.PgaGain = OPAMP_PGA_GAIN_4_OR_MINUS_3;
		  		 		 hopamp2.Init.PgaGain = OPAMP_PGA_GAIN_4_OR_MINUS_3;

		  		 		 break;
		  		 	 case 0x08:
		  		 		 HAL_OPAMP_Stop(&hopamp1);
		  		 		 HAL_OPAMP_Stop(&hopamp2);
		  		 		 hopamp1.Init.PgaGain = OPAMP_PGA_GAIN_8_OR_MINUS_7;
		  		 		 hopamp2.Init.PgaGain = OPAMP_PGA_GAIN_8_OR_MINUS_7;
		  		 		 break;
		  		 	 case 0x10:
		  		 		 HAL_OPAMP_Stop(&hopamp1);
		  		 		 HAL_OPAMP_Stop(&hopamp2);
		  		 		 hopamp1.Init.PgaGain = OPAMP_PGA_GAIN_16_OR_MINUS_15;
		  		 		 hopamp2.Init.PgaGain = OPAMP_PGA_GAIN_16_OR_MINUS_15;
		  		 		 break;
		  		 	 default:
		  		 		 HAL_OPAMP_Stop(&hopamp1);
		  		 		 HAL_OPAMP_Stop(&hopamp1);
		  		 		 hopamp1.Init.PgaGain = OPAMP_PGA_GAIN_16_OR_MINUS_15;
		  		 		 hopamp2.Init.PgaGain = OPAMP_PGA_GAIN_16_OR_MINUS_15;
		  		 		 break;
		  		 }
		         if (HAL_OPAMP_Init(&hopamp1) != HAL_OK) {
		             Error_Handler();
		         }
		         if (HAL_OPAMP_Init(&hopamp2) != HAL_OK) {
		             Error_Handler();
		         }
		  		 HAL_OPAMP_Start(&hopamp1);                   // Запу�?каем OPAMP
		  		 HAL_OPAMP_Start(&hopamp2);
		  	 }
		  }

		  CheckUARTTimeout();
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Supply configuration update enable
  */
  HAL_PWREx_ConfigSupply(PWR_LDO_SUPPLY);

  /** Configure the main internal regulator output voltage
  */
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE3);

  while(!__HAL_PWR_GET_FLAG(PWR_FLAG_VOSRDY)) {}

  /** Macro to configure the PLL clock source
  */
  __HAL_RCC_PLL_PLLSOURCE_CONFIG(RCC_PLLSOURCE_HSE);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI|RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSIState = RCC_HSI_DIV2;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 5;
  RCC_OscInitStruct.PLL.PLLN = 40;
  RCC_OscInitStruct.PLL.PLLP = 2;
  RCC_OscInitStruct.PLL.PLLQ = 2;
  RCC_OscInitStruct.PLL.PLLR = 2;
  RCC_OscInitStruct.PLL.PLLRGE = RCC_PLL1VCIRANGE_2;
  RCC_OscInitStruct.PLL.PLLVCOSEL = RCC_PLL1VCOWIDE;
  RCC_OscInitStruct.PLL.PLLFRACN = 0;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2
                              |RCC_CLOCKTYPE_D3PCLK1|RCC_CLOCKTYPE_D1PCLK1;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.SYSCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB3CLKDivider = RCC_APB3_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_APB1_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_APB2_DIV1;
  RCC_ClkInitStruct.APB4CLKDivider = RCC_APB4_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */
void CalculateSawtoothBuffer(void)
{
    for (int i = 0; i < DAC_BUFFER_SIZE; i++) {
        // Линейное нара�?тание от 0 до SawAmpDac
        uint32_t value = (i * SawAmpDac) / (DAC_BUFFER_SIZE - 1);
        value += OffsetDac;

        // Ограничение
        if (value > 4095) value = 4095;
        if (value < 0) value = 0;

        dac_buffer[i] = (uint16_t)value;
    }
}

// Функци�? обновлени�? параметров пилы
void UpdateSawtooth(float amplitude_volts, float offset_volts, float period_ms)
{
    // Конвертаци�? вольт в коды DAC (Vref = 3.3V)
    SawAmpDac = (uint32_t)(amplitude_volts * 4095.0f / 3.3f);
    OffsetDac = (uint32_t)(offset_volts * 4095.0f / 3.3f);
    SawPeriodMs = (uint32_t)period_ms;



    // Пере�?читать ча�?тоту таймера
    // Ча�?тота DAC обновлени�? = DAC_BUFFER_SIZE / (period_ms / 1000)
    uint32_t dac_freq_hz = (DAC_BUFFER_SIZE * 1000) / SawPeriodMs;

    // �?а�?тройка таймера (TIM7) дл�? нужной ча�?тоты
    // При APB1 = 100 МГц
    uint32_t timer_clock = 100000000;  // 100 МГц
    uint32_t prescaler = 0;
    uint32_t period = 0;

    // Подбор делителей
    uint32_t total_divider = timer_clock / dac_freq_hz;

    // Е�?ли делитель небольшой, то prescaler = 0
    if (total_divider <= 65536) {
        prescaler = 0;
        period = total_divider - 1;
    }
    // Е�?ли делитель больше 65536, нужно и�?пользовать prescaler
    else {
        // Ищем prescaler такой, чтобы period не превышал 65535
        prescaler = total_divider / 65536;
        period = (total_divider / (prescaler + 1)) - 1;
    }
    __HAL_TIM_SET_PRESCALER(&htim7, prescaler);
    __HAL_TIM_SET_AUTORELOAD(&htim7, period);

    // Пере�?читать буфер
    CalculateSawtoothBuffer();
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
