import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decoded = jwtDecode(token);
        console.log('Decoded token:', decoded); // Debug log
        // Create a consistent user object structure
        setUser({
          id: decoded.user_id,
          type: decoded.user_type,
          name: decoded.name || '',
          email: decoded.email || '',
        });
        // Set default Authorization header for axios
        axios.defaults.headers.common['Authorization'] = token;
      } catch (error) {
        console.error('Token decode error:', error); // Debug log
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password, userType) => {
    try {
      const response = await axios.post(`/auth/login/${userType}`, {
        email,
        password,
      });

      const { token, user: userData } = response.data;
      localStorage.setItem('token', token);
      axios.defaults.headers.common['Authorization'] = token;
      
      // Create a consistent user object structure
      const user = {
        id: userData.id,
        type: userType,
        name: userData.name,
        email: userData.email,
      };
      
      setUser(user);
      return user;
    } catch (error) {
      throw error.response?.data?.error || 'Login failed';
    }
  };

  const register = async (userData, userType) => {
    try {
      const response = await axios.post(`/auth/register/${userType}`, userData);
      return response.data;
    } catch (error) {
      throw error.response?.data?.error || 'Registration failed';
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 