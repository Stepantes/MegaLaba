
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_session import Session
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

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

db = SQLAlchemy(app)
Session(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

app.logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    modules = db.relationship('SmartGreenhouseModule', backref='owner', lazy=True)
    favorite_greenhouse_id = db.Column(db.Integer, db.ForeignKey('greenhouses.greenhouse_id', ondelete='SET NULL'), nullable=True)  # <-- добавьте эту строку

    def to_dict(self):
        return {
            'id': self.id,
            'login': self.login,
            'favorite_greenhouse_id': self.favorite_greenhouse_id  
        }

class Greenhouse(db.Model):
    __tablename__ = 'greenhouses'
    greenhouse_id = db.Column(db.Integer, primary_key=True)
    greenhouse_name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    main_module_id = db.Column(db.Integer, db.ForeignKey('smart_greenhouse_modules.module_id', ondelete='SET NULL'), nullable=False)

    def to_dict(self):
        return {
            'greenhouse_id': self.greenhouse_id,
            'greenhouse_name': self.greenhouse_name,
            'owner_id': self.owner_id,
            'main_module_id': self.main_module_id
        }

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
    greenhouse_id = db.Column(db.Integer, db.ForeignKey('greenhouses.greenhouse_id', ondelete='SET NULL'), nullable=True)

    last_temperature = db.Column(db.Numeric(5,2))
    last_temperature_updated = db.Column(db.DateTime)
    last_humidity = db.Column(db.Numeric(5,2))
    last_humidity_updated = db.Column(db.DateTime)
    last_light = db.Column(db.Integer)
    last_light_updated = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'module_id': self.module_id,
            'module_name': self.module_name,
            'mac_address': self.mac_address,
            'ip_address': self.ip_address,
            'target_humidity': float(self.target_humidity) if self.target_humidity is not None else None,
            'target_temperature': float(self.target_temperature) if self.target_temperature is not None else None,
            'target_lighting': self.target_lighting,
            'is_active': self.is_active,
            'is_claimed': self.id is not None,
            'greenhouse_id': self.greenhouse_id,
            'last_temperature': float(self.last_temperature) if self.last_temperature is not None else None,
            'last_temperature_updated': self.last_temperature_updated.isoformat() if self.last_temperature_updated else None,
            'last_humidity': float(self.last_humidity) if self.last_humidity is not None else None,
            'last_humidity_updated': self.last_humidity_updated.isoformat() if self.last_humidity_updated else None,
            'last_light': self.last_light,
            'last_light_updated': self.last_light_updated.isoformat() if self.last_light_updated else None,
        }

class SensorHistory(db.Model):
    __tablename__ = 'sensor_history'
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, nullable=False)
    value_type = db.Column(db.String(32), nullable=False) 
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

@app.route('/api/greenhouses/<int:greenhouse_id>/delete', methods=['DELETE'])
@login_required
def delete_greenhouse(greenhouse_id):
    greenhouse = Greenhouse.query.filter_by(greenhouse_id=greenhouse_id, owner_id=current_user.id).first()
    if not greenhouse:
        return jsonify({'error': 'Теплица не найдена или не принадлежит вам'}), 404

    modules = SmartGreenhouseModule.query.filter_by(greenhouse_id=greenhouse_id).all()
    for module in modules:
        module.greenhouse_id = None

    if greenhouse.main_module_id:
        main_module = SmartGreenhouseModule.query.get(greenhouse.main_module_id)
        if main_module and main_module.greenhouse_id == greenhouse_id:
            main_module.greenhouse_id = None

    user = User.query.get(current_user.id)
    if user.favorite_greenhouse_id == greenhouse_id:
        user.favorite_greenhouse_id = None

    db.session.delete(greenhouse)
    db.session.commit()
    return jsonify({'message': 'Теплица успешно удалена'}), 200

@app.route('/api/modules/user', methods=['GET'])
@login_required
def get_user_modules():
    modules = SmartGreenhouseModule.query.filter_by(id=current_user.id).all()
    return jsonify([m.to_dict() for m in modules]), 200

@app.route('/api/auth/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Выход'})

