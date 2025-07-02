import React from 'react';
import { Box, Typography, Paper, Grid, Button, Divider } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function Home() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const paperStyle = {
    p: 4,
    borderRadius: 3,
    boxShadow: 6,
    height: '100%',
    background: 'linear-gradient(135deg, #222 60%, #333 100%)',
    color: 'inherit',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
  };

  const buttonStyle = {
    mt: 3,
    py: 1.5,
    px: 4,
    fontWeight: 'bold',
    fontSize: '1.1rem',
    borderRadius: 2,
    boxShadow: 3,
  };

  const renderVoterContent = () => (
    <Paper sx={paperStyle}>
      <Typography variant="h5" gutterBottom fontWeight="bold">
        Welcome, {user?.name || 'Voter'}!
      </Typography>
      <Typography paragraph>
        As a registered voter, you have access to:
      </Typography>
      <ul style={{ marginLeft: 20, marginBottom: 0 }}>
        <li>View all candidates and their detailed profiles</li>
        <li>Ask questions directly to candidates about their platforms</li>
        <li>View questions and answers from other voters</li>
        <li>Stay informed about the election process</li>
      </ul>
      <Button
        variant="contained"
        color="primary"
        onClick={() => navigate('/candidates')}
        sx={buttonStyle}
      >
        View Candidates
      </Button>
    </Paper>
  );

  const renderCandidateContent = () => (
    <Paper sx={paperStyle}>
      <Typography variant="h5" gutterBottom fontWeight="bold">
        Welcome, {user?.name || 'Candidate'}!
      </Typography>
      <Typography paragraph>
        As a candidate, you can:
      </Typography>
      <ul style={{ marginLeft: 20, marginBottom: 0 }}>
        <li>Upload your professional photo to make a great first impression</li>
        <li>Share your biography to tell voters about your background and experience</li>
        <li>Present your platform to outline your vision and policies</li>
        <li>Answer questions directly from voters to engage with the community</li>
      </ul>
      <Button
        variant="contained"
        color="primary"
        onClick={() => navigate('/profile')}
        sx={buttonStyle}
      >
        Manage Your Profile
      </Button>
    </Paper>
  );

  const renderPublicContent = () => (
    <Grid container spacing={4} sx={{ mt: 1 }}>
      <Grid item xs={12} md={6}>
        <Paper sx={paperStyle}>
          <Typography variant="h5" gutterBottom fontWeight="bold">
            For Voters
          </Typography>
          <Typography paragraph>
            As a voter, you can:
          </Typography>
          <ul style={{ marginLeft: 20, marginBottom: 0 }}>
            <li>View all candidates and their information</li>
            <li>Donate to your preferred candidates</li>
            <li>Ask questions to candidates</li>
            <li>View questions and answers from other voters</li>
          </ul>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/register')}
            sx={buttonStyle}
          >
            Register as Voter
          </Button>
        </Paper>
      </Grid>

      <Grid item xs={12} md={6}>
        <Paper sx={paperStyle}>
          <Typography variant="h5" gutterBottom fontWeight="bold">
            For Candidates
          </Typography>
          <Typography paragraph>
            As a candidate, you can:
          </Typography>
          <ul style={{ marginLeft: 20, marginBottom: 0 }}>
            <li>Create and manage your profile</li>
            <li>Upload your biography and platform</li>
            <li>Receive donations from supporters</li>
            <li>Answer questions from voters</li>
          </ul>
          <Button
            variant="contained"
            color="secondary"
            onClick={() => navigate('/register')}
            sx={buttonStyle}
          >
            Register as Candidate
          </Button>
        </Paper>
      </Grid>
    </Grid>
  );

  return (
    <Box sx={{ flexGrow: 1, mt: 4, mb: 4, px: { xs: 1, sm: 4, md: 8 } }}>
      <Typography
        variant="h3"
        component="h1"
        align="center"
        fontWeight="bold"
        gutterBottom
        sx={{ letterSpacing: 1 }}
      >
        Welcome to Val Verde Candidate Registry
      </Typography>
      <Divider sx={{ mb: 5, bgcolor: 'secondary.main', height: 4, borderRadius: 2, mx: 'auto', width: 80 }} />
      {user ? (
        user.type === 'voter' ? renderVoterContent() : renderCandidateContent()
      ) : (
        renderPublicContent()
      )}
    </Box>
  );
}

export default Home; 