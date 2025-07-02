import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { useFormik } from 'formik';
import * as yup from 'yup';
import { useAuth } from '../../contexts/AuthContext';

const validationSchema = yup.object({
  email: yup
    .string()
    .email('Enter a valid email')
    .required('Email is required'),
  password: yup
    .string()
    .required('Password is required'),
  userType: yup
    .string()
    .oneOf(['voter', 'candidate'], 'Invalid user type')
    .required('User type is required'),
});

function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState('');

  const formik = useFormik({
    initialValues: {
      email: '',
      password: '',
      userType: 'voter',
    },
    validationSchema: validationSchema,
    onSubmit: async (values) => {
      try {
        await login(values.email, values.password, values.userType);
        navigate('/');
      } catch (err) {
        setError(err);
      }
    },
  });

  return (
    <Box component="form" onSubmit={formik.handleSubmit} sx={{ mt: 1 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel id="user-type-label">I am a</InputLabel>
        <Select
          labelId="user-type-label"
          id="userType"
          name="userType"
          value={formik.values.userType}
          onChange={formik.handleChange}
          error={formik.touched.userType && Boolean(formik.errors.userType)}
        >
          <MenuItem value="voter">Voter</MenuItem>
          <MenuItem value="candidate">Candidate</MenuItem>
        </Select>
      </FormControl>

      <TextField
        margin="normal"
        required
        fullWidth
        id="email"
        label="Email Address"
        name="email"
        autoComplete="email"
        autoFocus
        value={formik.values.email}
        onChange={formik.handleChange}
        error={formik.touched.email && Boolean(formik.errors.email)}
        helperText={formik.touched.email && formik.errors.email}
      />

      <TextField
        margin="normal"
        required
        fullWidth
        name="password"
        label="Password"
        type="password"
        id="password"
        autoComplete="current-password"
        value={formik.values.password}
        onChange={formik.handleChange}
        error={formik.touched.password && Boolean(formik.errors.password)}
        helperText={formik.touched.password && formik.errors.password}
      />

      <Button
        type="submit"
        fullWidth
        variant="contained"
        sx={{ mt: 3, mb: 2 }}
      >
        Sign In
      </Button>

      <Box sx={{ textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Don't have an account?{' '}
          <Button
            color="primary"
            onClick={() => navigate('/register')}
          >
            Sign Up
          </Button>
        </Typography>
      </Box>
    </Box>
  );
}

export default Login; 