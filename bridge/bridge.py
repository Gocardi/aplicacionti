import asyncio
import os
import struct
from bleak import BleakClient
import paho.mqtt.client as mqtt

MAC_ADDRESS = "78:02:B7:04:15:D5"
WRITE_CHAR_UUID = "000033f1-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID = "000033f2-0000-1000-8000-00805f9b34fb"
BATTERY_CHAR_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors/watch"

# Setup MQTT Client (API v2)
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def notification_handler(sender, data):
    if len(data) > 0:
        header = data[0]
        # Command 0xB2: Pasos
        if header == 0xB2 and len(data) >= 6:
            steps = struct.unpack('<I', data[2:6])[0]
            print(f"🔔 Evento de Pasos: {steps}")
            mqtt_client.publish(MQTT_TOPIC, f'{{"sensor": "steps", "value": {steps}}}')
        
        # Command 0xD1: Multimedia
        elif header == 0xD1 and len(data) >= 2:
            media_action = data[1]
            if media_action == 0x07:
                print("🔔 Evento Multimedia (Play/Pause) detectado, ejecutando comando local.")
                os.system('playerctl play-pause')

async def poll_battery(client):
    while True:
        try:
            battery_data = await client.read_gatt_char(BATTERY_CHAR_UUID)
            if battery_data:
                battery_level = int(battery_data[0])
                print(f"🔋 Nivel de batería: {battery_level}%")
                mqtt_client.publish(MQTT_TOPIC, f'{{"sensor": "battery", "value": {battery_level}}}')
        except Exception as e:
            print(f"⚠️ Error leyendo la batería: {e}")
        await asyncio.sleep(10)

async def main():
    # Connect to MQTT
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print(f"Conectado a MQTT Broker en {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        print(f"Error conectando a MQTT: {e}")
        return

    print(f"Conectando al Smartwatch con MAC {MAC_ADDRESS}...")
    async with BleakClient(MAC_ADDRESS) as client:
        print("Conectado exitosamente al Smartwatch.")
        
        # Start Notifications
        await client.start_notify(NOTIFY_CHAR_UUID, notification_handler)
        print("Suscrito a notificaciones GATT.")
        
        # Start streaming command (0xB2)
        command = bytearray([0xB2])
        await client.write_gatt_char(WRITE_CHAR_UUID, command)
        print("Comando de streaming 0xB2 enviado.")
        
        # Start polling battery in the background
        asyncio.create_task(poll_battery(client))
        
        print("--------------------------------------------------")
        print("Puente BLE -> MQTT activo. Presiona Ctrl+C para salir.")
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
