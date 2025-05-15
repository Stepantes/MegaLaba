import { Link } from 'react-router-dom';
import { useAuth } from '../Assets/AuthContext';
import '../Pages/Profile.css';

const Layout = ({ children }) => {
    const { logout } = useAuth();

    return (
        <div className="dashboard">
            <div className='header'>Личный кабинет</div>
            <div className='container'>
                <nav className="dashboard-nav">
                    <Link to="/" className="nav-link">Главная</Link>
                    <Link to="/my-modules" className="nav-link">Мои модули</Link>
                    <Link to="/available-modules" className="nav-link">Доступные модули</Link>
                    <button onClick={logout} className="logout-button">Выйти</button>
                </nav>

                <div className="dashboard-content">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default Layout;