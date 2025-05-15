import requests
import time
import threading
import uuid
import socket
import json
import random

class GreenhouseModuleSimulator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "GreenhouseModule/2.0",
            "Accept": "application/json"
        })
        
        # Настройки сервера
        self.server_url = "http://127.0.0.1:5000"
        
        # Параметры модуля
        self.state = {
            "is_connected": False,
            "is_active": False,
            "is_claimed": False,
            "should_send_data": False,
            "stop_thread": False,
            "module_id": None,
            "mac_address": self._generate_mac_address(),
            "ip_address": self._get_local_ip(),
            "update_interval": 5  # Интервал отправки данных в секундах
        }
        
        # Текущие показания датчиков
        self.sensor_data = {
            "temperature": 22.0,
            "humidity": 45.0,
            "light": 5000
        }
        
        # Настройки симуляции
        self.simulation_params = {
            "temperature_range": (15.0, 35.0),
            "humidity_range": (30.0, 80.0),
            "light_range": (1000, 10000),
            "variation_step": 0.5
        }

    def _generate_mac_address(self):
        """Генерирует случайный MAC-адрес"""
        return ':'.join(['{:02x}'.format(random.randint(0, 255)) for _ in range(6)])

    def _get_local_ip(self):
        """Получает локальный IP-адрес"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def connect_to_server(self):
        """Подключение к серверу"""
        try:
            data = {
                "mac_address": self.state["mac_address"],
                "ip_address": self.state["ip_address"]
            }
            
            response = self.session.post(
                f"{self.server_url}/api/modules/connect",
                json=data
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                self.state.update({
                    "is_connected": True,
                    "module_id": response_data.get("module_id"),
                    "is_active": response_data.get("is_active", False),
                    "is_claimed": not response_data.get("exists", True)
                })
                
                print(f"\n{'Модуль обновлен' if response_data.get('exists') else 'Новый модуль зарегистрирован'}")
                print(f"ID: {self.state['module_id']}")
                print(f"MAC: {self.state['mac_address']}")
                print(f"IP: {self.state['ip_address']}")
                print(f"Статус: {'Активен' if self.state['is_active'] else 'Неактивен'}")
                print(f"Привязка: {'Есть' if self.state['is_claimed'] else 'Нет'}")
                
                return True
            else:
                print(f"\nОшибка подключения (код {response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"\nОшибка при подключении: {e}")
            return False

    def check_status(self):
        """Проверяет статус модуля на сервере"""
        try:
            headers = {
                "X-Module-MAC": self.state["mac_address"],
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.server_url}/api/modules/status",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.state.update({
                    "is_active": data["is_active"],
                    "is_claimed": data["is_claimed"]
                })
                
                print("\nТекущий статус модуля:")
                print(f"ID: {self.state['module_id']}")
                print(f"Активен: {'ДА' if self.state['is_active'] else 'НЕТ'}")
                print(f"Привязан: {'ДА' if self.state['is_claimed'] else 'НЕТ'}")
                return True
            else:
                print(f"\nОшибка запроса статуса (код {response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            print(f"\nОшибка при проверке статуса: {e}")
            return False

    def send_sensor_data(self):
        """Отправляет данные датчиков на сервер"""
        try:
            if not self.state["is_active"]:
                return False

            # Имитация изменения показаний датчиков
            self._simulate_sensor_changes()
            
            data = {
                "Temperature": self.sensor_data["temperature"],
                "Humidity": self.sensor_data["humidity"],
                "Light": self.sensor_data["light"]
            }
            
            headers = {
                "X-Module-MAC": self.state["mac_address"],
                "X-Module-ID": str(self.state["module_id"])
            }
            
            response = self.session.post(
                f"{self.server_url}/adjust",
                json=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"\nДанные отправлены: {data}")
                print(f"Ответ сервера: {response.json()}")
                return True
            else:
                print(f"\nОшибка отправки данных (код {response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            print(f"\nОшибка при отправке данных: {e}")
            return False

    def _simulate_sensor_changes(self):
        """Имитирует изменения показаний датчиков"""
        # Температура
        self.sensor_data["temperature"] += random.uniform(
            -self.simulation_params["variation_step"],
            self.simulation_params["variation_step"]
        )
        self.sensor_data["temperature"] = max(
            min(self.sensor_data["temperature"], self.simulation_params["temperature_range"][1]),
            self.simulation_params["temperature_range"][0]
        )
        
        # Влажность
        self.sensor_data["humidity"] += random.uniform(
            -self.simulation_params["variation_step"],
            self.simulation_params["variation_step"]
        )
        self.sensor_data["humidity"] = max(
            min(self.sensor_data["humidity"], self.simulation_params["humidity_range"][1]),
            self.simulation_params["humidity_range"][0]
        )
        
        # Освещенность
        self.sensor_data["light"] = random.randint(
            self.simulation_params["light_range"][0],
            self.simulation_params["light_range"][1]
        )

    def data_sending_loop(self):
        """Цикл отправки данных"""
        while not self.state["stop_thread"]:
            if self.state["is_active"] and self.state["is_connected"]:
                self.send_sensor_data()
            time.sleep(self.state["update_interval"])

    def change_network_settings(self):
        """Изменяет сетевые настройки модуля"""
        print("\nТекущие сетевые настройки:")
        print(f"1. MAC-адрес: {self.state['mac_address']}")
        print(f"2. IP-адрес: {self.state['ip_address']}")
        
        choice = input("Что изменить? (1-MAC, 2-IP, 0-отмена): ")
        
        if choice == "1":
            new_mac = input("Введите новый MAC-адрес (формат XX:XX:XX:XX:XX:XX): ")
            if len(new_mac.split(':')) == 6:
                self.state["mac_address"] = new_mac
                print("MAC-адрес изменен. Необходимо переподключиться к серверу.")
            else:
                print("Неверный формат MAC-адреса!")
                
        elif choice == "2":
            new_ip = input("Введите новый IP-адрес: ")
            self.state["ip_address"] = new_ip
            print("IP-адрес изменен. Необходимо переподключиться к серверу.")
            
        elif choice == "0":
            return
            
        else:
            print("Неверный выбор!")

    def show_sensor_data(self):
        """Показывает текущие показания датчиков"""
        print("\nТекущие показания датчиков:")
        print(f"Температура: {self.sensor_data['temperature']:.1f}°C")
        print(f"Влажность: {self.sensor_data['humidity']:.1f}%")
        print(f"Освещенность: {self.sensor_data['light']} люкс")

    def manual_control_menu(self):
        """Меню ручного управления"""
        while not self.state["stop_thread"]:
            print("\nМеню управления модулем:")
            print("1. Подключиться к серверу")
            print("2. Проверить статус")
            print("3. Показать данные датчиков")
            print("4. Изменить сетевые настройки")
            print("5. Выход")
            
            choice = input("Выберите действие (1-5): ")
            
            if choice == "1":
                if not self.state["is_connected"]:
                    self.connect_to_server()
                else:
                    print("\nМодуль уже подключен!")
                    
            elif choice == "2":
                if self.state["is_connected"]:
                    self.check_status()
                else:
                    print("\nСначала подключитесь к серверу!")
                    
            elif choice == "3":
                self.show_sensor_data()
                
            elif choice == "4":
                self.change_network_settings()
                
            elif choice == "5":
                self.state["stop_thread"] = True
                print("\nЗавершение работы модуля...")
                
            else:
                print("Неверный выбор!")

    def run(self):
        """Запускает модуль"""
        print("Симулятор модуля умной теплицы")
        print(f"MAC-адрес: {self.state['mac_address']}")
        print(f"IP-адрес: {self.state['ip_address']}")
        
        # Запуск потока отправки данных
        data_thread = threading.Thread(target=self.data_sending_loop)
        data_thread.daemon = True
        data_thread.start()
        
        # Основной интерфейс
        try:
            self.manual_control_menu()
        except KeyboardInterrupt:
            self.state["stop_thread"] = True
            print("\nМодуль остановлен")
        
        data_thread.join()

if __name__ == "__main__":
    module = GreenhouseModuleSimulator()
    module.run()