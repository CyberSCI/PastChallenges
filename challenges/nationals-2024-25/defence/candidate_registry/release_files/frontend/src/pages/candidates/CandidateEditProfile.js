import React, { useState, useEffect } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  Button,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';

function CandidateEditProfile() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    biography: '',
    platform: '',
    picture_url: '',
  });

  useEffect(() => {
    const fetchCandidateData = async () => {
      try {
        const response = await axios.get(`/api/candidates/${user.id}`);
        setFormData({
          name: response.data.name,
          email: response.data.email,
          biography: response.data.biography || '',
          platform: response.data.platform || '',
          picture_url: response.data.picture_url || '',
        });
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch candidate data');
        setLoading(false);
      }
    };

    if (user && user.type === 'candidate') {
      fetchCandidateData();
    } else {
      navigate('/');
    }
  }, [user, navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`/api/candidates/${user.id}`, formData);
      navigate(`/candidates/${user.id}`);
    } catch (err) {
      setError('Failed to update profile');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Card>
        <CardContent>
          <Typography variant="h4" gutterBottom>
            Edit Profile
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              margin="normal"
              required
            />

            <TextField
              fullWidth
              label="Email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              margin="normal"
              required
            />

            <TextField
              fullWidth
              label="Biography"
              name="biography"
              multiline
              rows={4}
              value={formData.biography}
              onChange={handleChange}
              margin="normal"
            />

            <TextField
              fullWidth
              label="Platform"
              name="platform"
              multiline
              rows={4}
              value={formData.platform}
              onChange={handleChange}
              margin="normal"
            />

            <TextField
              fullWidth
              label="Profile Picture URL"
              name="picture_url"
              value={formData.picture_url}
              onChange={handleChange}
              margin="normal"
            />

            <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                color="primary"
                type="submit"
                fullWidth
              >
                Save Changes
              </Button>
              <Button
                variant="outlined"
                color="primary"
                onClick={() => navigate(`/candidates/${user.id}`)}
                fullWidth
              >
                Cancel
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
}

export default CandidateEditProfile; 