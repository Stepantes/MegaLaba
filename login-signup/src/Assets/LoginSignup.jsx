import React, { useState } from 'react';
import './LoginSignup.css';
import user_icon from '../Assets/person.png';
import password_icon from '../Assets/password.png';
import axios from 'axios';
import { useAuth } from './AuthContext';
import { useNavigate } from 'react-router-dom';

const LoginSignup = () => {
    const { login } = useAuth();
    const navigate = useNavigate();
    const [action, setAction] = useState("Вход");
    const [formData, setFormData] = useState({
        login: '',
        password: ''
    });
    const [message, setMessage] = useState('');
    const [messageType, setMessageType] = useState(''); // 'success' или 'error'
    const [isLoading, setIsLoading] = useState(false);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async () => {
        if (!formData.login || !formData.password) {
            setMessageType('error');
            setMessage('Введите логин и пароль');
            return;
        }

        setIsLoading(true);
        setMessage('');
        setMessageType('');

        try {
            if (action === "Вход") {
                await login(formData.login, formData.password);
                setMessageType('success');
                setMessage('Вход выполнен успешно!');
                setTimeout(() => navigate('/'), 1000); // Задержка для отображения сообщения
            } else {
                await axios.post(
                    'http://localhost:5000/api/auth/register',
                    formData,
                    { 
                        withCredentials: true,
                        headers: { 'Content-Type': 'application/json' }
                    }
                );
                setMessageType('success');
                setMessage('Регистрация прошла успешно! Теперь войдите в систему.');
                setAction("Вход");
            }
        } catch (error) {
            console.error('Ошибка:', error);
            setMessageType('error');
            setMessage(
                error.response?.data?.error || 
                error.message || 
                'Произошла ошибка'
            );
        } finally {
            setIsLoading(false);
        }
    };

    const switchMode = () => {
        setAction(prev => prev === "Вход" ? "Регистрация" : "Вход");
        setMessage('');
        setMessageType('');
    };

    return (
        <div className="container">
            <div className="header">
                <div className='text'>{action}</div>
                <div className='underline'></div>
            </div>

            {message && (
                <div className={`message ${messageType}`}>
                    {messageType === 'success' ? (
                        <span className="message-icon">✓</span>
                    ) : (
                        <span className="message-icon">⚠</span>
                    )}
                    {message}
                </div>
            )}

            <div className='inputs'>
                <div className='input'>
                    <img src={user_icon} alt="Иконка пользователя" />
                    <input
                        type="text"
                        name="login"
                        placeholder='Логин'
                        value={formData.login}
                        onChange={handleChange}
                        disabled={isLoading}
                    />
                </div>
                <div className='input'>
                    <img src={password_icon} alt="Иконка пароля" />
                    <input
                        type="password"
                        name="password"
                        placeholder='Пароль'
                        value={formData.password}
                        onChange={handleChange}
                        disabled={isLoading}
                    />
                </div>
            </div>

            <button 
                className="submit-btn"
                onClick={handleSubmit}
                disabled={isLoading}
            >
                {isLoading ? (
                    <span className="spinner"></span>
                ) : (
                    "Готово"
                )}
            </button>

            <div className="submit-container">
                <div className='toggle-btn'>
                    <div 
                        className={`submit ${action === "Регистрация" ? 'active' : ''}`}
                        onClick={!isLoading ? switchMode : undefined}
                    >
                        {action === "Вход" ? "Регистрация" : "Вход"}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LoginSignup;