@app.route('/api/user')
@login_required
def get_user():
    return jsonify(current_user.to_dict())

@app.route('/api/greenhouses/<int:greenhouse_id>/main-module', methods=['PUT'])
@login_required
def set_main_module(greenhouse_id):
    data = request.get_json()
    new_main_id = data.get('main_module_id')
    greenhouse = Greenhouse.query.filter_by(greenhouse_id=greenhouse_id, owner_id=current_user.id).first()
    if not greenhouse:
        return jsonify({'error': 'Теплица не найдена или не принадлежит вам'}), 404

    new_main = SmartGreenhouseModule.query.filter_by(module_id=new_main_id, greenhouse_id=greenhouse_id).first()
    if not new_main:
        return jsonify({'error': 'Модуль не найден или не принадлежит этой теплице'}), 400

    greenhouse.main_module_id = new_main.module_id
    db.session.commit()

    secondary_modules = SmartGreenhouseModule.query.filter(
        SmartGreenhouseModule.greenhouse_id == greenhouse_id,
        SmartGreenhouseModule.module_id != new_main.module_id
    ).all()
    for sec_mod in secondary_modules:
        sec_mod.target_temperature = new_main.target_temperature
        sec_mod.target_humidity = new_main.target_humidity
        sec_mod.target_lighting = new_main.target_lighting
    db.session.commit()

    return jsonify({'message': 'Главный модуль успешно изменён и параметры синхронизированы'}), 200

@app.route('/api/user/favorite-greenhouse', methods=['PUT'])
@login_required
def set_favorite_greenhouse():
    data = request.get_json()
    greenhouse_id = data.get('greenhouse_id')
    user = User.query.get(current_user.id)
    if greenhouse_id is None:
        user.favorite_greenhouse_id = None
        db.session.commit()
        return jsonify({'message': 'Избранная теплица сброшена'}), 200
    greenhouse = Greenhouse.query.filter_by(greenhouse_id=greenhouse_id, owner_id=current_user.id).first()
    if not greenhouse:
        return jsonify({'error': 'Теплица не найдена или не принадлежит вам'}), 404
    user.favorite_greenhouse_id = greenhouse_id
    db.session.commit()
    return jsonify({'message': 'Избранная теплица обновлена'}), 200

@app.route('/api/user/favorite-greenhouse', methods=['GET'])
@login_required
def get_favorite_greenhouse():
    user = User.query.get(current_user.id)
    if user and user.favorite_greenhouse_id:
        greenhouse = Greenhouse.query.get(user.favorite_greenhouse_id)
        if greenhouse:
            modules = SmartGreenhouseModule.query.filter_by(greenhouse_id=greenhouse.greenhouse_id).all()
            greenhouse_dict = greenhouse.to_dict()
            greenhouse_dict['modules'] = [m.to_dict() for m in modules]
            return jsonify(greenhouse_dict), 200
    return jsonify(None), 200

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
        modules = SmartGreenhouseModule.query.filter(
            SmartGreenhouseModule.id.is_(None)
        ).all()
        result = [m.to_dict() for m in modules]
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

@app.route('/api/modules/<int:module_id>/settings', methods=['GET'])
def get_module_settings(module_id):
    module = SmartGreenhouseModule.query.get(module_id)
    if not module:
        return jsonify({'error': 'Module not found'}), 404
    return jsonify({
        "target_temperature": float(module.target_temperature) if module.target_temperature is not None else None,
        "target_humidity": float(module.target_humidity) if module.target_humidity is not None else None,
        "target_lighting": module.target_lighting
    }), 200

