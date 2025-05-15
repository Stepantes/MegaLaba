import { useEffect, useState } from 'react';
import { useAuth } from '../Assets/AuthContext';
import { useNavigate } from 'react-router-dom';
import Layout from './Layout';

const Dashboard = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [modules, setModules] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) {
            navigate('/login');
        } else {
            fetchModules();
        }
    }, [user, navigate]);

    const fetchModules = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/modules/user', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            const data = await response.json();
            setModules(data);
        } catch (error) {
            console.error('Error fetching modules:', error);
        } finally {
            setLoading(false);
        }
    };

    const toggleModuleStatus = async (moduleId, currentStatus) => {
        try {
            const response = await fetch(`http://localhost:5000/api/modules/${moduleId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ is_active: !currentStatus })
            });
            
            if (response.ok) {
                fetchModules();
            }
        } catch (error) {
            console.error('Error toggling module status:', error);
        }
    };

    if (!user) return null;

    return (
        <Layout>
            <h2>Главная страница</h2>
            <div className="user-info">
                <p>ID: {user.id}</p>
                <p>Логин: {user.login}</p>
            </div>

            <h3>Мои модули</h3>
            {loading ? (
                <p>Загрузка...</p>
            ) : modules.length === 0 ? (
                <p>У вас нет зарегистрированных модулей</p>
            ) : (
                <div className="modules-list">
                    {modules.map(module => (
                        <div key={module.module_id} className="module-card">
                            <h4>{module.module_name}</h4>
                            <p>MAC: {module.mac_address}</p>
                            <p>IP: {module.ip_address || 'Неизвестно'}</p>
                            <p>Статус: {module.is_active ? 'Активен' : 'Не активен'}</p>
                            <button 
                                onClick={() => toggleModuleStatus(module.module_id, module.is_active)}
                                className={module.is_active ? 'active' : ''}
                            >
                                {module.is_active ? 'Выключить' : 'Включить'}
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </Layout>
    );
};

export default Dashboard;