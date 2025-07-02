import React, { useState, useEffect } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  TextField,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
} from '@mui/material';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

function Questions() {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState('');
  const [newQuestion, setNewQuestion] = useState('');
  const [answerTexts, setAnswerTexts] = useState({}); // Track answers per question
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      if (authLoading) {
        return; // Wait for auth to finish loading
      }

      if (!isAuthenticated) {
        setError('Please log in to view questions');
        setLoading(false);
        navigate('/login');
        return;
      }

      try {
        const token = localStorage.getItem('token');
        const [questionsRes, candidatesRes] = await Promise.all([
          axios.get('/api/questions', {
            headers: { Authorization: token }
          }),
          axios.get('/api/candidates', {
            headers: { Authorization: token }
          }),
        ]);
        setQuestions(questionsRes.data || []);
        setCandidates(candidatesRes.data || []);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching data:', err);
        if (err.response?.status === 401) {
          setError('Please log in to view questions');
          navigate('/login');
        } else {
          setError('Failed to fetch data');
        }
        setLoading(false);
      }
    };

    fetchData();
  }, [isAuthenticated, authLoading, navigate]);

  const handleSubmitQuestion = async () => {
    if (!newQuestion.trim() || !isAuthenticated) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.post('/api/questions', {
        question_text: newQuestion,
      }, {
        headers: { Authorization: token }
      });
      // Refresh questions
      const response = await axios.get('/api/questions', {
        headers: { Authorization: token }
      });
      setQuestions(response.data || []);
      setNewQuestion('');
    } catch (err) {
      console.error('Error submitting question:', err);
      if (err.response?.status === 401) {
        setError('Please log in to submit questions');
        navigate('/login');
      } else {
        setError('Failed to submit question');
      }
    }
  };

  const handleAnswerChange = (questionId, text) => {
    setAnswerTexts(prev => ({
      ...prev,
      [questionId]: text
    }));
  };

  const handleSubmitAnswer = async (questionId) => {
    const answerText = answerTexts[questionId];
    if (!answerText?.trim() || !isAuthenticated) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.post('/api/answers', {
        question_id: questionId,
        answer_text: answerText,
      }, {
        headers: { Authorization: token }
      });

      // Refresh questions to show the new answer
      const questionsResponse = await axios.get('/api/questions', {
        headers: { Authorization: token }
      });
      setQuestions(questionsResponse.data || []);
      
      // Clear the answer text for this question
      setAnswerTexts(prev => {
        const newAnswers = { ...prev };
        delete newAnswers[questionId];
        return newAnswers;
      });
    } catch (err) {
      console.error('Error submitting answer:', err);
      if (err.response?.status === 401) {
        setError('Please log in to submit answers');
        navigate('/login');
      } else {
        setError('Failed to submit answer');
      }
    }
  };

  const filteredQuestions = selectedCandidate
    ? (questions || []).filter(q => q.candidateId === selectedCandidate)
    : (questions || []);

  if (authLoading || loading) {
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
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h4" gutterBottom>
            Questions & Answers
          </Typography>

          {/* Question Form - Only for voters */}
          {user?.type === 'voter' && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Ask a Question
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Your question"
                value={newQuestion}
                onChange={(e) => setNewQuestion(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Button
                variant="contained"
                onClick={handleSubmitQuestion}
                disabled={!newQuestion.trim()}
              >
                Submit Question
              </Button>
            </Box>
          )}

          {/* Filter */}
          <Box sx={{ mb: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Filter by Candidate</InputLabel>
              <Select
                value={selectedCandidate}
                onChange={(e) => setSelectedCandidate(e.target.value)}
                label="Filter by Candidate"
              >
                <MenuItem value="">All Candidates</MenuItem>
                {(candidates || []).map((candidate) => (
                  <MenuItem key={candidate.id} value={candidate.id}>
                    {candidate.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {/* Questions List */}
          <List>
            {filteredQuestions.map((question) => (
              <React.Fragment key={question.id}>
                <Paper elevation={1} sx={{ mb: 2, p: 2 }}>
                  <Typography variant="subtitle1" color="primary">
                    Question from: {question.voter_name}
                  </Typography>
                  <Typography variant="body1" sx={{ mt: 1 }}>
                    Q: <span dangerouslySetInnerHTML={{ __html: question.question_text }} />
                  </Typography>
                  {question.answer ? (
                    <Box sx={{ mt: 2, pl: 2, borderLeft: '2px solid', borderColor: 'primary.main' }}>
                      <Typography variant="body2" color="text.secondary">
                        Answered by: {question.answer.answerer_name}
                      </Typography>
                      <Typography variant="body1" color="primary">
                        A: <span dangerouslySetInnerHTML={{ __html: question.answer.answer_text }} />
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Answered on: {new Date(question.answer.answer_created_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                  ) : user?.type === 'candidate' ? (
                    <Box sx={{ mt: 2 }}>
                      <TextField
                        fullWidth
                        multiline
                        rows={2}
                        label="Your answer"
                        value={answerTexts[question.id] || ''}
                        onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                        sx={{ mb: 1 }}
                      />
                      <Button
                        variant="contained"
                        onClick={() => handleSubmitAnswer(question.id)}
                        disabled={!answerTexts[question.id]?.trim()}
                      >
                        Submit Answer
                      </Button>
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      No answer yet
                    </Typography>
                  )}
                </Paper>
              </React.Fragment>
            ))}
          </List>
        </CardContent>
      </Card>
    </Container>
  );
}

export default Questions; 