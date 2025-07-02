import React from 'react';
import { Outlet, useNavigate, Navigate } from 'react-router-dom';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Button,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Home as HomeIcon,
  People as PeopleIcon,
  QuestionAnswer as QuestionAnswerIcon,
  Person as PersonIcon,
  ExitToApp as ExitToAppIcon,
  Login as LoginIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const drawerWidth = 240;

function MainLayout() {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const menuItems = [
    { text: 'Home', icon: <HomeIcon />, path: '/' },
    { text: 'Candidates', icon: <PeopleIcon />, path: '/candidates' },
    { text: 'Questions', icon: <QuestionAnswerIcon />, path: '/questions' },
    ...(user?.type === 'candidate' ? [{ text: 'Profile', icon: <PersonIcon />, path: '/profile' }] : []),
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleLogin = () => {
    navigate('/login');
  };

  // If not authenticated, redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const drawer = (
    <div>
      <Toolbar />
      <List>
        {menuItems.map((item) => (
          <ListItem
            button
            key={item.text}
            onClick={() => {
              navigate(item.path);
              setMobileOpen(false);
            }}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
        <ListItem button onClick={handleLogout}>
          <ListItemIcon>
            <ExitToAppIcon />
          </ListItemIcon>
          <ListItemText primary="Logout" />
        </ListItem>
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          minHeight: 72,
          boxShadow: '0 4px 24px 0 rgba(0,0,0,0.18)',
          background: 'linear-gradient(90deg, #222 60%, #333 100%)',
        }}
      >
        <Toolbar sx={{ minHeight: 72 }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
            <img 
              src="/images/valverdeflag.png" 
              alt="Val Verde Flag" 
              style={{ 
                height: '52px', 
                marginRight: '24px',
                objectFit: 'contain',
                borderRadius: '6px',
                boxShadow: '0 2px 8px 0 rgba(0,0,0,0.18)'
              }} 
            />
            <Typography variant="h6" noWrap component="div" fontWeight="bold" sx={{ letterSpacing: 1 }}>
              Val Verde Candidate Registry
            </Typography>
          </Box>
          {!isAuthenticated && (
            <Button
              color="inherit"
              startIcon={<LoginIcon />}
              onClick={handleLogin}
            >
              Login
            </Button>
          )}
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}

export default MainLayout; 