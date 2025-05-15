import { Navigate, Outlet } from 'react-router-dom'; 
import { useAuth } from '../src/Assets/AuthContext'; 

const ProtectedRoute = () => {
    const { user, loading } = useAuth();

    if (loading) return <div>Загрузка...</div>;
    return user ? <Outlet /> : <Navigate to="/login" replace />;
};

export default ProtectedRoute;