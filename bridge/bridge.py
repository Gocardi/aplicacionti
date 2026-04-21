import asyncio
import os
import struct
from bleak import BleakClient
import paho.mqtt.client as mqtt

MAC_ADDRESS = "78:02:B7:04:15:D5"
WRITE_CHAR_UUID = "000033f1-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID = "000033f2-0000-1000-8000-00805f9b34fb"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_TX = "sensors/watch"
MQTT_TOPIC_RX = "edge/acciones"

# Setup MQTT Client (API v2)
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
ble_client_global = None

def notification_handler(sender, data):
    if len(data) > 0:
        header = data[0]
        # Command 0xB2: Pasos
        if header == 0xB2 and len(data) >= 6:
            steps = struct.unpack('<I', data[2:6])[0]
            print(f"🔔 Pasos actualizados: {steps}")
            mqtt_client.publish(MQTT_TOPIC_TX, f'{{"sensor": "steps", "value": {steps}}}')

def on_message(client, userdata, msg):
    print(f"Recibido mensaje en MQTT: {msg.topic}")
    # Run async action in the running event loop
    loop = asyncio.get_running_loop()
    asyncio.run_coroutine_threadsafe(handle_action(), loop)

async def handle_action():
    print("▶ Ejecutando comando local playerctl play-pause")
    await asyncio.create_subprocess_shell('playerctl play-pause')
    
    if ble_client_global and ble_client_global.is_connected:
        print("▶ Enviando comando de vibración [0xAB, 0x01] al smartwatch")
        await ble_client_global.write_gatt_char(WRITE_CHAR_UUID, bytearray([0xAB, 0x01]))

async def main():
    global ble_client_global
    
    # Store running loop for callbacks
    asyncio.get_running_loop()
    
    # Connect to MQTT
    mqtt_client.on_message = on_message
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        mqtt_client.subscribe(MQTT_TOPIC_RX)
        print(f"Conectado a MQTT Broker en {MQTT_BROKER}:{MQTT_PORT} y suscrito a {MQTT_TOPIC_RX}")
    except Exception as e:
        print(f"Error conectando a MQTT: {e}")
        return

    print(f"Conectando al Smartwatch con MAC {MAC_ADDRESS}...")
    async with BleakClient(MAC_ADDRESS) as client:
        ble_client_global = client
        print("Conectado exitosamente al Smartwatch.")
        
        # Start Notifications
        await client.start_notify(NOTIFY_CHAR_UUID, notification_handler)
        print("Suscrito a notificaciones GATT.")
        
        # Start streaming command (0xB2)
        command = bytearray([0xB2])
        await client.write_gatt_char(WRITE_CHAR_UUID, command)
        print("Comando de streaming 0xB2 enviado.")
        
        print("--------------------------------------------------")
        print("Puente BLE <-> MQTT activo. Presiona Ctrl+C para salir.")
        print("--------------------------------------------------")
        
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Finalizando aplicación...")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
