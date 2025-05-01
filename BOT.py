import requests
import time
import threading

# Настройки сервера
SERVER_URL = "http://127.0.0.1:5000/adjust"

# Текущие параметры (можно менять во время работы)
current_params = {
    "Temperature": 40,
    "Humidity": "20%",
    "Light": 5
}

# Флаг для остановки потока
stop_thread = False

def send_requests():
    """Отправляет запросы на сервер каждую секунду."""
    global stop_thread, current_params
    while not stop_thread:
        try:
            response = requests.post(SERVER_URL, json=current_params)
            print(f"\nОтправлено: {current_params} | Ответ: {response.json()}")
        except Exception as e:
            print(f"Ошибка: {e}")
        time.sleep(1)

def user_input_handler():
    """Обрабатывает ввод пользователя для изменения параметров."""
    global stop_thread, current_params
    while not stop_thread:
        print("\nТекущие параметры:")
        print(f"1. Temperature: {current_params['Temperature']}°C")
        print(f"2. Humidity: {current_params['Humidity']}")
        print(f"3. Light: {current_params['Light']}")
        print("4. Выход")
        
        choice = input("Выберите параметр для изменения (1-4): ")
        
        if choice == "1":
            try:
                value = float(input("Новое значение Temperature (°C): "))
                current_params["Temperature"] = value
            except ValueError:
                print("Ошибка: введите число!")
        elif choice == "2":
            try:
                value = input("Новое значение Humidity (например, 30%): ")
                current_params["Humidity"] = value
            except ValueError:
                print("Ошибка: введите число!")
        elif choice == "3":
            try:
                value = float(input("Новое значение Light: "))
                current_params["Light"] = value
            except ValueError:
                print("Ошибка: введите число!")
        elif choice == "4":
            stop_thread = True
            print("Завершение работы...")
        else:
            print("Неверный выбор!")

if __name__ == "__main__":
    print("Клиент запущен. Изменяйте параметры в реальном времени.")
    
    # Запуск потока для отправки запросов
    request_thread = threading.Thread(target=send_requests)
    request_thread.start()
    
    # Основной поток для обработки ввода
    user_input_handler()
    
    # Ожидание завершения потока
    request_thread.join()
    print("Клиент остановлен.")