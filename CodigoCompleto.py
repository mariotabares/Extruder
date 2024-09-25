from machine import Pin, I2C
import time
from max6675 import MAX6675
import sh1106

# Configura los pines para el MAX6675
so = Pin(12, Pin.IN, Pin.PULL_UP)
sck = Pin(14, Pin.OUT)
cs = Pin(4, Pin.OUT)

# Banderas de comunicacion
FD = Pin(7, Pin.IN)
FP = Pin(5, Pin.IN)
FI = Pin(6, Pin.IN)

# Inicializa el MAX6675 
max6675 = MAX6675(sck, cs, so)

# Configuración del pin de entrada para el detector de cruce por cero
zero_cross_pin = Pin(3, Pin.IN, Pin.PULL_UP)

# Configuración del pin de salida para el TRIAC
triac_pin = Pin(9, Pin.OUT, Pin.PULL_UP)

# Configuración de los pines de los pulsadores
button_up = Pin(0, Pin.IN, Pin.PULL_UP)
button_down = Pin(1, Pin.IN, Pin.PULL_UP)

# Variables para almacenar el tiempo
last_cross_time = 0
time_between_crossings = 0
delay_time = 0

# Configura la pantalla OLED
i2c = I2C(1, scl=Pin(27), sda=Pin(26))
oled_width = 128
oled_height = 64
oled = sh1106.SH1106_I2C(oled_width, oled_height, i2c)

# PID
setpoint = 140    # Temperatura deseada en grados Celsius
Kp = 0.024
Ki = 1.08
Kd = 0.27
Ts = 13.5  # Tiempo de muestreo en segundos

# Variables PID inicializadas
error_anterior = 0  
error_trasanterior = 0
integral = 0
q0 = (1 + (Ts / 2 * Ki) + (Kp / Ts))
q1 = -Kp * int(1 - (Ts / 2 * Ki) + (2 * (Kp / Ts)))
q2 = Kp * (Kd / Ts)
u_k_1 = 0

# Inicializa el contador
contador = 0

# Variable para controlar la frecuencia de actualización del OLED
last_oled_update = time.ticks_ms()  # Tiempo del último refresco de OLED
oled_interval = 4000  # Intervalo de 4 segundos en milisegundos

# Función para mostrar la temperatura y dirección en la pantalla
def mostrar_texto(temp, dirMotor):
    oled.fill(0)  # Limpia la pantalla
    oled.text('TEMPERATURA:', 0, 0)
    oled.text(f'{temp:.2f} C', 0, 10)
    oled.text('DIRECCION:', 0, 20)
    oled.text(dirMotor, 0, 30)
    oled.show()
    print(temp, dirMotor)

# Función para leer la temperatura desde el MAX6675
def leerTemperatura():
    return max6675.read()

# Función que se ejecuta en cada cruce por cero
def zero_cross_detected(pin):
    global last_cross_time, time_between_crossings, delay_time

    # Obtener el tiempo actual en microsegundos
    current_time = time.ticks_us()

    if last_cross_time != 0:
        # Calcular el tiempo entre los cruces por cero
        time_between_crossings = time.ticks_diff(current_time, last_cross_time)

    # Actualizar el tiempo del último cruce por cero
    last_cross_time = current_time

    # Activar el TRIAC justo en el cruce por cero
    triac_pin.on()

    if delay_time < time_between_crossings:
        # Desactiva el TRIAC después de un retardo calculado
        time.sleep_us(delay_time)
        triac_pin.off()
    else:
        # Reiniciar delay_time si se excede del tiempo entre cruces
        delay_time = time_between_crossings
        triac_pin.on()  # Asegurarse de apagar el TRIAC

# Función para manejar los pulsadores
def check_buttons():
    global setpoint

    if not button_up.value():  # Si se presiona el botón de incremento
        setpoint += 1  # Incrementa el setpoint
        print(f"Setpoint incrementado: {setpoint}")
        time.sleep(0.2)  # Evita rebotes

    if not button_down.value():  # Si se presiona el botón de decremento
        setpoint -= 1  # Decrementa el setpoint
        print(f"Setpoint decrementado: {setpoint}")
        time.sleep(0.2)  # Evita rebotes

# Configuración de la interrupción en el pin de cruce por cero
zero_cross_pin.irq(trigger=Pin.IRQ_RISING, handler=zero_cross_detected)

# Bucle principal
try:
    prevDirMotor = 'pausa'  # Variable para almacenar la última dirección válida

    while True:
        # Determinar la dirección del motor
        if FP.value() == 1:
            # Pausar y mantener la dirección previa
            dirMotor = 'pausa'
        else:
            if FD.value() == 1:
                dirMotor = 'derecha'
                prevDirMotor = 'derecha'
            elif FI.value() == 1:
                dirMotor = 'izquierda'
                prevDirMotor = 'izquierda'
            else:
                dirMotor = prevDirMotor  # Retomar la dirección previa

        # Leer la temperatura
        temp = leerTemperatura()
        u_k = u_k_1

        # Incrementa el contador
        contador += 1

        # Calcular el error PID
        error = setpoint - temp

        # Ley del controlador PID
        u_k = u_k_1 + q0 * error + q1 * error_anterior + q2 * error_trasanterior

        # Saturar la salida del PID entre 0 y 100
        if u_k > 100:
            u_k = 100
        elif u_k < 0:
            u_k = 0

        # Escalar el valor de u_k para calcular el delay_time
        delay_time = int((time_between_crossings-1500) * (u_k / 100.0))

        # Asegurarse de que delay_time no sea negativo ni mayor que el tiempo entre cruces
        if delay_time < 0:
            delay_time = 0
        elif delay_time > time_between_crossings:
            delay_time = time_between_crossings

        # Actualizar los errores anteriores
        error_trasanterior = error_anterior
        error_anterior = error

        # Verificar si los pulsadores se han presionado para modificar el setpoint
        check_buttons()

        # Mostrar la información en la OLED cada 4 segundos
        if time.ticks_diff(time.ticks_ms(), last_oled_update) >= oled_interval:
            mostrar_texto(temp, dirMotor)  # Ahora muestra la dirección correcta
            last_oled_update = time.ticks_ms()  # Actualizar el tiempo del último refresco de la pantalla

        # Mostrar el contador, la temperatura, y los valores relevantes en la consola
        print(f'{contador} , {temp:.2f} , {u_k}, {delay_time}, {time_between_crossings};')

        # Esperar el tiempo de muestreo
        time.sleep(2)

except KeyboardInterrupt:
    print("Programa interrumpido")
    triac_pin.off()  # Apagar el TRIAC al salir
