для bool надо использовать библиотеку 
```cpp
#include "stdbool.h"
```

# Мигаем светодиодом
```cpp
if(HAL_GetTick() - T >= 2000){
		  T = HAL_GetTick();
		  flag = !flag;
}
HAL_GPIO_WritePin(GPIOE,GPIO_PIN_3, flag);

```

# Цифровой вход (кнопка)

 На плате WeAct есть кнопка K1 на PC13, подключеннная к VCC
```cpp
	
	  button_state = !(HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_13));
	  if(button_state){
		  GPIOE->BSRR = (1 << 3);
//		  HAL_GPIO_WritePin(GPIOE,GPIO_PIN_3, 1);
	  }else{
		  GPIOE->BSRR = (1 << (3+16));
//		  HAL_GPIO_WritePin(GPIOE,GPIO_PIN_3, 0);
	  }
```
обработчик кнопки(переключатель)
```cpp
button_state = !(HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_13));
	  if(button_state && !button_pressed && HAL_GetTick() - T >= 50){
		  T = HAL_GetTick();
		  button_pressed =1;
		  flag = !flag;
	  }else if(!button_state && button_pressed && HAL_GetTick() - T >= 50){
		  T = HAL_GetTick();
		  button_pressed =0;
	  }

	  HAL_GPIO_WritePin(GPIOE,GPIO_PIN_3, flag);
```