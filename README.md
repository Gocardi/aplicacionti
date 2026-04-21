# Proyecto AplicacionTI: IoT y Edge Computing

Este proyecto es una demostración práctica para ilustrar los conceptos de Computación Ubicua y Edge Computing, conectando un reloj inteligente Togala P99 a un entorno basado en Arch Linux e integrando análisis local mediante MQTT y LF Edge eKuiper.

## Conceptos Clave

- **Computación Ubicua:** Integración de la tecnología de manera imperceptible en nuestro entorno. En este proyecto, el smartwatch interacciona de forma autónoma (como detectar inactividad, reproductor multimedia) actuando en pro del bienestar y conveniencia del usuario.
- **Edge Computing:** Consiste en procesar la información cerca del sitio en donde se generan los datos en lugar de mandarla a una nube centralizada. Los datos del smartwatch se procesan localmente de forma ultra-rápida (en eKuiper de LF Edge), lo que permite respuestas de baja latencia (ej. alertas de sedentarismo) sin comprometer la privacidad del usuario al no enviar los datos personales sin procesar a internet.

## Estructura del Proyecto

1. **Bridge BLE-MQTT (`bridge/bridge.py`):** Un script asíncrono en Python usando `bleak` para extraer los datos del smartwatch vía el protocolo Bluetooth Low Energy (GLoryFit) e inyectarlos de manera normalizada a un broker de mensajería (Mosquitto). También acciona comandos locales de linux.
2. **Broker de Mensajería:** Mosquitto corriendo en Docker, sirviendo como la "columna vertebral" del ecosistema en el Edge.
3. **Procesamiento de Reglas en eKuiper (`rules/`):** Utilizado para ingestar streams de datos de MQTT en tiempo real y ejecutar reglas del tipo SQL. En este caso detecta eventos de "sedentarismo".

## Prerrequisitos en Arch Linux

Es imprescindible instalar las herramientas para contenedores, clientes Bluetooth, y Python en tu ambiente Arch Linux:

```bash
sudo pacman -Syu
sudo pacman -S docker docker-compose python-pip mosquitto playerctl
```

*(Nota: Asegúrate de habilitar e iniciar el servicio Docker: `sudo systemctl enable --now docker`)*

## Guía de Instalación y Ejecución

**1. Desplegar los Contenedores (Edge Core)**

Inicia Mosquitto y LF Edge eKuiper como demonios mediante docker-compose:

```bash
docker-compose up -d
```
Verifica que los servicios estén activos: `docker-compose ps`

**2. Instalar dependencias de Python para el Bridge**

Desde la carpeta raíz del proyecto, instala las librerías `bleak` y `paho-mqtt` que nos permiten la comunicación Bluetooth Asíncrona respectiva:

```bash
pip install -r bridge/requirements.txt
```

**3. Levantar el Bridge BLE -> Edge**

Asegúrate de que el Smartwatch esté encendido y dentro del alcance. Luego ejecuta:

```bash
python bridge/bridge.py
```

**4. Dar de Alta el Stream y la Regla en eKuiper**

Mientras el bridge se ejecuta, manda las siguientes instrucciones HTTP a la API REST de eKuiper (puerto 9081) usando `curl` o un cliente similar:

**Crear el Stream:**
```bash
curl -X POST http://localhost:9081/streams -H "Content-Type: application/json" -d '{"sql": "CREATE STREAM watch_stream () WITH (DATASOURCE=\"sensors/watch\", FORMAT=\"json\")"}'
```

**Asignar la Regla de Sedentarismo:**
```bash
curl -X POST http://localhost:9081/rules -H "Content-Type: application/json" -d @rules/sedentarismo_rule.json
```

Si el smartwatch reporta pocos pasos, eKuiper detectará el evento y dejará un informe en los logs del contenedor (ej: `docker logs ekuiper`). Además, los toques táctiles del reproductor en el smartwatch aplicarán `playerctl play-pause` nativamente.
