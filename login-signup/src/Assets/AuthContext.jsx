import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Единая функция для всех запросов
    const makeRequest = async (method, url, data = null) => {
        try {
            const response = await axios({
                method,
                url: `http://localhost:5000${url}`,
                data,
                withCredentials: true,
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            return response.data;
        } catch (error) {
            throw error;
        }
    };

    const checkAuth = async () => {
        try {
            const data = await makeRequest('GET', '/api/user');
            setUser(data);
        } catch {
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (login, password) => {
        const data = await makeRequest('POST', '/api/auth/login', { login, password });
        setUser(data.user);
        return true;
    };

    const logout = async () => {
        await makeRequest('GET', '/api/auth/logout');
        setUser(null);
    };

    useEffect(() => {
        checkAuth();
    }, []);

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, makeRequest }}>
            {!loading && children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);