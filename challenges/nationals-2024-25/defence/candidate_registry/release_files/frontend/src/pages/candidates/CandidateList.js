import React, { useState, useEffect } from 'react';
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
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Stack,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Search as SearchIcon, Sort as SortIcon } from '@mui/icons-material';
import axios from 'axios';

const CandidateList = () => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/candidates');
        setCandidates(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch candidates. Please try again later.');
        console.error('Error fetching candidates:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCandidates();
  }, []);

  const filteredCandidates = candidates.filter(candidate => {
    const searchLower = searchTerm.toLowerCase();
    return (
      candidate.name.toLowerCase().includes(searchLower) ||
      (candidate.biography && candidate.biography.toLowerCase().includes(searchLower)) ||
      (candidate.platform && candidate.platform.toLowerCase().includes(searchLower))
    );
  });

  const sortedCandidates = [...filteredCandidates].sort((a, b) => {
    if (sortBy === 'name') {
      return a.name.localeCompare(b.name);
    } else if (sortBy === 'donations') {
      return (b.total_donations || 0) - (a.total_donations || 0);
    }
    return 0;
  });

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Candidates
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Meet the candidates running in the election
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search candidates..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ maxWidth: 400 }}
        />

        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Sort By</InputLabel>
          <Select
            value={sortBy}
            label="Sort By"
            onChange={(e) => setSortBy(e.target.value)}
          >
            <MenuItem value="name">Name</MenuItem>
            <MenuItem value="donations">Total Donations</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {sortedCandidates.length === 0 ? (
        <Typography variant="body1" color="text.secondary" align="center">
          No candidates found matching your search.
        </Typography>
      ) : (
        <Grid container spacing={3}>
          {sortedCandidates.map((candidate) => (
            <Grid item xs={12} sm={6} md={4} key={candidate.id}>
              <Card 
                sx={{ 
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 6,
                  }
                }}
                onClick={() => navigate(`/candidates/${candidate.id}`)}
              >
                <CardMedia
                  component="img"
                  height="200"
                  image={candidate.picture_url || '/default-candidate.jpg'}
                  alt={candidate.name}
                  sx={{ objectFit: 'cover' }}
                />
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography gutterBottom variant="h5" component="h2">
                    {candidate.name}
                  </Typography>
                  {candidate.biography && (
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {candidate.biography.length > 150
                        ? `${candidate.biography.substring(0, 150)}...`
                        : candidate.biography}
                    </Typography>
                  )}
                  <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip
                      label={`$${candidate.total_donations || 0} raised`}
                      color="primary"
                      size="small"
                    />
                    {candidate.platform && (
                      <Chip
                        label="Platform Available"
                        color="secondary"
                        size="small"
                      />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Container>
  );
};

export default CandidateList; 