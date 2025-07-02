import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Grid,
} from '@mui/material';
import { useFormik } from 'formik';
import * as yup from 'yup';
import { useAuth } from '../../contexts/AuthContext';

const validationSchema = yup.object({
  name: yup
    .string()
    .required('Name is required')
    .min(2, 'Name should be of minimum 2 characters length'),
  email: yup
    .string()
    .email('Enter a valid email')
    .required('Email is required'),
  password: yup
    .string()
    .min(8, 'Password should be of minimum 8 characters length')
    .required('Password is required'),
  confirmPassword: yup
    .string()
    .oneOf([yup.ref('password'), null], 'Passwords must match')
    .required('Confirm password is required'),
  userType: yup
    .string()
    .oneOf(['voter', 'candidate'], 'Invalid user type')
    .required('User type is required'),
});

function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [error, setError] = useState('');

  const formik = useFormik({
    initialValues: {
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
      userType: 'voter',
    },
    validationSchema: validationSchema,
    onSubmit: async (values) => {
      try {
        const { confirmPassword, ...registrationData } = values;
        await register(registrationData, values.userType);
        navigate('/login');
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
        id="name"
        label="Full Name"
        name="name"
        autoComplete="name"
        autoFocus
        value={formik.values.name}
        onChange={formik.handleChange}
        error={formik.touched.name && Boolean(formik.errors.name)}
        helperText={formik.touched.name && formik.errors.name}
      />

      <TextField
        margin="normal"
        required
        fullWidth
        id="email"
        label="Email Address"
        name="email"
        autoComplete="email"
        value={formik.values.email}
        onChange={formik.handleChange}
        error={formik.touched.email && Boolean(formik.errors.email)}
        helperText={formik.touched.email && formik.errors.email}
      />

      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField
            required
            fullWidth
            name="password"
            label="Password"
            type="password"
            id="password"
            autoComplete="new-password"
            value={formik.values.password}
            onChange={formik.handleChange}
            error={formik.touched.password && Boolean(formik.errors.password)}
            helperText={formik.touched.password && formik.errors.password}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            required
            fullWidth
            name="confirmPassword"
            label="Confirm Password"
            type="password"
            id="confirmPassword"
            value={formik.values.confirmPassword}
            onChange={formik.handleChange}
            error={formik.touched.confirmPassword && Boolean(formik.errors.confirmPassword)}
            helperText={formik.touched.confirmPassword && formik.errors.confirmPassword}
          />
        </Grid>
      </Grid>

      <Button
        type="submit"
        fullWidth
        variant="contained"
        sx={{ mt: 3, mb: 2 }}
      >
        Register
      </Button>

      <Box sx={{ textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Already have an account?{' '}
          <Button
            color="primary"
            onClick={() => navigate('/login')}
          >
            Sign In
          </Button>
        </Typography>
      </Box>
    </Box>
  );
}

export default Register; 