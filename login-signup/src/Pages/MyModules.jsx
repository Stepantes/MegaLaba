import { useEffect, useState } from 'react';
import { useAuth } from '../Assets/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from './Layout';
import '../Pages/MyModules.css';

const MyModules = () => {
    const { user, makeRequest } = useAuth();
    const navigate = useNavigate();
    const [modules, setModules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [editingModule, setEditingModule] = useState(null);
    const [formData, setFormData] = useState({
        module_name: '',
        target_temperature: '',
        target_humidity: '',
        target_lighting: ''
    });

    useEffect(() => {
        if (!user) {
            navigate('/login');
        } else {
            fetchUserModules();
        }
    }, [user, navigate]);

    const fetchUserModules = async () => {
        try {
            setLoading(true);
            setError(null);
            
            // Добавляем контрольный параметр запроса
            const timestamp = Date.now();
            const response = await axios.get(
                `http://localhost:5000/api/modules/user?check=${timestamp}`,
                { withCredentials: true }
            );
            
            // Валидация ответа
            if (!Array.isArray(response.data)) {
                throw new Error('Invalid response format');
            }
            
            setModules(response.data);
            
        } catch (error) {
            if (error.response?.status === 401) {
                navigate('/login');
            } else {
                setError('Ошибка загрузки данных');
            }
        } finally {
            setLoading(false);
        }
    };

    const toggleModuleStatus = async (moduleId, currentStatus) => {
        try {
            setLoading(true);
            setError(null);
    
            const data = await makeRequest(
                'PUT',
                `/api/modules/${moduleId}/status`,
                { is_active: !currentStatus }
            );
    
            // Обновляем состояние модулей
            setModules(modules.map(module => 
                module.module_id === moduleId 
                    ? { ...module, is_active: !currentStatus } 
                    : module
            ));
    
        } catch (error) {
            console.error('Ошибка переключения статуса:', error);
            setError(error.response?.data?.error || 'Ошибка переключения статуса');
        } finally {
            setLoading(false);
        }
    };

    const startEditing = (module) => {
        setEditingModule(module.module_id);
        setFormData({
            module_name: module.module_name || '',
            target_temperature: module.target_temperature || '',
            target_humidity: module.target_humidity || '',
            target_lighting: module.target_lighting || ''
        });
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const saveSettings = async (moduleId) => {
        try {
            setLoading(true);
            setError(null);

            const data = await makeRequest(
                'PUT',
                `/api/modules/${moduleId}/settings`,
                {
                    module_name: formData.module_name,
                    target_temperature: parseFloat(formData.target_temperature),
                    target_humidity: parseFloat(formData.target_humidity),
                    target_lighting: parseInt(formData.target_lighting)
                }
            );
            
            setEditingModule(null);
            fetchUserModules();
            
        } catch (error) {
            console.error('Ошибка сохранения настроек:', error);
            setError(error.response?.data?.error || 'Ошибка сохранения настроек');
        } finally {
            setLoading(false);
        }
    };

    const cancelEditing = () => {
        setEditingModule(null);
        setError(null);
    };

    if (!user) return null;

    return (
        <Layout>
            <div className="my-modules-container">
                <h2>Мои модули</h2>
                
                {error && (
                    <div className="alert alert-error">
                        <span>⚠</span>
                        {error}
                    </div>
                )}

                {loading ? (
                    <div className="loading-spinner"></div>
                ) : modules.length === 0 ? (
                    <div className="no-modules-message">
                        <p>У вас нет подключенных модулей</p>
                        <button 
                            onClick={() => navigate('/available-modules')}
                            className="connect-button"
                        >
                            Подключить модуль
                        </button>
                    </div>
                ) : (
                    <div className="modules-grid">
                        {modules.map(module => (
                            <div key={module.module_id} className="module-card">
                                {editingModule === module.module_id ? (
                                    <div className="module-edit-form">
                                        <div className="form-group">
                                            <label>Название модуля:</label>
                                            <input
                                                type="text"
                                                name="module_name"
                                                value={formData.module_name}
                                                onChange={handleInputChange}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Целевая температура (°C):</label>
                                            <input
                                                type="number"
                                                name="target_temperature"
                                                value={formData.target_temperature}
                                                onChange={handleInputChange}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Целевая влажность (%):</label>
                                            <input
                                                type="number"
                                                name="target_humidity"
                                                value={formData.target_humidity}
                                                onChange={handleInputChange}
                                                min="0"
                                                max="100"
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Целевая освещенность:</label>
                                            <input
                                                type="number"
                                                name="target_lighting"
                                                value={formData.target_lighting}
                                                onChange={handleInputChange}
                                                min="0"
                                            />
                                        </div>
                                        <div className="form-actions">
                                            <button 
                                                onClick={() => saveSettings(module.module_id)}
                                                className="save-button"
                                            >
                                                Сохранить
                                            </button>
                                            <button 
                                                onClick={cancelEditing}
                                                className="cancel-button"
                                            >
                                                Отмена
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        <div className="module-header">
                                            <h3>{module.module_name || `Модуль ${module.module_id}`}</h3>
                                            <span className={`status-badge ${module.is_active ? 'active' : 'inactive'}`}>
                                                {module.is_active ? 'Активен' : 'Не активен'}
                                            </span>
                                        </div>
                                        
                                        <div className="module-details">
                                            <p><strong>MAC:</strong> {module.mac_address}</p>
                                            <p><strong>IP:</strong> {module.ip_address || 'Неизвестно'}</p>
                                            <p><strong>Температура:</strong> {module.target_temperature || 'Не задано'}°C</p>
                                            <p><strong>Влажность:</strong> {module.target_humidity || 'Не задано'}%</p>
                                            <p><strong>Освещенность:</strong> {module.target_lighting || 'Не задано'}</p>
                                        </div>
                                        
                                        <div className="module-actions">
                                            <button 
                                                onClick={() => toggleModuleStatus(module.module_id, module.is_active)}
                                                className={`toggle-button ${module.is_active ? 'active' : ''}`}
                                            >
                                                {module.is_active ? 'Выключить' : 'Включить'}
                                            </button>
                                            <button 
                                                onClick={() => startEditing(module)}
                                                className="edit-button"
                                            >
                                                Настроить
                                            </button>
                                        </div>
                                    </>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </Layout>
    );
};

export default MyModules;