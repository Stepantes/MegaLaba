import { useEffect, useState } from 'react';
import { useAuth } from '../Assets/AuthContext';
import { useNavigate } from 'react-router-dom';
import Layout from './Layout';

const AvailableModules = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [modules, setModules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);
    const [claimingId, setClaimingId] = useState(null);

    useEffect(() => {
        if (!user) {
            navigate('/login');
        } else {
            fetchAvailableModules();
        }
    }, [user, navigate]);

    const fetchAvailableModules = async () => {
        try {
            setLoading(true);
            setError(null);
            setSuccessMessage(null);
            
            const response = await fetch('http://localhost:5000/api/modules/available', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || 'Ошибка загрузки модулей');
            }
            
            const data = await response.json();
            // Фильтруем только модули без владельца (id === null)
            setModules(data);
            
        } catch (error) {
            console.error('Ошибка получения модулей:', error);
            setError(error.message);
            if (error.message.includes('401')) {
                navigate('/login');
            }
        } finally {
            setLoading(false);
        }
    };

    const claimModule = async (moduleId) => {
        try {
            setClaimingId(moduleId);
            setError(null);
            setSuccessMessage(null);

            const response = await fetch(`http://localhost:5000/api/modules/${moduleId}/claim`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || 'Ошибка при подключении модуля');
            }
            
            setSuccessMessage('Модуль успешно подключен!');
            fetchAvailableModules(); // Обновляем список
            
        } catch (error) {
            console.error('Ошибка подключения модуля:', error);
            setError(error.message);
        } finally {
            setClaimingId(null);
        }
    };

    if (!user) return null;

    return (
        <Layout>
            <div className="available-modules-container">
                <h2>Доступные модули</h2>
                
                {error && (
                    <div className="alert alert-error">
                        <span>⚠</span>
                        {error}
                    </div>
                )}
                
                {successMessage && (
                    <div className="alert alert-success">
                        <span>✓</span>
                        {successMessage}
                    </div>
                )}

                {loading ? (
                    <div className="loading-spinner"></div>
                ) : modules.length === 0 ? (
                    <p className="no-modules-message">Нет доступных модулей для подключения</p>
                ) : (
                    <div className="modules-grid">
                        {modules.map(module => (
                            <div key={module.module_id} className="module-card">
                                <div className="module-header">
                                    <h3>{module.module_name || `Модуль ${module.module_id}`}</h3>
                                    <span className={`status-badge ${module.is_active ? 'active' : 'inactive'}`}>
                                        {module.is_active ? 'Активен' : 'Не активен'}
                                    </span>
                                </div>
                                
                                <div className="module-details">
                                    <p><strong>MAC:</strong> {module.mac_address}</p>
                                    <p><strong>IP:</strong> {module.ip_address || 'Неизвестно'}</p>
                                </div>
                                
                                <button 
                                    onClick={() => claimModule(module.module_id)}
                                    className="claim-button"
                                    disabled={claimingId === module.module_id}
                                >
                                    {claimingId === module.module_id ? (
                                        <>
                                            <span className="button-spinner"></span>
                                            Подключение...
                                        </>
                                    ) : (
                                        'Подключить'
                                    )}
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </Layout>
    );
};

export default AvailableModules;