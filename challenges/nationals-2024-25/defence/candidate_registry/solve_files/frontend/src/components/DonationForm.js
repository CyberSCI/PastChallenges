import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Grid,
  Alert,
} from '@mui/material';
import { useFormik } from 'formik';
import * as yup from 'yup';

const validationSchema = yup.object({
  amount: yup
    .number()
    .min(1, 'Amount must be at least $1')
    .required('Amount is required'),
  cardNumber: yup
    .string()
    .matches(/^\d{16}$/, 'Card number must be 16 digits')
    .required('Card number is required'),
  cardHolder: yup
    .string()
    .required('Card holder name is required'),
  expiryMonth: yup
    .number()
    .min(1, 'Month must be between 1 and 12')
    .max(12, 'Month must be between 1 and 12')
    .required('Expiry month is required'),
  expiryYear: yup
    .number()
    .min(new Date().getFullYear(), 'Year must be current or future')
    .max(new Date().getFullYear() + 10, 'Year must be within 10 years')
    .required('Expiry year is required'),
  cvv: yup
    .string()
    .matches(/^\d{3,4}$/, 'CVV must be 3 or 4 digits')
    .required('CVV is required'),
});

function DonationForm({ candidateId, onDonationSuccess }) {
  const [error, setError] = useState('');

  const formik = useFormik({
    initialValues: {
      amount: '',
      cardNumber: '',
      cardHolder: '',
      expiryMonth: '',
      expiryYear: '',
      cvv: '',
    },
    validationSchema: validationSchema,
    onSubmit: async (values) => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/donations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token,
          },
          body: JSON.stringify({
            ...values,
            candidate_id: parseInt(candidateId)
          }),
        });

        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.error || 'Failed to process donation');
        }

        onDonationSuccess(data);
        formik.resetForm();
      } catch (err) {
        console.error('Donation error:', err);
        setError(err.message);
      }
    },
  });

  return (
    <Box component="form" onSubmit={formik.handleSubmit} sx={{ mt: 2 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TextField
        fullWidth
        label="Donation Amount ($)"
        name="amount"
        type="number"
        value={formik.values.amount}
        onChange={formik.handleChange}
        error={formik.touched.amount && Boolean(formik.errors.amount)}
        helperText={formik.touched.amount && formik.errors.amount}
        sx={{ mb: 2 }}
      />

      <Typography variant="h6" gutterBottom>
        Payment Information
      </Typography>

      <TextField
        fullWidth
        label="Card Number"
        name="cardNumber"
        value={formik.values.cardNumber}
        onChange={formik.handleChange}
        error={formik.touched.cardNumber && Boolean(formik.errors.cardNumber)}
        helperText={formik.touched.cardNumber && formik.errors.cardNumber}
        sx={{ mb: 2 }}
      />

      <TextField
        fullWidth
        label="Card Holder Name"
        name="cardHolder"
        value={formik.values.cardHolder}
        onChange={formik.handleChange}
        error={formik.touched.cardHolder && Boolean(formik.errors.cardHolder)}
        helperText={formik.touched.cardHolder && formik.errors.cardHolder}
        sx={{ mb: 2 }}
      />

      <Grid container spacing={2}>
        <Grid item xs={6}>
          <TextField
            fullWidth
            label="Expiry Month"
            name="expiryMonth"
            type="number"
            value={formik.values.expiryMonth}
            onChange={formik.handleChange}
            error={formik.touched.expiryMonth && Boolean(formik.errors.expiryMonth)}
            helperText={formik.touched.expiryMonth && formik.errors.expiryMonth}
          />
        </Grid>
        <Grid item xs={6}>
          <TextField
            fullWidth
            label="Expiry Year"
            name="expiryYear"
            type="number"
            value={formik.values.expiryYear}
            onChange={formik.handleChange}
            error={formik.touched.expiryYear && Boolean(formik.errors.expiryYear)}
            helperText={formik.touched.expiryYear && formik.errors.expiryYear}
          />
        </Grid>
      </Grid>

      <TextField
        fullWidth
        label="CVV"
        name="cvv"
        type="password"
        value={formik.values.cvv}
        onChange={formik.handleChange}
        error={formik.touched.cvv && Boolean(formik.errors.cvv)}
        helperText={formik.touched.cvv && formik.errors.cvv}
        sx={{ mt: 2, mb: 2 }}
      />

      <Button
        type="submit"
        variant="contained"
        color="primary"
        fullWidth
        disabled={formik.isSubmitting}
      >
        {formik.isSubmitting ? 'Processing...' : 'Donate'}
      </Button>
    </Box>
  );
}

export default DonationForm; 