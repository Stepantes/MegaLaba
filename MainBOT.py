
import requests
import uuid
import socket
import json

SERVER_URL = "http://127.0.0.1:5000"
CONNECT_ENDPOINT = f"{SERVER_URL}/api/modules/connect"
STATUS_ENDPOINT = f"{SERVER_URL}/api/modules/status"
ADJUST_ENDPOINT = f"{SERVER_URL}/adjust"
SENSOR_UPDATE_ENDPOINT = f"{SERVER_URL}/api/modules"

def default_mac():
    return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(5, -1, -1)])

def default_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class ManualBot:
    def __init__(self):
        self.mac_address = default_mac()
        self.ip_address = default_ip()
        self.module_id = None
        self.temperature = 22.0
        self.humidity = 50.0
        self.light = 1000

    def print_log(self, msg):
        print(f"{self.mac_address}; {msg}")

    def set_mac(self, mac):
        self.mac_address = mac
        self.print_log(f"MAC-адрес изменён на {mac}")

    def set_ip(self, ip):
        self.ip_address = ip
        self.print_log(f"IP-адрес изменён на {ip}")

    def set_param(self, param, value):
        if param == "temperature":
            self.temperature = float(value)
            self.print_log(f"Температура изменена на {self.temperature}")
        elif param == "humidity":
            self.humidity = float(value)
            self.print_log(f"Влажность изменена на {self.humidity}")
        elif param == "light":
            self.light = float(value)
            self.print_log(f"Освещённость изменена на {self.light}")
        else:
            self.print_log(f"Неизвестный параметр: {param}")

    def connect(self):
        data = {
            "mac_address": self.mac_address,
            "ip_address": self.ip_address
        }
        try:
            resp = requests.post(CONNECT_ENDPOINT, json=data, timeout=10)
            if resp.status_code in [200, 201]:
                r = resp.json()
                self.module_id = r.get("module_id")
                self.print_log(f"Подключено к серверу. Ответ: {r}")
            else:
                self.print_log(f"Ошибка подключения (код {resp.status_code}): {resp.text}")
        except Exception as e:
            self.print_log(f"Ошибка подключения: {e}")

    def status(self):
        headers = {
            "X-Module-MAC": self.mac_address,
            "Content-Type": "application/json"
        }
        try:
            resp = requests.get(STATUS_ENDPOINT, headers=headers, timeout=5)
            if resp.status_code == 200:
                self.print_log(f"Статус: {resp.json()}")
            else:
                self.print_log(f"Ошибка статуса (код {resp.status_code}): {resp.text}")
        except Exception as e:
            self.print_log(f"Ошибка статуса: {e}")

    def send_sensor_values(self):
        if not self.module_id:
            self.print_log("Сначала подключитесь к серверу (connect)")
            return
        data = {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "light": self.light
        }
        try:
            resp = requests.put(
                f"{SENSOR_UPDATE_ENDPOINT}/{self.module_id}/sensor-values",
                json=data,
                timeout=10
            )
            if resp.status_code == 200:
                self.print_log(f"Показания отправлены. Ответ: {resp.json()}")
            else:
                self.print_log(f"Ошибка отправки показаний (код {resp.status_code}): {resp.text}")
        except Exception as e:
            self.print_log(f"Ошибка отправки показаний: {e}")

    def adjust(self):
        data = {
            "Temperature": self.temperature,
            "Humidity": self.humidity,
            "Light": self.light
        }
        headers = {
            "X-Module-MAC": self.mac_address,
            "X-Module-ID": str(self.module_id) if self.module_id else "",
            "Content-Type": "application/json"
        }
        try:
            resp = requests.post(ADJUST_ENDPOINT, json=data, headers=headers, timeout=10)
            if resp.status_code == 200:
                self.print_log(f"{resp.json()}")
            else:
                self.print_log(f"Ошибка adjust (код {resp.status_code}): {resp.text}")
        except Exception as e:
            self.print_log(f"Ошибка adjust: {e}")

    def manual(self):
        print("Ручной режим отправки запроса.")
        url = input("URL (например, http://127.0.0.1:5000/api/modules/4/sensor-values): ").strip()
        data_input = input("JSON-данные (например, {\"temperature\":24.71,\"humidity\":0,\"light\":0}): ").strip()
        method = input("HTTP-метод (по умолчанию PUT): ").strip().upper() or "PUT"
        try:
            data = json.loads(data_input) if data_input else None
        except Exception as e:
            print(f"Ошибка парсинга JSON: {e}")
            return
        try:
            resp = requests.request(method, url, json=data, timeout=10)
            try:
                resp_data = resp.json()
            except Exception:
                resp_data = resp.text
            self.print_log(f"MANUAL {method} {url} -> [{resp.status_code}] {resp_data}")
        except Exception as e:
            self.print_log(f"Ошибка ручного запроса: {e}")

    def help(self):
        print("""
Доступные команды:
  connect                — подключиться к серверу
  set mac XX:XX:XX...    — вручную задать MAC-адрес
  set ip X.X.X.X         — вручную задать IP-адрес
  set temperature VALUE  — вручную задать температуру
  set humidity VALUE     — вручную задать влажность
  set light VALUE        — вручную задать освещённость
  status                 — запросить статус модуля на сервере
  send                   — отправить текущие значения датчиков на сервер
  adjust                 — отправить adjust-запрос (управляющие сигналы)
  manual                 — ручной ввод: URL, JSON [, METHOD]
  show                   — показать текущие параметры
  help                   — показать это сообщение
  exit                   — выйти
""")

    def show(self):
        print(f"""
MAC: {self.mac_address}
IP: {self.ip_address}
Температура: {self.temperature}
Влажность: {self.humidity}
Освещённость: {self.light}
Module ID: {self.module_id}
""")

def main():
    bot = ManualBot()
    print("Manual SmartGreenhouse Bot (CLI)")
    bot.help()
    while True:
        try:
            cmd = input(">>> ").strip()
            if not cmd:
                continue
            if cmd == "exit":
                break
            elif cmd == "help":
                bot.help()
            elif cmd == "connect":
                bot.connect()
            elif cmd == "status":
                bot.status()
            elif cmd == "send":
                bot.send_sensor_values()
            elif cmd == "adjust":
                bot.adjust()
            elif cmd == "manual":
                bot.manual()
            elif cmd == "show":
                bot.show()
            elif cmd.startswith("set "):
                parts = cmd.split()
                if len(parts) == 3:
                    _, what, value = parts
                    if what == "mac":
                        bot.set_mac(value)
                    elif what == "ip":
                        bot.set_ip(value)
                    elif what in ("temperature", "humidity", "light"):
                        bot.set_param(what, value)
                    else:
                        print("Неизвестный параметр для set")
                else:
                    print("Формат: set [mac|ip|temperature|humidity|light] значение")
            else:
                print("Неизвестная команда. help — список команд.")
        except KeyboardInterrupt:
            print("\nВыход.")
            break
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