@app.route('/api/modules/<int:module_id>/settings', methods=['PUT'])
@login_required
def update_module_settings(module_id):
    module = SmartGreenhouseModule.query.get(module_id)
    if not module or module.id != current_user.id:
        return jsonify({'error': 'Module not found or not owned by user'}), 404

    data = request.get_json()
    if 'target_temperature' in data:
        try:
            module.target_temperature = float(data['target_temperature'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Некорректное значение температуры'}), 400
    if 'target_humidity' in data:
        try:
            module.target_humidity = float(data['target_humidity'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Некорректное значение влажности'}), 400
    if 'target_lighting' in data:
        try:
            module.target_lighting = int(float(data['target_lighting']))
        except (ValueError, TypeError):
            return jsonify({'error': 'Некорректное значение освещённости'}), 400

    db.session.commit()
    return jsonify({'message': 'Настройки модуля обновлены'}), 200

@app.route('/api/modules/status', methods=['GET'])
def get_module_status():
    try:
        module_mac = request.headers.get('X-Module-MAC')
        if not module_mac:
            return jsonify({"error": "Missing MAC address"}), 400

        module = SmartGreenhouseModule.query.filter_by(
            mac_address=module_mac
        ).first()

        if not module:
            return jsonify({"error": "Module not found"}), 404

        return jsonify({
            "module_id": module.module_id,
            "is_active": module.is_active,
            "is_claimed": module.id is not None
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/modules/<int:module_id>/status', methods=['PUT'])
@login_required
def update_module_status(module_id):
    try:
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
        module.is_active = new_status
        db.session.commit()

        return jsonify({
            'message': 'Module status updated',
            'module': module.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/greenhouses/create', methods=['POST'])
@login_required
def create_greenhouse():
    data = request.get_json()
    name = data.get('greenhouse_name')
    main_module_id = data.get('main_module_id')
    secondary_module_ids = data.get('secondary_module_ids', [])
    if not name or not name.strip():
        return jsonify({'error': 'Имя теплицы обязательно'}), 400

    existing = Greenhouse.query.filter_by(owner_id=current_user.id, greenhouse_name=name.strip()).first()
    if existing:
        return jsonify({'error': 'У вас уже есть теплица с таким именем'}), 400

    if not main_module_id:
        return jsonify({'error': 'Главный модуль обязателен'}), 400

    main_module = SmartGreenhouseModule.query.get(int(main_module_id))
    if not main_module:
        return jsonify({'error': 'Главный модуль не найден'}), 400
    if main_module.greenhouse_id is not None:
        return jsonify({'error': 'Главный модуль уже привя��ан к другой теплице'}), 400

    for sec_id in secondary_module_ids:
        if str(sec_id) == str(main_module_id):
            return jsonify({'error': 'Главный модуль не может быть неосновным'}), 400
        module = SmartGreenhouseModule.query.get(int(sec_id))
        if not module:
            return jsonify({'error': f'Неосновной модуль {sec_id} не найден'}), 400
        if module.greenhouse_id is not None:
            return jsonify({'error': f'Модуль {module.module_name or module.module_id} уже привязан к другой теплице'}), 400

    # Создаём теплицу
    greenhouse = Greenhouse(
        greenhouse_name=name.strip(),
        owner_id=current_user.id,
        main_module_id=int(main_module_id)
    )
    db.session.add(greenhouse)
    db.session.commit()

    # Привязываем главный модуль
    main_module.greenhouse_id = greenhouse.greenhouse_id
    db.session.commit()

    # Копируем параметры главного модуля в неосновные и привязываем их
    for sec_id in secondary_module_ids:
        module = SmartGreenhouseModule.query.get(int(sec_id))
        if module:
            module.greenhouse_id = greenhouse.greenhouse_id
            module.target_temperature = main_module.target_temperature
            module.target_humidity = main_module.target_humidity
            module.target_lighting = main_module.target_lighting
    db.session.commit()

    return jsonify({'message': 'Теплица успешно создана'}), 201

@app.route('/api/greenhouses/user', methods=['GET'])
@login_required
def get_user_greenhouses():
    greenhouses = Greenhouse.query.filter_by(owner_id=current_user.id).all()
    return jsonify([g.to_dict() for g in greenhouses]), 200

# Adjust 
TARGET_TEMPERATURE = 25  
TARGET_HUMIDITY = 50    
TARGET_LIGHT = 10        

@app.route('/adjust', methods=['POST'])
def adjust_parameters():
    try:
        module_mac = request.headers.get('X-Module-MAC')
        module_id = request.headers.get('X-Module-ID')

        if not module_mac or not module_id:
            return jsonify({"error": "Missing authentication headers"}), 401

        module = SmartGreenhouseModule.query.filter_by(
            module_id=module_id,
            mac_address=module_mac
        ).first()

        if not module:
            return jsonify({"error": "Module not found or access denied"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        try:
            temperature = float(data['Temperature'])
            humidity = float(data['Humidity'])
            light = float(data['Light'])
        except (KeyError, ValueError):
            return jsonify({"error": "Invalid data format"}), 400

        adjustments = {
        "Temperature": "ON" if module.target_temperature is not None and temperature < float(module.target_temperature) else "OFF",
        "Humidity": "ON" if module.target_humidity is not None and humidity < float(module.target_humidity) else "OFF",
        "Light": "ON" if module.target_lighting is not None and float(light) < float(module.target_lighting) else "OFF",
}

        return jsonify(adjustments), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/modules/<int:module_id>/sensor-values', methods=['PUT'])
def update_sensor_values(module_id):
    data = request.get_json()
    module = SmartGreenhouseModule.query.get(module_id)
    if not module:
        return jsonify({'error': 'Модуль не найден'}), 404

    now = datetime.utcnow()

    if 'temperature' in data:
        module.last_temperature = data['temperature']
        module.last_temperature_updated = now
        db.session.add(SensorHistory(
            module_id=module_id,
            value_type='temperature',
            value=float(data['temperature']),
            timestamp=now
        ))
    if 'humidity' in data:
        module.last_humidity = data['humidity']
        module.last_humidity_updated = now
        db.session.add(SensorHistory(
            module_id=module_id,
            value_type='humidity',
            value=float(data['humidity']),
            timestamp=now
        ))
    if 'light' in data:
        module.last_light = data['light']
        module.last_light_updated = now
        db.session.add(SensorHistory(
            module_id=module_id,
            value_type='light',
            value=float(data['light']),
            timestamp=now
        ))

    db.session.commit()
    return jsonify({'message': 'Показания обновлены'}), 200


@app.route('/api/modules/<int:module_id>/history-24h', methods=['GET'])
@login_required
def get_module_history_24h(module_id):
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(hours=24)
    history = (
        db.session.query(SensorHistory)
        .filter(SensorHistory.module_id == module_id, SensorHistory.timestamp >= since)
        .order_by(SensorHistory.timestamp)
        .all()
    )
    result = {"temperature": [], "humidity": [], "light": []}
    for entry in history:
        if entry.value_type in result:
            result[entry.value_type].append({
                "time": entry.timestamp.isoformat(),
                "value": float(entry.value)
            })
    return jsonify(result), 200

@app.route('/api/modules/<int:module_id>/unclaim', methods=['PUT'])
@login_required
def unclaim_module(module_id):
    try:
        module = SmartGreenhouseModule.query.get(module_id)
        if not module or module.id != current_user.id:
            return jsonify({'error': 'Module not found or not owned by user'}), 404

        if not module.greenhouse_id:
            module.id = None
            module.is_active = False
            db.session.commit()
            return jsonify({'message': 'Module unclaimed and deactivated successfully'}), 200

        greenhouse = Greenhouse.query.filter_by(greenhouse_id=module.greenhouse_id).first()
        if not greenhouse:
            module.id = None
            module.greenhouse_id = None
            module.is_active = False
            db.session.commit()
            return jsonify({'message': 'Module unclaimed and deactivated successfully'}), 200

        if greenhouse.main_module_id == module.module_id:
            other_modules = SmartGreenhouseModule.query.filter(
                SmartGreenhouseModule.greenhouse_id == greenhouse.greenhouse_id,
                SmartGreenhouseModule.module_id != module.module_id
            ).all()

            if other_modules:
                new_main = other_modules[0]
                greenhouse.main_module_id = new_main.module_id
                db.session.commit()
            else:
                db.session.delete(greenhouse)
                db.session.commit()

        module.id = None
        module.greenhouse_id = None
        module.is_active = False
        db.session.commit()
        return jsonify({'message': 'Module unclaimed and deactivated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
