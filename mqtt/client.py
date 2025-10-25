import json
import paho.mqtt.client as mqtt
import threading

class MqttClient:
    """
    Kelas pembungkus untuk komunikasi MQTT antara GUI dan broker.
    - Menghubungkan ke broker
    - Menerima data dari ESP32
    - Mengirim kontrol LED dari GUI
    """

    def __init__(self, config, on_message_callback=None):
        self.config = config
        self.broker = config["broker"]["host"]
        self.port = config["broker"]["port"]
        self.keepalive = config["broker"]["keepalive"]
        self.username = config["broker"]["username"]
        self.password = config["broker"]["password"]
        self.topics = config["topics"]

        self.client_id = "dashboard-client"
        self.on_message_callback = on_message_callback

        self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        """Callback saat berhasil terhubung ke broker"""
        if rc == 0:
            self.connected = True
            print("[MQTT] Connected with code 0")
            self.client.subscribe(self.topics["sensor_temp"])
            self.client.subscribe(self.topics["sensor_humidity"])
            if "led_status" in self.topics:
                self.client.subscribe(self.topics["led_status"])
            print("[MQTT] Subscribed to topics.")
        else:
            print(f"[MQTT] Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        """Callback saat pesan diterima"""
        try:
            payload = msg.payload.decode()
            print(f"[MQTT] Message received on {msg.topic}: {payload}")

            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = {"raw": payload}

            if self.on_message_callback:
                self.on_message_callback(msg.topic, data)

        except Exception as e:
            print(f"[MQTT] Error processing message: {e}")

    def on_disconnect(self, client, userdata, rc):
        """Callback saat koneksi terputus"""
        self.connected = False
        print("[MQTT] Disconnected from broker.")

    def connect(self):
        """Menyambung ke broker MQTT"""
        try:
            print(f"[MQTT] Connecting to broker: {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, self.keepalive)

            thread = threading.Thread(target=self.client.loop_forever)
            thread.daemon = True
            thread.start()
            return True
        except Exception as e:
            print(f"[MQTT] Connection error: {e}")
            return False

    def publish(self, topic: str, message):
        """
        Fungsi umum untuk publish pesan ke topic tertentu.
        Digunakan oleh DashboardUI.
        """
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            self.client.publish(topic, message)
            print(f"[MQTT] Published to {topic}: {message}")
        except Exception as e:
            print(f"[MQTT] Failed to publish message: {e}")

    def publish_led_control(self, state: bool):
        """Publish kontrol LED ke ESP32 (opsional, kompatibilitas lama)"""
        topic = self.topics["led_control"]
        message = "on" if state else "off"
        self.publish(topic, message)

    def disconnect(self):
        """Putus koneksi dari broker"""
        try:
            self.client.disconnect()
        except Exception as e:
            print(f"[MQTT] Disconnect error: {e}")
