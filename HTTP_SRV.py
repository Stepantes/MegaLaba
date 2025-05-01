from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# Шаблонные (целевые) параметры
TARGET_TEMPERATURE = 25  # °C
TARGET_HUMIDITY = 50     # %
TARGET_LIGHT = 10        # усл. ед.

@app.route('/adjust', methods=['POST'])
def adjust_parameters():
    try:
        data = request.get_json()
        
        # Проверяем наличие всех полей
        if not all(key in data for key in ['Temperature', 'Humidity', 'Light']):
            return jsonify({"error": "Missing parameters"}), 400
        
        temperature = float(data['Temperature'])
        humidity = float(data['Humidity'].strip('%'))
        light = float(data['Light'])
        
        # Определяем, нужно ли подавать напряжение (ON/OFF)
        adjustments = {
            "Temperature": "ON" if temperature < TARGET_TEMPERATURE else "OFF",
            "Humidity": "ON" if humidity < TARGET_HUMIDITY else "OFF",
            "Light": "ON" if light < TARGET_LIGHT else "OFF",
        }
        
        return jsonify(adjustments)
    
    except ValueError:
        return jsonify({"error": "Invalid data format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)