# Proyecto AplicacionTI: IoT y Edge Computing

Este proyecto es una demostración práctica de Computación Ubicua y Edge Computing en un entorno Arch Linux.

El ecosistema integra datos extraídos vía BLE desde un smartwatch Togala P99. Estos datos viajan a través de los siguientes componentes para detectar eventos de inactividad (sedentarismo) y accionar el entorno local:
**Sensor (Smartwatch) -> Bridge (Python) -> Broker (Mosquitto) -> Motor de Reglas (LF Edge eKuiper) -> Acción (Reproductor Multimedia Local)**

## Flujo Operativo y Conceptos
- **Computación Ubicua:** Integración imperceptible. El usuario lleva el reloj y su actividad afecta directamente al entorno (si no camina, la música se pausa automáticamente).
- **Edge Computing:** Todos los datos se procesan "en el borde". eKuiper evalúa la cantidad de pasos enventanados en intervalos de tiempo localmente, publicando una alerta a Mosquitto (tópico `edge/acciones`), todo sin enviar datos a la nube.

## Prerrequisitos (Arch Linux)

Asegúrate de instalar los paquetes clave:
```bash
sudo pacman -S docker docker-compose python-pip mosquitto playerctl
```
Y de iniciar tu servicio de Docker: `sudo systemctl enable --now docker`

## Levantar el Entorno y Dependencias

**1. Contenedores Base (Mosquitto & eKuiper):**
Desde la carpeta raíz del proyecto ejecuta:
```bash
docker-compose up -d
```

**2. Descargar las Librerías Python:**
```bash
pip install -r bridge/requirements.txt
```

## Ejecución del Puente BLE-MQTT
Asegúrate de que tu reloj Togala P99 tenga el Bluetooth encendido y ejecuta el bridge asíncrono para enganchar tu hardware a Mosquitto:
```bash
python bridge/bridge.py
```

## Crear Configuración en eKuiper

A la par de la ejecución de la app, manda estos requests para formalizar la regla de negocio y analizar los streams en tiempo real:

**Registrar Stream (Fuente de datos):**
```bash
curl -X POST http://localhost:9081/streams -H "Content-Type: application/json" -d '{"sql": "CREATE STREAM watch_stream () WITH (DATASOURCE=\"sensors/watch\", FORMAT=\"json\")"}'
```

**Asignar Regla de Sedentarismo:**
```bash
curl -X POST http://localhost:9081/rules -H "Content-Type: application/json" -d @rules/sedentarismo_rule.json
```

Si tus pasos tomados no superan el threshold (pasos < 5 en una ventana de 60 segundos), eKuiper desencadenará el evento en `edge/acciones`, lo cual pausará localmente tu música mediante `playerctl` e instruirá al smartwatch a que envíe una ráfaga táctica (vibración).
