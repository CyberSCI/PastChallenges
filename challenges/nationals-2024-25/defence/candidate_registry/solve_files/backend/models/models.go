package models

import (
	"database/sql"
	"time"
)

type Candidate struct {
	ID             int            `json:"id"`
	Name           string         `json:"name"`
	Email          string         `json:"email"`
	Biography      sql.NullString `json:"biography"`
	Platform       sql.NullString `json:"platform"`
	PictureURL     sql.NullString `json:"picture_url"`
	TotalDonations float64        `json:"total_donations"`
	CreatedAt      time.Time      `json:"created_at"`
}

type Voter struct {
	ID        int       `json:"id"`
	Name      string    `json:"name"`
	Email     string    `json:"email"`
	CreatedAt time.Time `json:"created_at"`
}

type Donation struct {
	ID            int       `json:"id"`
	VoterID       int       `json:"voter_id"`
	CandidateID   int       `json:"candidate_id"`
	Amount        float64   `json:"amount"`
	CreatedAt     time.Time `json:"created_at"`
	CandidateName string    `json:"candidate_name,omitempty"`
}

type Question struct {
	ID            int       `json:"id"`
	VoterID       int       `json:"voter_id"`
	CandidateID   int       `json:"candidate_id"`
	QuestionText  string    `json:"question_text"`
	CreatedAt     time.Time `json:"created_at"`
	CandidateName string    `json:"candidate_name,omitempty"`
	VoterName     string    `json:"voter_name,omitempty"`
	Answer        *Answer   `json:"answer,omitempty"`
}

type Answer struct {
	ID           int       `json:"id"`
	QuestionID   int       `json:"question_id"`
	AnswerText   string    `json:"answer_text"`
	CreatedAt    time.Time `json:"created_at"`
	AnswererName string    `json:"answerer_name,omitempty"`
}

type RegistrationRequest struct {
	Name     string `json:"name" binding:"required"`
	Email    string `json:"email" binding:"required"`
	Password string `json:"password" binding:"required,min=8"`
}

type LoginRequest struct {
	Email    string `json:"email" binding:"required"`
	Password string `json:"password" binding:"required"`
}
