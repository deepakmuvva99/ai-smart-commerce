import { createContext, useContext, useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        if (token) {
            fetchUser(token);
        } else {
            setIsLoading(false);
        }
    }, [token]);

    const fetchUser = async (authToken) => {
        try {
            const response = await fetch(`${API_URL}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
            } else {
                logout(); // Token invalid/expired
            }
        } catch (error) {
            console.error("Failed to fetch user:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const login = async (email, password) => {
        const formData = new URLSearchParams();
        formData.append('username', email); // OAuth2 expects 'username' instead of 'email'
        formData.append('password', password);

        const response = await fetch(`${API_URL}/users/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Login failed');
        }

        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);

        // Fetch user immediately to get the role
        const userResponse = await fetch(`${API_URL}/users/me`, {
            headers: { 'Authorization': `Bearer ${data.access_token}` }
        });
        if (userResponse.ok) {
            const userData = await userResponse.json();
            setUser(userData);
            return userData;
        }
        return null;
    };

    const signup = async (email, password) => {
        const response = await fetch(`${API_URL}/users/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
            const data = await response.json();
            let errorMessage = 'Registration failed';
            if (Array.isArray(data.detail)) {
                errorMessage = data.detail.map(err => err.msg).join(', ');
            } else if (data.detail) {
                errorMessage = data.detail;
            }
            throw new Error(errorMessage);
        }

        // Return the registration data (contains the verification_token for our demo)
        return await response.json();
    };

    const requestPasswordReset = async (email) => {
        const response = await fetch(`${API_URL}/users/forgot-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email }),
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to request password reset');
        }
        return await response.json();
    };

    const resetPassword = async (token, newPassword) => {
        const response = await fetch(`${API_URL}/users/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, new_password: newPassword }),
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to reset password');
        }
        return await response.json();
    };

    const verifyEmail = async (token) => {
        const response = await fetch(`${API_URL}/users/verify/${token}`);
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to verify email');
        }
        return await response.json();
    };



    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ 
            user, token, isLoading, login, signup, logout, 
            requestPasswordReset, resetPassword, verifyEmail 
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
