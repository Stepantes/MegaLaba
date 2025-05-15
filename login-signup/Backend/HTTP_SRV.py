from flask import Flask, request, jsonify, session  # Добавлен session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_session import Session
from datetime import datetime, timedelta  # Добавлен timedelta
import os
from dotenv import load_dotenv
import logging  # Добавлен logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_COOKIE_NAME'] = 'greenhouse_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize extensions
db = SQLAlchemy(app)
Session(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configure logging
app.logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    modules = db.relationship('SmartGreenhouseModule', backref='owner', lazy=True)

class SmartGreenhouseModule(db.Model):
    __tablename__ = 'smart_greenhouse_modules'
    module_id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    module_name = db.Column(db.String(100))
    mac_address = db.Column(db.String(17), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    target_humidity = db.Column(db.Numeric(5,2))
    target_temperature = db.Column(db.Numeric(5,2))
    target_lighting = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



# Auth Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')

    if not login or not password:
        return jsonify({'error': 'Введите логин и пароль'}), 400

    if User.query.filter_by(login=login).first():
        return jsonify({'error': 'Пользователь с данным логином уже зарегистрирован'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(login=login, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Пользователь успешно создан'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')

    user = User.query.filter_by(login=login).first()
    if user and check_password_hash(user.password, password):
        login_user(user, remember=True)
        return jsonify({
            'message': 'Успешный вход',
            'user': {
                'id': user.id,
                'login': user.login
            }
        })
    return jsonify({'error': 'Неверно введены данные'}), 401

@app.route('/api/auth/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Выход'})

@app.route('/api/user')
@login_required
def get_user():
    return jsonify({
        'id': current_user.id,
        'login': current_user.login
    })

# Module Routes
@app.route('/api/modules/connect', methods=['POST'])
def connect_module():
    try:
        data = request.get_json()
        mac = data.get('mac_address')
        ip = data.get('ip_address')

        if not mac or not ip:
            return jsonify({"error": "Требуются MAC и IP адреса"}), 400

        module = SmartGreenhouseModule.query.filter_by(mac_address=mac).first()

        if module:
            module.ip_address = ip
            module.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({
                "message": "Модуль обновлен",
                "module_id": module.module_id,
                "is_active": module.is_active,
                "exists": True
            }), 200
        else:
            new_module = SmartGreenhouseModule(
                mac_address=mac,
                ip_address=ip,
                is_active=False
            )
            db.session.add(new_module)
            db.session.commit()
            return jsonify({
                "message": "Модуль зарегистрирован",
                "module_id": new_module.module_id,
                "is_active": new_module.is_active,
                "exists": False
            }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/modules/available', methods=['GET'])
@login_required
def get_available_modules():
    try:
        # Получаем только модули, не привязанные ни к какому пользователю
        modules = SmartGreenhouseModule.query.filter(
            SmartGreenhouseModule.id.is_(None)
        ).all()
        
        result = [{
            'module_id': m.module_id,
            'module_name': m.module_name if m.module_name else f"Модуль {m.module_id}",
            'mac_address': m.mac_address,
            'ip_address': m.ip_address,
            'is_active': m.is_active,
            'is_claimed': m.id is not None  # Всегда False, так как мы фильтруем по id=None
        } for m in modules]
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/modules/<int:module_id>/claim', methods=['PUT'])
@login_required
def claim_module(module_id):
    try:
        module = SmartGreenhouseModule.query.get(module_id)
        if not module:
            return jsonify({'error': 'Module not found'}), 404
        
        if module.id is not None:
            return jsonify({'error': 'Module already claimed'}), 400
        
        module.id = current_user.id
        db.session.commit()
        return jsonify({'message': 'Module claimed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/modules/<int:module_id>/settings', methods=['PUT'])
@login_required
def update_module_settings(module_id):
    try:
        module = SmartGreenhouseModule.query.get(module_id)
        if not module or module.id != current_user.id:
            return jsonify({'error': 'Module not found or not owned by user'}), 404
        
        data = request.get_json()
        
        # Обновляем все параметры
        module.module_name = data.get('module_name', module.module_name)
        module.target_temperature = data.get('target_temperature', module.target_temperature)
        module.target_humidity = data.get('target_humidity', module.target_humidity)
        module.target_lighting = data.get('target_lighting', module.target_lighting)
        
        db.session.commit()
        return jsonify({
            'message': 'Settings updated successfully',
            'module': {
                'module_id': module.module_id,
                'module_name': module.module_name,
                'target_temperature': module.target_temperature,
                'target_humidity': module.target_humidity,
                'target_lighting': module.target_lighting
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/modules/user', methods=['GET'])
@login_required
def get_user_modules():
    try:
        # Журналирование для отладки
        app.logger.info(f"Запрос модулей для пользователя ID: {current_user.id}, Login: {current_user.login}")
        
        # Явная проверка принадлежности модулей
        modules = db.session.query(SmartGreenhouseModule).filter(
            SmartGreenhouseModule.id == current_user.id
        ).all()
        
        if not modules:
            app.logger.info(f"Пользователь {current_user.id} не имеет модулей")
        
        result = [{
            'module_id': m.module_id,
            'module_name': m.module_name,
            'mac_address': m.mac_address,
            # ... остальные поля
        } for m in modules]
        
        return jsonify(result), 200
        
    except Exception as e:
        app.logger.error(f"Ошибка в get_user_modules: {str(e)}")
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/modules/status', methods=['GET'])
@login_required
def get_module_status():
    try:
        module_mac = request.headers.get('X-Module-MAC')
        if not module_mac:
            return jsonify({"error": "Missing MAC address"}), 400
        
        module = SmartGreenhouseModule.query.filter_by(
            mac_address=module_mac,
            id=current_user.id
        ).first()
        
        if not module:
            return jsonify({"error": "Module not found"}), 404
        
        return jsonify({
            "module_id": module.module_id,
            "is_active": module.is_active,
            "is_claimed": True
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/modules/<int:module_id>/status', methods=['PUT'])
@login_required
def update_module_status(module_id):
    try:
        # Проверяем принадлежность модуля текущему пользователю
        module = SmartGreenhouseModule.query.filter_by(
            module_id=module_id,
            id=current_user.id
        ).first()

        if not module:
            return jsonify({
                'error': 'Module not found or not owned by user'
            }), 404

        data = request.get_json()
        new_status = data.get('is_active', False)
        
        # Обновляем статус
        module.is_active = new_status
        db.session.commit()

        return jsonify({
            'message': 'Module status updated',
            'module_id': module.module_id,
            'is_active': module.is_active
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500

# Adjust Parameters
TARGET_TEMPERATURE = 25  # °C
TARGET_HUMIDITY = 50     # %
TARGET_LIGHT = 10        # arbitrary units

@app.route('/adjust', methods=['POST'])
@login_required
def adjust_parameters():
    try:
        # Проверяем заголовки аутентификации
        module_mac = request.headers.get('X-Module-MAC')
        module_id = request.headers.get('X-Module-ID')
        
        if not module_mac or not module_id:
            return jsonify({"error": "Missing authentication headers"}), 401
        
        # Проверяем принадлежность модуля
        module = SmartGreenhouseModule.query.filter_by(
            module_id=module_id,
            mac_address=module_mac,
            id=current_user.id
        ).first()
        
        if not module:
            return jsonify({"error": "Module not found or access denied"}), 403
        
        # Получаем данные
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Валидация данных
        try:
            temperature = float(data['Temperature'])
            humidity = float(data['Humidity'])  # Убедитесь, что клиент отправляет число
            light = float(data['Light'])
        except (KeyError, ValueError):
            return jsonify({"error": "Invalid data format"}), 400
        
        # Логика обработки (пример)
        adjustments = {
            "Temperature": "ON" if temperature < module.target_temperature else "OFF",
            "Humidity": "ON" if humidity < module.target_humidity else "OFF",
            "Light": "ON" if light < module.target_lighting else "OFF",
        }
        
        return jsonify(adjustments), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)