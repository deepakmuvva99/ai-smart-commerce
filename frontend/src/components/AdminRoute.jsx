import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AdminRoute({ children }) {
    const { user, isLoading } = useAuth();

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gray-950 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    // If not logged in at all, go to login
    if (!user) {
        return <Navigate to="/login" replace />;
    }

    // If logged in but NOT an admin, kick them out to homepage
    if (user.role !== 'admin') {
        return <Navigate to="/" replace />;
    }

    // Authenticated AND is an admin: render the dashboard
    return children;
}
