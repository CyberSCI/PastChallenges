import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Button,
  TextField,
  Divider,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

function VoterProfile() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [donations, setDonations] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
  });

  useEffect(() => {
    if (!user || !user.id) {
      setError('Please log in to view your profile');
      setLoading(false);
      return;
    }

    const fetchProfileData = async () => {
      try {
        const [profileRes, donationsRes, questionsRes] = await Promise.all([
          axios.get(`/api/voters/${user.id}`),
          axios.get(`/api/voters/${user.id}/donations`),
          axios.get(`/api/voters/${user.id}/questions`),
        ]);
        setProfile(profileRes.data);
        setDonations(donationsRes.data);
        setQuestions(questionsRes.data);
        setFormData({
          name: profileRes.data.name,
          email: profileRes.data.email,
        });
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch profile data');
        setLoading(false);
      }
    };

    fetchProfileData();
  }, [user]);

  const handleUpdateProfile = async () => {
    if (!user || !user.id) {
      setError('Please log in to update your profile');
      return;
    }

    try {
      await axios.put(`/api/voters/${user.id}`, formData);
      setProfile({ ...profile, ...formData });
      setEditMode(false);
    } catch (err) {
      setError('Failed to update profile');
    }
  };

  if (!user || !user.id) {
    return (
      <Container>
        <Alert severity="error" sx={{ mt: 2 }}>
          Please log in to view your profile
        </Alert>
      </Container>
    );
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container sx={{ py: 4 }}>
      <Grid container spacing={4}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h4" gutterBottom>
                Profile
              </Typography>
              {editMode ? (
                <Box>
                  <TextField
                    fullWidth
                    label="Name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    sx={{ mb: 2 }}
                  />
                  <TextField
                    fullWidth
                    label="Email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    sx={{ mb: 2 }}
                  />
                  <Button
                    variant="contained"
                    onClick={handleUpdateProfile}
                    sx={{ mr: 2 }}
                  >
                    Save
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => setEditMode(false)}
                  >
                    Cancel
                  </Button>
                </Box>
              ) : (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    {profile.name}
                  </Typography>
                  <Typography color="text.secondary" gutterBottom>
                    {profile.email}
                  </Typography>
                  <Button
                    variant="outlined"
                    onClick={() => setEditMode(true)}
                    sx={{ mt: 2 }}
                  >
                    Edit Profile
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={8}>
          <Card sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                My Donations
              </Typography>
              <List>
                {donations.map((donation) => (
                  <ListItem key={donation.id}>
                    <ListItemText
                      primary={`$${donation.amount} to ${donation.candidateName}`}
                      secondary={new Date(donation.date).toLocaleDateString()}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                My Questions
              </Typography>
              <List>
                {questions.map((question) => (
                  <React.Fragment key={question.id}>
                    <ListItem>
                      <ListItemText
                        primary={`To: ${question.candidateName}`}
                        secondary={
                          <Box>
                            <Typography variant="body2">
                              Q: {question.text}
                            </Typography>
                            {question.answer && (
                              <Typography variant="body2" color="text.secondary">
                                A: {question.answer}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

export default VoterProfile; 