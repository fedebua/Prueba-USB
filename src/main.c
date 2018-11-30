/* Copyright 2015, Pablo Ridolfi
 * All rights reserved.
 *
 * This file is part of lpc1769_template.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its
 *    contributors may be used to endorse or promote products derived from this
 *    software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 */

/** @brief Ejemplo con FreeRTOS, USB, LCD 16x2.
 **
 **/

/** \addtogroup usb_cdc CDC+LCD+FreeRTOS example
 ** @{ */

/*==================[inclusions]=============================================*/

#include "../../USB_TEST/inc/main.h"

#include "../../USB_TEST/inc/cdc_vcom.h"
#include "board.h"

/*==================[macros and definitions]=================================*/

/*==================[internal data declaration]==============================*/

/*==================[internal functions declaration]=========================*/

/** @brief hardware initialization function
 *	@return none
 */
static void initHardware(void);
extern uint32_t prompt;
xSemaphoreHandle semtick;

/*==================[internal functions definition]==========================*/

/** @brief Inicialización general del hardware
 *
 */
static void initHardware(void)
{
    SystemCoreClockUpdate();
    Board_Init();
    Board_LED_Set(0, false);

    Chip_GPIOINT_Init(LPC_GPIOINT);
    Chip_GPIOINT_SetIntFalling(LPC_GPIOINT, GPIOINT_PORT0, 1 << 18);
    NVIC_EnableIRQ(EINT3_IRQn);

    Chip_GPIO_SetPinDIROutput(LPC_GPIO, 2, 9);
    Chip_GPIO_SetPinOutLow(LPC_GPIO, 2, 9);
}

/** @brief Tarea que destella el led del stick cada 500ms y prueba STDOUT
 *
 * @param p no utilizado
 */
static void ledTask(void * p)
{
	while (1)
	{
		Board_LED_Toggle(0);
		vTaskDelay(500 / portTICK_RATE_MS);
	}
}

/*==================[external functions definition]==========================*/

/** @brief entry point */
int main(void)
{
	initHardware();

	xTaskCreate(ledTask, (signed const char *)"led", 2048, 0, tskIDLE_PRIORITY+1, 0);
	xTaskCreate(cdcTask, (signed const char *)"cdc", 1024, 0, tskIDLE_PRIORITY+2, 0);
	vSemaphoreCreateBinary(semtick);
	xSemaphoreTake(semtick,0);


	vTaskStartScheduler();

	while(1);
}

void vApplicationTickHook(void)
{
	portBASE_TYPE xTaskSwitchRequired = pdFALSE;
	if(prompt)
		xSemaphoreGiveFromISR(semtick, &xTaskSwitchRequired); //Doy un tick por cada ms
	portEND_SWITCHING_ISR(xTaskSwitchRequired);
}
/** @} doxygen end group definition */

/*==================[end of file]============================================*/
