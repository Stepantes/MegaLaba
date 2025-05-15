import { useEffect, useState } from 'react';
import { useAuth } from '../Assets/AuthContext';
import { useNavigate } from 'react-router-dom';
import Layout from './Layout';
import Logo from '../Assets/Logo.svg';
import HumidityIcon from '../Assets/Humidity.svg';
import TemperatureIcon from '../Assets/Temperature.svg';
import styles from './DashboardHistoryPanel.module.css';
import LightIcon from '../Assets/Light.svg';
import TargetVsActualBlock from "./TargetVsActualBlock";
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

const SensorCard = ({ icon, label, value, unit }) => (
    <div className="sensor-card">
        <img src={icon} alt={label} className="sensor-icon" />
        <div className="sensor-value">{value !== undefined && value !== null ? value : "--"}</div>
        <div className="sensor-label">{label}</div>
        <div className="sensor-unit">{unit}</div>
    </div>
);

const chartConfigs = [
    {
        key: 'temperature',
        label: 'Температура',
        color: '#ff6b6b',
        unit: '°C',
        icon: TemperatureIcon,
    },
    {
        key: 'humidity',
        label: 'Влажность',
        color: '#59a1b8',
        unit: '%',
        icon: HumidityIcon,
    },
    {
        key: 'light',
        label: 'Освещённость',
        color: '#f7b731',
        unit: 'лк',
        icon: LightIcon,
    }
];

const HistoryChart = ({ data, label, color, unit }) => (
    <div className={styles["history-chart-block"]}>
        <div className={styles["history-chart-label"]}>{label}</div>
        <ResponsiveContainer width="100%" height={180}>
            <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                    dataKey="time"
                    tickFormatter={t => t.slice(11, 16)}
                    minTickGap={30}
                />
                <YAxis unit={unit} />
                <Tooltip labelFormatter={t => t.replace('T', ' ').slice(0, 16)} />
                <Legend />
                <Line type="monotone" dataKey="value" stroke={color} dot={false} />
            </LineChart>
        </ResponsiveContainer>
    </div>
);

