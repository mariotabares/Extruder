import utime
from machine import Pin

# Declaración de puertos
PUL = 20    # Señal pulsada
DIR = 21   # Define la dirección
EN = 22     # Define el enable
DER = 10    # Define la interrupción derecha
PA = 11    # Define la interrupción de pausa
IZQ = 12    # Define la interrupción izquierda

# Banderas
FD = Pin(4, Pin.OUT)  # Cambiado a OUT para poder controlarlas
FP = Pin(3, Pin.OUT)
FI = Pin(2, Pin.OUT)

# Configuración de pines
button_pin_derecha = Pin(DER, Pin.IN, Pin.PULL_UP)     # Botón Derecha
button_pin_izquierda = Pin(IZQ, Pin.IN, Pin.PULL_UP)   # Botón Izquierda
button_pin_pausa = Pin(PA, Pin.IN, Pin.PULL_UP)        # Botón Pausa
pul_pin = Pin(PUL, Pin.OUT)
dir_pin = Pin(DIR, Pin.OUT)
en_pin = Pin(EN, Pin.OUT)

# Estado inicial y variables de control
paused = False
current_direction = None  # Variable para almacenar la dirección actual del movimiento

# Variables para debounce
debounce_delay = 500  # Retardo de debounce en milisegundos
last_interrupt_time = 0  # Variable para almacenar el tiempo de la última interrupción

# Funciones de manejo de interrupción con debounce
def button_interrupt_handler_derecha(pin):
    global paused, current_direction, last_interrupt_time
    current_time = utime.ticks_ms()
    if current_time - last_interrupt_time > debounce_delay:
        last_interrupt_time = current_time
        if not paused and current_direction != "derecha":
            current_direction = "derecha"
            dir_pin.value(0)   # Dirección hacia la derecha
            en_pin.value(1)
            FD.value(1)  # Activa bandera de derecha
            FI.value(0)  # Desactiva la bandera de izquierda
            FP.value(0)  # Desactiva la bandera de pausa
            print("Iniciando movimiento a la derecha")

def button_interrupt_handler_izquierda(pin):
    global paused, current_direction, last_interrupt_time
    current_time = utime.ticks_ms()
    if current_time - last_interrupt_time > debounce_delay:
        last_interrupt_time = current_time
        if not paused and current_direction != "izquierda":
            current_direction = "izquierda"
            dir_pin.value(1)   # Dirección hacia la izquierda
            en_pin.value(1)
            FI.value(1)  # Activa bandera de izquierda
            FD.value(0)  # Desactiva la bandera de derecha
            FP.value(0)  # Desactiva la bandera de pausa
            print("Iniciando movimiento a la izquierda")

def button_interrupt_handler_pausa(pin):
    global paused, last_interrupt_time
    current_time = utime.ticks_ms()
    if current_time - last_interrupt_time > debounce_delay:
        last_interrupt_time = current_time
        paused = not paused
        if paused:
            FP.value(1)  # Activa bandera de pausa
            FD.value(0)  # Desactiva la bandera de derecha
            FI.value(0)  # Desactiva la bandera de izquierda
            print("Pausa")
        else:
            FP.value(0)  # Desactiva la bandera de pausa
            print("Continuar")

# Configuración de interrupciones
button_pin_derecha.irq(trigger=Pin.IRQ_FALLING, handler=button_interrupt_handler_derecha)
button_pin_izquierda.irq(trigger=Pin.IRQ_FALLING, handler=button_interrupt_handler_izquierda)
button_pin_pausa.irq(trigger=Pin.IRQ_FALLING, handler=button_interrupt_handler_pausa)

# Bucle principal
while True:
    if not paused:
        if current_direction == "derecha":
            dir_pin.value(0)   # Dirección hacia la derecha
            en_pin.value(1)
            while not paused and current_direction == "derecha":  # Continuar girando mientras no esté pausado y la dirección sea "derecha"
                pul_pin.value(1)
                utime.sleep_us(400)
                pul_pin.value(0)
                utime.sleep_us(400)
                

        elif current_direction == "izquierda":
            dir_pin.value(1)   # Dirección hacia la izquierda
            en_pin.value(1)
            while not paused and current_direction == "izquierda":  # Continuar girando mientras no esté pausado y la dirección sea "izquierda"
                pul_pin.value(1)
                utime.sleep_us(400)
                pul_pin.value(0)
                utime.sleep_us(400)
                

    utime.sleep_ms(100)  # Pequeña pausa para reducir el uso de CPU
  