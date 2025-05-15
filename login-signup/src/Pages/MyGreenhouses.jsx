import { useEffect, useState } from 'react';
import { useAuth } from '../Assets/AuthContext';
import { useNavigate } from 'react-router-dom';
import Layout from './Layout';
import './MyGreenhouses.css';

const AZURE = "#59a1b8";
const FAVORITE_KEY = "favorite_greenhouse_id";

const StarIcon = ({ filled, onClick, title }) => (
    <svg
        width="28"
        height="28"
        viewBox="0 0 28 28"
        fill={filled ? AZURE : "none"}
        stroke={AZURE}
        strokeWidth="2"
        style={{ cursor: onClick ? "pointer" : "default", marginBottom: 2 }}
        onClick={onClick}
        title={title}
    >
        <polygon
            points="14,3 17.7,10.5 26,11.2 19.5,16.8 21.5,24.5 14,20.2 6.5,24.5 8.5,16.8 2,11.2 10.3,10.5"
            fill={filled ? AZURE : "none"}
        />
    </svg>
);

const MyGreenhouses = () => {
    const { user, makeRequest } = useAuth();
    const navigate = useNavigate();
    const [greenhouses, setGreenhouses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [modules, setModules] = useState([]);
    const [form, setForm] = useState({
        greenhouse_name: '',
        main_module_id: '',
        secondary_module_ids: []
    });
    const [error, setError] = useState(null);
    const [creating, setCreating] = useState(false);

    // Избранная теплица
    const [favoriteId, setFavoriteId] = useState(() => {
        const stored = localStorage.getItem(FAVORITE_KEY);
        return stored || null;
    });

    useEffect(() => {
        if (!user) {
            navigate('/login');
        } else {
            fetchGreenhouses();
            fetchModules();
            fetchFavoriteFromBackend();
            fetchFavoriteFromBackend();
        }
    }, [user, navigate]);

    const fetchFavoriteFromBackend = async () => {
        try {
            const resp = await fetch('http://localhost:5000/api/user/favorite-greenhouse', {
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!resp.ok) {
                setFavoriteId(null);
                localStorage.removeItem(FAVORITE_KEY);
                return;
            }
            const greenhouse = await resp.json();
            if (greenhouse && greenhouse.greenhouse_id) {
                setFavoriteId(String(greenhouse.greenhouse_id));
                localStorage.setItem(FAVORITE_KEY, String(greenhouse.greenhouse_id));
            } else {
                setFavoriteId(null);
                localStorage.removeItem(FAVORITE_KEY);
            }
        } catch (e) {
            setFavoriteId(null);
            localStorage.removeItem(FAVORITE_KEY);
        }
    };

    const handleSetFavorite = async (greenhouseId) => {
        const idString = String(greenhouseId);
        try {
            await fetch('http://localhost:5000/api/user/favorite-greenhouse', {
                method: 'PUT',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ greenhouse_id: greenhouseId })
            });
            setFavoriteId(idString);
            localStorage.setItem(FAVORITE_KEY, idString);
        } catch (e) {
            alert('Ошибка при установке избранной теплицы');
        }
    };

    const handleDeleteGreenhouse = async (greenhouseId) => {
        if (!window.confirm('Вы уверены, что хотите удалить эту теплицу?')) return;
        try {
            setLoading(true);
            setError(null);
            const response = await fetch(`http://localhost:5000/api/greenhouses/${greenhouseId}/delete`, {
                method: 'DELETE',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Ошибка удаления теплицы');
            }
            if (favoriteId === String(greenhouseId)) {
                setFavoriteId(null);
                localStorage.removeItem(FAVORITE_KEY);
                await fetch('http://localhost:5000/api/user/favorite-greenhouse', {
                    method: 'PUT',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ greenhouse_id: null })
                });
            }
            fetchGreenhouses();
            fetchModules();
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const fetchGreenhouses = async () => {
        try {
            setLoading(true);
            const response = await fetch('http://localhost:5000/api/greenhouses/user', {
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            setGreenhouses(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('Ошибка загрузки теплиц:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchModules = async () => {
        try {
            const data = await makeRequest('GET', '/api/modules/user');
            setModules(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('Ошибка загрузки модулей:', error);
        }
    };

    const handleSetMainModule = async (greenhouseId, moduleId) => {
        try {
            await makeRequest('PUT', `/api/greenhouses/${greenhouseId}/main-module`, {
                main_module_id: moduleId
            });
            fetchGreenhouses();
            fetchModules();
        } catch (error) {
            setError(error.response?.data?.error || 'Ошибка смены главного модуля');
        }
    };

    const handleFormChange = (e) => {
        const { name, value, type, checked } = e.target;
        if (name === 'secondary_module_ids') {
            let newIds = [...form.secondary_module_ids];
            if (checked) {
                if (newIds.length < 3) newIds.push(value);
            } else {
                newIds = newIds.filter(id => id !== value);
            }
            setForm(f => ({ ...f, secondary_module_ids: newIds }));
        } else {
            setForm(f => ({ ...f, [name]: value }));
        }
    };

    const handleCreateGreenhouse = async (e) => {
        e.preventDefault();
        setError(null);
        if (!form.greenhouse_name.trim()) {
            setError('Введите имя теплицы');
            return;
        }
        if (!form.main_module_id) {
            setError('Выберите главный модуль');
            return;
        }
        setCreating(true);
        try {
            await makeRequest('POST', '/api/greenhouses/create', {
                greenhouse_name: form.greenhouse_name,
                main_module_id: form.main_module_id,
                secondary_module_ids: form.secondary_module_ids
            });
            setShowCreate(false);
            setForm({
                greenhouse_name: '',
                main_module_id: '',
                secondary_module_ids: []
            });
            fetchGreenhouses();
            fetchModules();
        } catch (error) {
            setError(error.response?.data?.error || 'Ошибка создания теплицы');
        } finally {
            setCreating(false);
        }
    };

    const getGreenhouseModules = (greenhouse) => {
        return modules.filter(m => m.greenhouse_id === greenhouse.greenhouse_id);
    };

    const favoriteGreenhouse = favoriteId ? greenhouses.find(g => String(g.greenhouse_id) === favoriteId) : null;

    if (!user) return null;

    return (
        <Layout>
            <div className="greenhouses-main-row">
                <div className="my-greenhouses-card">
                    <h2>Мои теплицы</h2>

                    <div className="favorite-greenhouse-info">
                        <h3 style={{ marginBottom: 6 }}>
                            {favoriteGreenhouse
                                ? <>Избранная теплица: <span style={{ color: AZURE }}>{favoriteGreenhouse.greenhouse_name}</span></>
                                : <>Избранная теплица не выбрана</>
                            }
                        </h3>
                        {favoriteGreenhouse && (
                            <div style={{ marginBottom: 10 }}>
                                <div>
                                    <b>Модули:</b>{" "}
                                    {getGreenhouseModules(favoriteGreenhouse).map(m =>
                                        <span key={m.module_id} style={{ marginRight: 8 }}>
                                            {m.module_name || `Модуль ${m.module_id}`}
                                        </span>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {loading ? (
                        <p>Загрузка...</p>
                    ) : greenhouses.length === 0 ? (
                        <p>У вас нет зарегистрированных теплиц</p>
                    ) : (
                        <div className="greenhouses-list">
                            {greenhouses.map(g => {
                                const ghModules = getGreenhouseModules(g);
                                const isFavorite = favoriteId && favoriteId === String(g.greenhouse_id);
                                return (
                                    <div key={g.greenhouse_id} className="greenhouse-card">
                                        <div className="greenhouse-header">
                                            <span className="greenhouse-title">{g.greenhouse_name || `Тепли��а ${g.greenhouse_id}`}</span>
                                            <button
                                                className="delete-greenhouse-btn"
                                                onClick={() => handleDeleteGreenhouse(g.greenhouse_id)}
                                                style={{ marginLeft: 12 }}
                                            >
                                                Удалить
                                            </button>
                                            <button
                                                className="favorite-greenhouse-btn"
                                                style={{
                                                    marginLeft: 10,
                                                    background: isFavorite ? AZURE : "#e0e0e0",
                                                    color: isFavorite ? "#fff" : "#333",
                                                    border: "none",
                                                    borderRadius: 6,
                                                    padding: "6px 12px",
                                                    cursor: "pointer"
                                                }}
                                                onClick={() => handleSetFavorite(g.greenhouse_id)}
                                                disabled={isFavorite}
                                                title={isFavorite ? "Это избранная теплица" : "Сделать избранной"}
                                            >
                                                {isFavorite ? "Избранная" : "Сделать избранной"}
                                            </button>
                                        </div>
                                        <div className="greenhouse-modules-row">
                                            {ghModules.length === 0 ? (
                                                <span className="no-modules-text">Нет модулей</span>
                                            ) : (
                                                ghModules.map(m => {
                                                    const isMain = String(m.module_id) === String(g.main_module_id);
                                                    return (
                                                        <div key={m.module_id} className="greenhouse-module-item">
                                                            <StarIcon
                                                                filled={isMain}
                                                                onClick={
                                                                    isMain
                                                                        ? undefined
                                                                        : () => handleSetMainModule(g.greenhouse_id, m.module_id)
                                                                }
                                                                title={isMain ? "Главный модуль" : "Сделать главным"}
                                                            />
                                                            <div className="module-name">
                                                                {m.module_name || `Модуль ${m.module_id}`}
                                                            </div>
                                                        </div>
                                                    );
                                                })
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
                <div className="greenhouse-create-side-panel">
                    <div className="greenhouse-create-side-text">
                        У вас нет теплицы или хотите добавить новую? <br />Создайте ее!
                    </div>
                    <button
                        className="create-greenhouse-btn"
                        onClick={() => setShowCreate(v => !v)}
                        style={{ marginBottom: 18 }}
                    >
                        {showCreate ? 'Отмена' : 'Создать теплицу'}
                    </button>
                    {showCreate && (
                        <form className="greenhouse-create-form" onSubmit={handleCreateGreenhouse}>
                            <div className="form-group">
                                <label>Имя теплицы <span style={{ color: 'red' }}>*</span></label>
                                <input
                                    type="text"
                                    name="greenhouse_name"
                                    value={form.greenhouse_name}
                                    onChange={handleFormChange}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Главный модуль <span style={{ color: 'red' }}>*</span></label>
                                <select
                                    name="main_module_id"
                                    value={form.main_module_id}
                                    onChange={handleFormChange}
                                    required
                                >
                                    <option value="">Выберите модуль</option>
                                    {modules.filter(m => !m.greenhouse_id).map(m => (
                                        <option key={m.module_id} value={m.module_id}>
                                            {m.module_name || `Модуль ${m.module_id}`}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Неосновные модули (до 3-х, по желанию)</label>
                                <div className="secondary-modules-list">
                                    {modules
                                        .filter(m => !m.greenhouse_id && m.module_id !== form.main_module_id)
                                        .map(m => (
                                            <label key={m.module_id} style={{ display: 'block', marginBottom: 4 }}>
                                                <input
                                                    type="checkbox"
                                                    name="secondary_module_ids"
                                                    value={m.module_id}
                                                    checked={form.secondary_module_ids.includes(String(m.module_id))}
                                                    onChange={handleFormChange}
                                                    disabled={form.secondary_module_ids.length >= 3 && !form.secondary_module_ids.includes(String(m.module_id))}
                                                />
                                                {m.module_name || `Модуль ${m.module_id}`}
                                            </label>
                                        ))}
                                </div>
                            </div>
                            {error && <div className="alert alert-error">{error}</div>}
                            <button type="submit" className="save-button" disabled={creating}>
                                {creating ? 'Создание...' : 'Создать'}
                            </button>
                        </form>
                    )}
                </div>
            </div>
        </Layout>
    );
};

export default MyGreenhouses;
