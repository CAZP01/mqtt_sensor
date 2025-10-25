import tkinter as tk
from mqtt.client import MqttClient
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import time


class DashboardUI:
    def __init__(self, root, config):
        self.root = root
        self.config = config

        self.root.title(config["dashboard"]["title"])
        self.root.geometry(f"{config['dashboard']['width']}x{config['dashboard']['height']}")
        self.root.configure(bg="#f5f6fa")

        self.temperature_data = []
        self.humidity_data = []
        self.timestamps = []
        self.led_status = tk.StringVar(value="OFF")
        self.led_control = tk.StringVar(value="OFF")

        self.setup_ui()

        self.mqtt_client = MqttClient(config, on_message_callback=self.on_mqtt_message)
        self.mqtt_client.connect()

        self.refresh_rate = config["dashboard"]["refresh_rate"]
        self.root.after(self.refresh_rate, self.update_graphs)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.running = True

    def setup_ui(self):
        title_label = tk.Label(
            self.root,
            text=self.config["dashboard"]["title"],
            font=("Segoe UI", 16, "bold"),
            bg="#2f3640",
            fg="white",
            pady=10
        )
        title_label.pack(fill="x")

        title_label = tk.Label(
            self.root,
            text="Chairul 'Azmi Zuhdi Pramono - 23106050024",
            font=("Segoe UI", 16, "bold"),
            bg="#2f3640",
            fg="white",
            pady=10
        )
        title_label.pack(fill="x")

        frame_temp = tk.LabelFrame(
            self.root, text="Grafik Suhu (°C)",
            font=("Segoe UI", 12, "bold"), bg="#f5f6fa"
        )
        frame_temp.pack(padx=10, pady=10, fill="both", expand=True)

        self.fig_temp, self.ax_temp = plt.subplots(figsize=(8, 3))
        self.ax_temp.set_title("Suhu")
        self.ax_temp.set_xlabel("Waktu")
        self.ax_temp.set_ylabel("°C")
        self.temp_line, = self.ax_temp.plot([], [], color="red")
        self.canvas_temp = FigureCanvasTkAgg(self.fig_temp, master=frame_temp)
        self.canvas_temp.get_tk_widget().pack(fill="both", expand=True)

        frame_hum = tk.LabelFrame(
            self.root, text="Grafik Kelembapan (%)",
            font=("Segoe UI", 12, "bold"), bg="#f5f6fa"
        )
        frame_hum.pack(padx=10, pady=10, fill="both", expand=True)

        self.fig_hum, self.ax_hum = plt.subplots(figsize=(8, 3))
        self.ax_hum.set_title("Kelembapan")
        self.ax_hum.set_xlabel("Waktu")
        self.ax_hum.set_ylabel("%")
        self.hum_line, = self.ax_hum.plot([], [], color="blue")
        self.canvas_hum = FigureCanvasTkAgg(self.fig_hum, master=frame_hum)
        self.canvas_hum.get_tk_widget().pack(fill="both", expand=True)

        self.frame_led = tk.Frame(self.root, bg="#f5f6fa")
        self.frame_led.pack(pady=15, fill="x")

        tk.Label(
            self.frame_led, text="Warna LED:",
            font=("Segoe UI", 12, "bold"), bg="#f5f6fa"
        ).grid(row=0, column=0, padx=5)

        self.label_led_status = tk.Label(
            self.frame_led, textvariable=self.led_status,
            font=("Segoe UI", 12), fg="black", bg="#f5f6fa"
        )
        self.label_led_status.grid(row=0, column=1, padx=5)

        btn_frame = tk.Frame(self.frame_led, bg="#f5f6fa")
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.btn_led_on = tk.Button(
            btn_frame,
            text="Nyalakan LED",
            command=lambda: self.control_led(True),
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=15,
            relief="flat",
            cursor="hand2"
        )
        self.btn_led_on.pack(side="left", padx=10)

        self.btn_led_off = tk.Button(
            btn_frame,
            text="Matikan LED",
            command=lambda: self.control_led(False),
            bg="#c0392b",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=15,
            relief="flat",
            cursor="hand2"
        )
        self.btn_led_off.pack(side="left", padx=10)

    def on_mqtt_message(self, topic, data):
        """Dipanggil ketika ada pesan dari broker"""
        try:
            if topic == self.config["topics"]["sensor_temp"]:
                temperature = float(data.get("temperature", 0))
                self.temperature_data.append(temperature)
                self.timestamps.append(time.strftime("%H:%M:%S"))
                print(f"[UI] Temperature updated: {temperature}")

            elif topic == self.config["topics"]["sensor_humidity"]:
                humidity = float(data.get("humidity", 0))
                self.humidity_data.append(humidity)
                print(f"[UI] Humidity updated: {humidity}")
            
            elif topic == self.config["topics"]["led_status"]:
                led_color = str(data.get("led", "OFF")).upper()
                self.led_status.set(led_color)
                print(f"[UI] LED color: {led_color}")
                self.update_led_background_from_status(led_color)

            if len(self.temperature_data) > 50:
                self.temperature_data.pop(0)
                self.humidity_data.pop(0)
                self.timestamps.pop(0)

        except Exception as e:
            print(f"[UI] Error handling message: {e}")

    def update_led_background_from_status(self, led_state):
        color_map = {
            "RED": "#e84118",
            "YELLOW": "#fbc531",
            "GREEN": "#4cd137",
            "OFF": "#f5f6fa"
        }
        color = color_map.get(led_state, "#f5f6fa")
        self.frame_led.configure(bg=color)
        for widget in self.frame_led.winfo_children():
            widget.configure(bg=color)

    def update_graphs(self):
        if self.temperature_data:
            self.temp_line.set_data(range(len(self.temperature_data)), self.temperature_data)
            self.ax_temp.set_xlim(0, len(self.temperature_data))
            self.ax_temp.set_ylim(min(self.temperature_data) - 1, max(self.temperature_data) + 1)
            self.canvas_temp.draw()

        if self.humidity_data:
            self.hum_line.set_data(range(len(self.humidity_data)), self.humidity_data)
            self.ax_hum.set_xlim(0, len(self.humidity_data))
            self.ax_hum.set_ylim(min(self.humidity_data) - 1, max(self.humidity_data) + 1)
            self.canvas_hum.draw()

        if self.running:
            self.root.after(self.refresh_rate, self.update_graphs)

    def control_led(self, state):
        """Kirim perintah ON/OFF ke broker dan update tampilan"""
        topic = self.config["topics"]["led_control"]
        payload = "ON" if state else "OFF"

        self.mqtt_client.publish(topic, payload)
        print(f"[UI] LED control sent: {payload}")

        if not state:
            self.led_status.set("OFF")
            self.update_led_background_from_status("OFF")
        else:
            self.led_status.set("ON")
            self.update_led_background_from_status("OFF")

    def on_close(self):
        print("[UI] Menutup aplikasi dan memutus koneksi MQTT...")
        self.running = False
        try:
            self.mqtt_client.client.loop_stop()
            self.mqtt_client.client.disconnect()
            print("[MQTT] Disconnected from broker.")
        except Exception as e:
            print(f"[UI] Gagal menghentikan MQTT: {e}")
        self.root.destroy()

if __name__ == "__main__":
    with open("mqtt/config.json") as f:
        config = json.load(f)

    root = tk.Tk()
    app = DashboardUI(root, config)
    root.mainloop()
