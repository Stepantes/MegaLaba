import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../Assets/AuthContext';
import '../Pages/Profile.css';

const navLinks = [
    { to: '/', label: 'Главная' },
    { to: '/my-greenhouses', label: 'Мои теплицы' },
    { to: '/my-modules', label: 'Мои модули' },
    { to: '/available-modules', label: 'Доступные модули' }
];

const Layout = ({ children }) => {
    const { logout } = useAuth();
    const location = useLocation();

    return (
        <div className="layout-centered-container">
            <div className="sidebar-layout">
                <nav className="dashboard-nav-vertical">
                    <div className="nav-links-group">
                        {navLinks.map(link => {
                            const isActive = location.pathname === link.to;
                            return (
                                <Link
                                    key={link.to}
                                    to={link.to}
                                    className={`nav-link-vertical${isActive ? ' active' : ''}`}
                                >
                                    {isActive && <span className="active-bar"></span>}
                                    {link.label}
                                </Link>
                            );
                        })}
                    </div>
                    <div className="logout-container">
                        <button onClick={logout} className="logout-button-vertical">Выйти</button>
                    </div>
                </nav>
                <div className="dashboard-content">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default Layout;