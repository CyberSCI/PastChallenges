import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Layouts
import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';

// Pages
import Home from './pages/Home';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import CandidateList from './pages/candidates/CandidateList';
import CandidateProfile from './pages/candidates/CandidateProfile';
import CandidateEditProfile from './pages/candidates/CandidateEditProfile';
import VoterProfile from './pages/voters/VoterProfile';
import Questions from './pages/questions/Questions';

// Create theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#d32f2f', // Red from the flag
    },
    secondary: {
      main: '#ffd600', // Yellow from the flag
    },
    success: {
      main: '#388e3c', // Green from the flag
    },
    background: {
      default: '#111', // Black background
      paper: '#222',   // Slightly lighter for surfaces
    },
    text: {
      primary: '#fff',
      secondary: '#ffd600', // Yellow for secondary text
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

// Profile route component that renders the appropriate profile based on user type
function ProfileRoute() {
  const { user } = useAuth();
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.type === 'candidate') {
    return <Navigate to={`/candidates/${user.id}`} replace />;
  }

  return <VoterProfile />;
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public routes */}
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
            </Route>

            {/* Protected routes */}
            <Route element={<MainLayout />}>
              <Route path="/" element={<Home />} />
              <Route path="/candidates" element={<CandidateList />} />
              <Route path="/candidates/:id" element={<CandidateProfile />} />
              <Route path="/candidates/:id/edit" element={<CandidateEditProfile />} />
              <Route path="/profile" element={<ProfileRoute />} />
              <Route path="/questions" element={<Questions />} />
            </Route>

            {/* Redirect to home for unknown routes */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App; 