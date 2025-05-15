import './App.css';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '../src/Assets/AuthContext';
import ProtectedRoute from '../src/ProtectedRoute';
import Dashboard from '../src/Pages/Dashboard';
import LoginSignup from '../src/Assets/LoginSignup';
import AvailableModules from '../src/Pages/AvailableModules';
import MyModules from '../src/Pages/MyModules';

function PrivateRoute({ children }) {
    const { user } = useAuth();
    return user ? children : <Navigate to="/login" />;
}

function App() {
  return (
      <AuthProvider>
          <Router>
              <Routes>
                  <Route path="/login" element={<LoginSignup />} />
                  <Route element={<ProtectedRoute />}>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/available-modules" element={<AvailableModules />} />
                      <Route path="/my-modules" element={<MyModules />} />
                  </Route>
              </Routes>
          </Router>
      </AuthProvider>
  );
}

export default App;