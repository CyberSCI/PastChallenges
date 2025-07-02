import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Button,
  TextField,
  Divider,
} from '@mui/material';
import { Edit as EditIcon } from '@mui/icons-material';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import DonationForm from '../../components/DonationForm';

function CandidateProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [questionText, setQuestionText] = useState('');
  const [questions, setQuestions] = useState([]);

  useEffect(() => {
    const fetchCandidateData = async () => {
      if (!id) {
        setError('Invalid candidate ID');
        setLoading(false);
        return;
      }

      try {
        const token = localStorage.getItem('token');
        const [candidateRes, questionsRes] = await Promise.all([
          axios.get(`/api/candidates/${id}`, {
            headers: { Authorization: token }
          }),
          axios.get(`/api/candidates/${id}/questions`, {
            headers: { Authorization: token }
          }),
        ]);
        setCandidate(candidateRes.data);
        setQuestions(questionsRes.data || []);
        setError(null);
      } catch (err) {
        setError('Failed to fetch candidate data');
        console.error('Error fetching candidate data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCandidateData();
  }, [id]);

  const handleDonationSuccess = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/candidates/${id}`, {
        headers: { Authorization: token }
      });
      setCandidate(response.data);
    } catch (err) {
      setError('Failed to update donation total');
      console.error('Error updating donation total:', err);
    }
  };

  const handleQuestionSubmit = async () => {
    if (!id) {
      setError('Invalid candidate ID');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(`/api/candidates/${id}/questions`, {
        text: questionText,
      }, {
        headers: { Authorization: token }
      });
      // Refresh questions
      const response = await axios.get(`/api/candidates/${id}/questions`, {
        headers: { Authorization: token }
      });
      setQuestions(response.data || []);
      setQuestionText('');
    } catch (err) {
      setError('Failed to submit question');
      console.error('Error submitting question:', err);
    }
  };

  if (!id) {
    return (
      <Container>
        <Alert severity="error" sx={{ mt: 2 }}>
          No candidate ID provided. Please select a candidate from the list.
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

  if (!candidate) {
    return (
      <Container>
        <Alert severity="error" sx={{ mt: 2 }}>
          Candidate not found.
        </Alert>
      </Container>
    );
  }

  return (
    <Container sx={{ py: 4 }}>
      <Grid container spacing={4}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardMedia
              component="img"
              height="400"
              image={candidate.picture_url || '/default-candidate.jpg'}
              alt={candidate.name}
              sx={{ objectFit: 'cover' }}
            />
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h4" gutterBottom>
                  {candidate.name}
                </Typography>
                {user?.type === 'candidate' && user?.id === parseInt(id) && (
                  <Button
                    variant="outlined"
                    startIcon={<EditIcon />}
                    onClick={() => navigate(`/candidates/${id}/edit`)}
                  >
                    Edit Profile
                  </Button>
                )}
              </Box>
              <Typography variant="h6" color="primary" gutterBottom>
                Total Donations: ${candidate.total_donations || 0}
              </Typography>
              {user?.type === 'voter' && (
                <DonationForm
                  candidateId={id}
                  onDonationSuccess={handleDonationSuccess}
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Biography
              </Typography>
              <Typography paragraph>
                {candidate.biography || 'No biography available.'}
              </Typography>

              <Typography variant="h5" gutterBottom>
                Platform
              </Typography>
              <Typography paragraph>
                {candidate.platform || 'No platform information available.'}
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Questions & Answers
              </Typography>
              {user?.type === 'voter' && (
                <Box sx={{ mb: 3 }}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Ask a question"
                    value={questionText}
                    onChange={(e) => setQuestionText(e.target.value)}
                    sx={{ mb: 2 }}
                  />
                  <Button
                    variant="contained"
                    onClick={handleQuestionSubmit}
                    disabled={!questionText.trim()}
                  >
                    Submit Question
                  </Button>
                </Box>
              )}
              <Divider sx={{ my: 2 }} />
              {questions.length === 0 ? (
                <Typography color="text.secondary">
                  No questions have been asked yet.
                </Typography>
              ) : (
                questions.map((q) => (
                  <Box key={q.id} sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" color="primary">
                      Q: {q.question_text}
                    </Typography>
                    {q.answer && (
                      <Typography variant="body1" sx={{ ml: 2, mt: 1 }}>
                        A: {q.answer.answer_text}
                      </Typography>
                    )}
                    <Divider sx={{ my: 2 }} />
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

export default CandidateProfile; 