const Dashboard = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [modules, setModules] = useState([]);
    const [loading, setLoading] = useState(true);

    // Избранная теплица 
    const [favoriteGreenhouse, setFavoriteGreenhouse] = useState(null);
    const [sensorData, setSensorData] = useState({
        temperature: null,
        humidity: null,
        light: null,
    });

    // Целевые значения 
    const [targetValues, setTargetValues] = useState({
        temperature: 24,
        humidity: 60,
        light: 1200,
    });

    // История за 24 часа
    const [history, setHistory] = useState({
        temperature: [],
        humidity: [],
        light: [],
    });

    // Для переключения графиков
    const [activeChartIdx, setActiveChartIdx] = useState(0);

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }
        fetchModules();
        fetchFavoriteGreenhouse();
    }, [user, navigate]);

    // Модули пользователя 
    const fetchModules = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/modules/user', {
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            setModules(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('Error fetching modules:', error);
        } finally {
            setLoading(false);
        }
    };

    //Избранную теплица с бэка
    const fetchFavoriteGreenhouse = async () => {
        try {
            const resp = await fetch('http://localhost:5000/api/user/favorite-greenhouse', {
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!resp.ok) {
                setFavoriteGreenhouse(null);
                setSensorData({ temperature: null, humidity: null, light: null });
                setHistory({ temperature: [], humidity: [], light: [] });
                return;
            }
            const greenhouse = await resp.json();
            if (!greenhouse) {
                setFavoriteGreenhouse(null);
                setSensorData({ temperature: null, humidity: null, light: null });
                setHistory({ temperature: [], humidity: [], light: [] });
                return;
            }
            setFavoriteGreenhouse(greenhouse);
            let mainModuleId = greenhouse.main_module_id;
            let moduleToShow = null;
            if (greenhouse.modules && greenhouse.modules.length > 0) {
                moduleToShow = greenhouse.modules.find(m => String(m.module_id) === String(mainModuleId)) || greenhouse.modules[0];
            }
            if (moduleToShow) {
                setSensorData({
                    temperature: moduleToShow.last_temperature,
                    humidity: moduleToShow.last_humidity,
                    light: moduleToShow.last_light,
                });
                fetchHistory(moduleToShow.module_id);

                // Здесь можно получить целевые значения из модуля/теплицы, если они есть
                if (moduleToShow.target_temperature || moduleToShow.target_humidity || moduleToShow.target_light) {
                    setTargetValues({
                        temperature: moduleToShow.target_temperature ?? 24,
                        humidity: moduleToShow.target_humidity ?? 60,
                        light: moduleToShow.target_lighting ?? 1200,
                    });
                }
            } else {
                setSensorData({ temperature: null, humidity: null, light: null });
                setHistory({ temperature: [], humidity: [], light: [] });
            }
        } catch (error) {
            setFavoriteGreenhouse(null);
            setSensorData({ temperature: null, humidity: null, light: null });
            setHistory({ temperature: [], humidity: [], light: [] });
        }
    };

    // Получить историю показателей за 24 часа для модуля
    const fetchHistory = async (moduleId) => {
        try {
            const resp = await fetch(`http://localhost:5000/api/modules/${moduleId}/history-24h`, {
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!resp.ok) {
                setHistory({ temperature: [], humidity: [], light: [] });
                return;
            }
            const data = await resp.json();
            setHistory({
                temperature: data.temperature || [],
                humidity: data.humidity || [],
                light: data.light || [],
            });
        } catch (error) {
            setHistory({ temperature: [], humidity: [], light: [] });
        }
    };

    if (!user) return null;

    // Обработчики для стрелок
    const handlePrevChart = () => {
        setActiveChartIdx((prev) => (prev - 1 + chartConfigs.length) % chartConfigs.length);
    };
    const handleNextChart = () => {
        setActiveChartIdx((prev) => (prev + 1) % chartConfigs.length);
    };

    const activeChart = chartConfigs[activeChartIdx];

    return (
        <Layout>
            <div className="dashboard-main-row">
                {/* Левая панель */}
                <div>
                <div className="dashboard-greenhouse-panel">
                        <div className="dashboard-greenhouse-title">
                            {favoriteGreenhouse
                                ? <>В теплице <b>{favoriteGreenhouse.greenhouse_name}</b> сейчас</>
                                : <>Избранная теплица не выбрана</>
                            }
                        </div>
                        <div className="dashboard-sensors-row">
                            <SensorCard
                                icon={HumidityIcon}
                                label="Влажность"
                                value={sensorData.humidity}
                                unit="%"
                            />
                            <SensorCard
                                icon={TemperatureIcon}
                                label="Температура"
                                value={sensorData.temperature}
                                unit="°C"
                            />
                            <SensorCard
                                icon={LightIcon}
                                label="Освещённость"
                                value={sensorData.light}
                                unit="лк"
                            />
                        </div>
                    </div>
                    <TargetVsActualBlock targets={targetValues} actuals={sensorData} />
                </div>
                {/* Правая панель*/}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                    <div className="logotip">
                            <img src={Logo} alt="Логотип" />
                        </div>
                        <div className="my-modules-card">
                            <h3>Мои модули</h3>
                            <div className="my-modules-list-scrollable">
                                <ul>
                                    {modules.map(module => (
                                        <li key={module.module_id}>
                                            {module.module_name || `Модуль ${module.module_id}`}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                    </div>
                    {/* Целевые и фактические показатели */}
                    <div className={styles['dashboard-history-panel-fact']}>
                        <div className={styles['dashboard-history-title']}>
                            История за 24 часа
                        </div>
                        <div className={styles['dashboard-history-charts']}>
                            <button
                                className={styles['history-arrow-btn']}
                                onClick={handlePrevChart}
                                style={{ left: 0 }}
                                aria-label="Предыдущий график"
                            >
                                &#8592;
                            </button>
                            <div style={{ flex: 1 }}>
                                <HistoryChart
                                    data={history[activeChart.key]}
                                    label={activeChart.label}
                                    color={activeChart.color}
                                    unit={activeChart.unit}
                                />
                            </div>
                            <button
                                className={styles['history-arrow-btn']}
                                onClick={handleNextChart}
                                style={{ right: 0 }}
                                aria-label="Следующий график"
                            >
                                &#8594;
                            </button>
                        </div>
                        <div className={styles['dashboard-history-indicators']}>
                            {chartConfigs.map((cfg, idx) => (
                                <span
                                    key={cfg.key}
                                    className={idx === activeChartIdx ? styles.active : ''}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default Dashboard;