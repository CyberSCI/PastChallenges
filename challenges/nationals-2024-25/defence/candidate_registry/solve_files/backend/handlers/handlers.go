package handlers

import (
	"database/sql"
	"log"
	"net/http"
	"strconv"
	"time"

	"voter-registry/backend/auth"
	"voter-registry/backend/models"

	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
)

var db *sql.DB

func InitHandlers(database *sql.DB) {
	db = database
}

// Auth middleware
func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		tokenString := c.GetHeader("Authorization")
		if tokenString == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header is required"})
			c.Abort()
			return
		}

		claims, err := auth.ValidateToken(tokenString)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
			c.Abort()
			return
		}

		c.Set("user_id", claims.UserID)
		c.Set("user_type", claims.UserType)
		c.Next()
	}
}

// Login handlers
func LoginVoter(c *gin.Context) {
	var req models.LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var voter models.Voter
	var passwordHash string
	err := db.QueryRow("SELECT id, name, email, password_hash FROM voters WHERE email = ?", req.Email).
		Scan(&voter.ID, &voter.Name, &voter.Email, &passwordHash)
	if err != nil {
		log.Printf("Failed to find voter: %v", err)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid email or password"})
		return
	}

	log.Printf("Found voter with ID: %d", voter.ID)

	if err := bcrypt.CompareHashAndPassword([]byte(passwordHash), []byte(req.Password)); err != nil {
		log.Printf("Password mismatch for voter: %d", voter.ID)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid email or password"})
		return
	}

	token, err := auth.GenerateToken(voter.ID, "voter")
	if err != nil {
		log.Printf("Failed to generate token: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	log.Printf("Successfully logged in voter: %d", voter.ID)
	c.JSON(http.StatusOK, gin.H{
		"token": token,
		"user": gin.H{
			"id":    voter.ID,
			"name":  voter.Name,
			"email": voter.Email,
		},
	})
}

func LoginCandidate(c *gin.Context) {
	var req models.LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var candidate models.Candidate
	var passwordHash string
	err := db.QueryRow("SELECT id, name, email, password_hash FROM candidates WHERE email = ?", req.Email).
		Scan(&candidate.ID, &candidate.Name, &candidate.Email, &passwordHash)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid email or password"})
		return
	}

	if err := bcrypt.CompareHashAndPassword([]byte(passwordHash), []byte(req.Password)); err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid email or password"})
		return
	}

	token, err := auth.GenerateToken(candidate.ID, "candidate")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"token": token,
		"user": gin.H{
			"id":    candidate.ID,
			"name":  candidate.Name,
			"email": candidate.Email,
		},
	})
}

// Candidate handlers
func RegisterCandidate(c *gin.Context) {
	var req models.RegistrationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to hash password"})
		return
	}

	// Insert into database
	result, err := db.Exec("INSERT INTO candidates (name, email, password_hash) VALUES (?, ?, ?)",
		req.Name, req.Email, string(hashedPassword))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to register candidate"})
		return
	}

	id, _ := result.LastInsertId()
	c.JSON(http.StatusCreated, gin.H{"id": id, "message": "Candidate registered successfully"})
}

func GetCandidates(c *gin.Context) {
	rows, err := db.Query(`
        SELECT 
            c.id, 
            c.name, 
            c.email, 
            c.biography, 
            c.platform, 
            c.picture_url, 
            c.created_at,
            COALESCE(SUM(d.amount), 0) as total_donations
        FROM candidates c
        LEFT JOIN donations d ON c.id = d.candidate_id
        GROUP BY c.id
    `)
	if err != nil {
		log.Printf("Failed to fetch candidates: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch candidates"})
		return
	}
	defer rows.Close()

	var candidates []models.Candidate
	for rows.Next() {
		var candidate models.Candidate
		err := rows.Scan(
			&candidate.ID,
			&candidate.Name,
			&candidate.Email,
			&candidate.Biography,
			&candidate.Platform,
			&candidate.PictureURL,
			&candidate.CreatedAt,
			&candidate.TotalDonations,
		)
		if err != nil {
			log.Printf("Failed to scan candidate: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to scan candidate"})
			return
		}
		candidates = append(candidates, candidate)
	}

	// Convert to JSON-friendly format
	type JSONCandidate struct {
		ID             int       `json:"id"`
		Name           string    `json:"name"`
		Email          string    `json:"email"`
		Biography      string    `json:"biography"`
		Platform       string    `json:"platform"`
		PictureURL     string    `json:"picture_url"`
		TotalDonations float64   `json:"total_donations"`
		CreatedAt      time.Time `json:"created_at"`
	}

	var jsonCandidates []JSONCandidate
	for _, c := range candidates {
		jsonCandidates = append(jsonCandidates, JSONCandidate{
			ID:             c.ID,
			Name:           c.Name,
			Email:          c.Email,
			Biography:      c.Biography.String,
			Platform:       c.Platform.String,
			PictureURL:     c.PictureURL.String,
			TotalDonations: c.TotalDonations,
			CreatedAt:      c.CreatedAt,
		})
	}

	c.JSON(http.StatusOK, jsonCandidates)
}

// Voter handlers
func RegisterVoter(c *gin.Context) {
	var req models.RegistrationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	log.Printf("Registering voter: %s", req.Email)

	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		log.Printf("Failed to hash password: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to hash password"})
		return
	}

	result, err := db.Exec("INSERT INTO voters (name, email, password_hash) VALUES (?, ?, ?)",
		req.Name, req.Email, string(hashedPassword))
	if err != nil {
		log.Printf("Failed to register voter: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to register voter"})
		return
	}

	id, _ := result.LastInsertId()
	log.Printf("Successfully registered voter with ID: %d", id)
	c.JSON(http.StatusCreated, gin.H{"id": id, "message": "Voter registered successfully"})
}

// Donation handlers
func CreateDonation(c *gin.Context) {
	var req struct {
		Amount      float64 `json:"amount" binding:"required,min=1"`
		CardNumber  string  `json:"cardNumber" binding:"required,len=16"`
		CardHolder  string  `json:"cardHolder" binding:"required"`
		ExpiryMonth int     `json:"expiryMonth" binding:"required,min=1,max=12"`
		ExpiryYear  int     `json:"expiryYear" binding:"required"`
		CVV         string  `json:"cvv" binding:"required,len=3"`
		CandidateID int     `json:"candidate_id" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		log.Printf("Failed to bind request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get voter ID from auth context
	voterID, exists := c.Get("user_id")
	if !exists {
		log.Printf("User not authenticated")
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
		return
	}

	// Verify candidate exists
	var candidateExists bool
	err := db.QueryRow("SELECT EXISTS(SELECT 1 FROM candidates WHERE id = ?)", req.CandidateID).Scan(&candidateExists)
	if err != nil {
		log.Printf("Failed to verify candidate: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to verify candidate"})
		return
	}
	if !candidateExists {
		log.Printf("Candidate not found: %d", req.CandidateID)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Candidate not found"})
		return
	}

	// Start a transaction
	tx, err := db.Begin()
	if err != nil {
		log.Printf("Failed to start transaction: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to start transaction"})
		return
	}
	defer tx.Rollback()

	// Insert bank details
	bankDetailsResult, err := tx.Exec(`
        INSERT INTO bank_details (
            voter_id, card_number, card_holder, expiry_month, expiry_year, cvv
        ) VALUES (?, ?, ?, ?, ?, ?)
    `, voterID, req.CardNumber, req.CardHolder, req.ExpiryMonth, req.ExpiryYear, req.CVV)
	if err != nil {
		log.Printf("Failed to save bank details: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save bank details"})
		return
	}

	bankDetailsID, err := bankDetailsResult.LastInsertId()
	if err != nil {
		log.Printf("Failed to get bank details ID: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get bank details ID"})
		return
	}

	// Insert donation
	donationResult, err := tx.Exec(`
        INSERT INTO donations (
            voter_id, candidate_id, bank_details_id, amount, status
        ) VALUES (?, ?, ?, ?, 'completed')
    `, voterID, req.CandidateID, bankDetailsID, req.Amount)
	if err != nil {
		log.Printf("Failed to create donation: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create donation"})
		return
	}

	donationID, err := donationResult.LastInsertId()
	if err != nil {
		log.Printf("Failed to get donation ID: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get donation ID"})
		return
	}

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		log.Printf("Failed to commit transaction: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to commit transaction"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"id":      donationID,
		"message": "Donation processed successfully",
		"amount":  req.Amount,
	})
}

// Question handlers
func CreateQuestion(c *gin.Context) {
	var question models.Question
	if err := c.ShouldBindJSON(&question); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get voter ID from auth context
	voterID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
		return
	}

	result, err := db.Exec("INSERT INTO questions (voter_id, question_text) VALUES (?, ?)",
		voterID, question.QuestionText)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create question"})
		return
	}

	id, _ := result.LastInsertId()
	c.JSON(http.StatusCreated, gin.H{"id": id, "message": "Question created successfully"})
}

func GetCandidateQuestions(c *gin.Context) {
	candidateID, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid candidate ID"})
		return
	}

	rows, err := db.Query(`
        SELECT q.id, q.voter_id, q.question_text, q.created_at,
               a.id, a.answer_text, a.created_at
        FROM questions q
        LEFT JOIN answers a ON q.id = a.question_id AND a.candidate_id = ?
        WHERE EXISTS (
            SELECT 1 FROM answers a2 
            WHERE a2.question_id = q.id AND a2.candidate_id = ?
        )
    `, candidateID, candidateID)
	if err != nil {
		log.Printf("Failed to fetch questions: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch questions"})
		return
	}
	defer rows.Close()

	type QuestionWithAnswer struct {
		Question models.Question `json:"question"`
		Answer   *models.Answer  `json:"answer,omitempty"`
	}

	var questions []QuestionWithAnswer
	for rows.Next() {
		var q models.Question
		var a models.Answer
		var answerID sql.NullInt64
		var answerText sql.NullString
		var answerCreatedAt sql.NullTime

		err := rows.Scan(
			&q.ID,
			&q.VoterID,
			&q.QuestionText,
			&q.CreatedAt,
			&answerID,
			&answerText,
			&answerCreatedAt)
		if err != nil {
			log.Printf("Failed to scan question: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to scan question"})
			return
		}

		qwa := QuestionWithAnswer{Question: q}
		if answerID.Valid {
			a.ID = int(answerID.Int64)
			a.QuestionID = q.ID
			a.AnswerText = answerText.String
			a.CreatedAt = answerCreatedAt.Time
			qwa.Answer = &a
		}

		questions = append(questions, qwa)
	}

	if err = rows.Err(); err != nil {
		log.Printf("Error iterating through questions: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error iterating through questions"})
		return
	}

	c.JSON(http.StatusOK, questions)
}

// Answer handlers
func CreateAnswer(c *gin.Context) {
	var answer models.Answer
	if err := c.ShouldBindJSON(&answer); err != nil {
		log.Printf("Failed to bind answer: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get candidate ID from auth context
	candidateID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
		return
	}

	// Verify the candidate exists
	var candidateName string
	err := db.QueryRow("SELECT name FROM candidates WHERE id = ?", candidateID).Scan(&candidateName)
	if err != nil {
		log.Printf("Failed to find candidate: %v", err)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid candidate"})
		return
	}

	log.Printf("Creating answer: question_id=%d, candidate_id=%d, answer_text=%s",
		answer.QuestionID, candidateID, answer.AnswerText)

	// Insert the answer
	result, err := db.Exec("INSERT INTO answers (question_id, candidate_id, answer_text) VALUES (?, ?, ?)",
		answer.QuestionID, candidateID, answer.AnswerText)
	if err != nil {
		log.Printf("Failed to create answer: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create answer"})
		return
	}

	id, _ := result.LastInsertId()
	log.Printf("Successfully created answer with ID: %d", id)

	// Verify the answer was stored correctly
	var storedAnswer struct {
		ID           int64
		QuestionID   int64
		AnswerText   string
		CreatedAt    time.Time
		AnswererName string
	}
	err = db.QueryRow(`
        SELECT a.id, a.question_id, a.answer_text, a.created_at, c.name
        FROM answers a
        JOIN candidates c ON a.candidate_id = c.id
        WHERE a.id = ?
    `, id).Scan(
		&storedAnswer.ID,
		&storedAnswer.QuestionID,
		&storedAnswer.AnswerText,
		&storedAnswer.CreatedAt,
		&storedAnswer.AnswererName,
	)
	if err != nil {
		log.Printf("Failed to verify stored answer: %v", err)
	} else {
		log.Printf("Verified stored answer: %+v", storedAnswer)
	}

	c.JSON(http.StatusCreated, gin.H{
		"id":      id,
		"message": "Answer created successfully",
		"answer":  storedAnswer,
	})
}

// GetCandidate returns a single candidate by ID
func GetCandidate(c *gin.Context) {
	id := c.Param("id")
	var candidate models.Candidate
	err := db.QueryRow(`
        SELECT 
            c.id, 
            c.name, 
            c.email, 
            c.biography, 
            c.platform, 
            c.picture_url, 
            c.created_at,
            COALESCE(SUM(d.amount), 0) as total_donations
        FROM candidates c
        LEFT JOIN donations d ON c.id = d.candidate_id
        WHERE c.id = ?
        GROUP BY c.id
    `, id).Scan(
		&candidate.ID,
		&candidate.Name,
		&candidate.Email,
		&candidate.Biography,
		&candidate.Platform,
		&candidate.PictureURL,
		&candidate.CreatedAt,
		&candidate.TotalDonations,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Candidate not found"})
		} else {
			log.Printf("Failed to fetch candidate: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch candidate"})
		}
		return
	}

	// Convert to JSON-friendly format
	type JSONCandidate struct {
		ID             int       `json:"id"`
		Name           string    `json:"name"`
		Email          string    `json:"email"`
		Biography      string    `json:"biography"`
		Platform       string    `json:"platform"`
		PictureURL     string    `json:"picture_url"`
		TotalDonations float64   `json:"total_donations"`
		CreatedAt      time.Time `json:"created_at"`
	}

	jsonCandidate := JSONCandidate{
		ID:             candidate.ID,
		Name:           candidate.Name,
		Email:          candidate.Email,
		Biography:      candidate.Biography.String,
		Platform:       candidate.Platform.String,
		PictureURL:     candidate.PictureURL.String,
		TotalDonations: candidate.TotalDonations,
		CreatedAt:      candidate.CreatedAt,
	}

	c.JSON(http.StatusOK, jsonCandidate)
}

// GetVoter returns a single voter by ID
func GetVoter(c *gin.Context) {
	id := c.Param("id")
	var voter models.Voter
	err := db.QueryRow(`
        SELECT id, name, email, created_at
        FROM voters
        WHERE id = ?
    `, id).Scan(
		&voter.ID, &voter.Name, &voter.Email, &voter.CreatedAt,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Voter not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch voter"})
		}
		return
	}
	c.JSON(http.StatusOK, voter)
}

// UpdateVoter updates a voter's information
func UpdateVoter(c *gin.Context) {
	id := c.Param("id")
	var voter models.Voter
	if err := c.ShouldBindJSON(&voter); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	_, err := db.Exec(`
        UPDATE voters
        SET name = ?, email = ?
        WHERE id = ?
    `, voter.Name, voter.Email, id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update voter"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Voter updated successfully"})
}

// GetVoterDonations returns all donations made by a voter
func GetVoterDonations(c *gin.Context) {
	id := c.Param("id")
	rows, err := db.Query(`
        SELECT d.id, d.amount, d.created_at, c.name as candidate_name
        FROM donations d
        JOIN candidates c ON d.candidate_id = c.id
        WHERE d.voter_id = ?
        ORDER BY d.created_at DESC
    `, id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch donations"})
		return
	}
	defer rows.Close()

	var donations []models.Donation
	for rows.Next() {
		var donation models.Donation
		err := rows.Scan(
			&donation.ID, &donation.Amount, &donation.CreatedAt, &donation.CandidateName,
		)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to scan donation"})
			return
		}
		donations = append(donations, donation)
	}
	c.JSON(http.StatusOK, donations)
}

// GetVoterQuestions returns all questions asked by a voter
func GetVoterQuestions(c *gin.Context) {
	id := c.Param("id")
	rows, err := db.Query(`
        SELECT q.id, q.question_text, q.created_at, c.name as candidate_name,
               a.answer_text, a.created_at as answer_created_at
        FROM questions q
        JOIN candidates c ON q.candidate_id = c.id
        LEFT JOIN answers a ON q.id = a.question_id
        WHERE q.voter_id = ?
        ORDER BY q.created_at DESC
    `, id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch questions"})
		return
	}
	defer rows.Close()

	var questions []models.Question
	for rows.Next() {
		var question models.Question
		var answerText sql.NullString
		var answerCreatedAt sql.NullTime
		err := rows.Scan(
			&question.ID, &question.QuestionText, &question.CreatedAt,
			&question.CandidateName, &answerText, &answerCreatedAt,
		)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to scan question"})
			return
		}
		if answerText.Valid {
			question.Answer = &models.Answer{
				AnswerText: answerText.String,
				CreatedAt:  answerCreatedAt.Time,
			}
		}
		questions = append(questions, question)
	}
	c.JSON(http.StatusOK, questions)
}

// GetQuestions returns all questions across candidates
func GetQuestions(c *gin.Context) {
	rows, err := db.Query(`
        SELECT 
            q.id, 
            q.question_text, 
            q.created_at, 
            v.name as voter_name,
            a.answer_text, 
            a.created_at as answer_created_at,
            c.name as answerer_name
        FROM questions q
        JOIN voters v ON q.voter_id = v.id
        LEFT JOIN answers a ON q.id = a.question_id
        LEFT JOIN candidates c ON a.candidate_id = c.id
        ORDER BY q.created_at DESC
    `)
	if err != nil {
		log.Printf("Failed to fetch questions: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch questions"})
		return
	}
	defer rows.Close()

	type QuestionResponse struct {
		ID           int       `json:"id"`
		QuestionText string    `json:"question_text"`
		CreatedAt    time.Time `json:"created_at"`
		VoterName    string    `json:"voter_name"`
		Answer       *struct {
			Text         string    `json:"answer_text"`
			CreatedAt    time.Time `json:"answer_created_at"`
			AnswererName string    `json:"answerer_name"`
		} `json:"answer,omitempty"`
	}

	var questions []QuestionResponse
	for rows.Next() {
		var q QuestionResponse
		var answerText sql.NullString
		var answerCreatedAt sql.NullTime
		var answererName sql.NullString

		err := rows.Scan(
			&q.ID,
			&q.QuestionText,
			&q.CreatedAt,
			&q.VoterName,
			&answerText,
			&answerCreatedAt,
			&answererName,
		)
		if err != nil {
			log.Printf("Failed to scan question: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to scan question"})
			return
		}

		log.Printf("Scanned question: ID=%d, AnswerText=%v, AnswerCreatedAt=%v, AnswererName=%v",
			q.ID, answerText, answerCreatedAt, answererName)

		if answerText.Valid {
			q.Answer = &struct {
				Text         string    `json:"answer_text"`
				CreatedAt    time.Time `json:"answer_created_at"`
				AnswererName string    `json:"answerer_name"`
			}{
				Text:         answerText.String,
				CreatedAt:    answerCreatedAt.Time,
				AnswererName: answererName.String,
			}
			log.Printf("Added answer to question %d: %+v", q.ID, q.Answer)
		}

		questions = append(questions, q)
	}

	if err = rows.Err(); err != nil {
		log.Printf("Error iterating through questions: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error iterating through questions"})
		return
	}

	log.Printf("Questions response: %+v", questions)
	c.JSON(http.StatusOK, questions)
}

// UpdateCandidate updates a candidate's profile
func UpdateCandidate(c *gin.Context) {
	id := c.Param("id")
	var req struct {
		Name       string `json:"name"`
		Biography  string `json:"biography"`
		Platform   string `json:"platform"`
		PictureURL string `json:"picture_url"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	_, err := db.Exec(`
        UPDATE candidates 
        SET name = ?, 
            biography = ?, 
            platform = ?, 
            picture_url = ?
        WHERE id = ?
    `, req.Name, req.Biography, req.Platform, req.PictureURL, id)

	if err != nil {
		log.Printf("Failed to update candidate: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update candidate"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Candidate updated successfully"})
}

// GetCandidatePayments returns all payment details for donations made to a candidate
func GetCandidatePayments(c *gin.Context) {
	// Get candidate ID from URL
	candidateID, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid candidate ID"})
		return
	}

	// Get user ID from context
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
		return
	}

	// Verify the user is the candidate
	var count int
	err = db.QueryRow("SELECT COUNT(*) FROM candidates WHERE id = ? AND id = ?", candidateID, userID).Scan(&count)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to verify candidate"})
		return
	}
	if count == 0 {
		c.JSON(http.StatusForbidden, gin.H{"error": "Not authorized to view these payments"})
		return
	}

	// Query to get all payment details for donations made to this candidate
	rows, err := db.Query(`
		SELECT bd.id, bd.card_number, bd.card_holder, bd.expiry_month, bd.expiry_year, 
		       d.amount, d.created_at, d.status
		FROM bank_details bd
		JOIN donations d ON d.bank_details_id = bd.id
		WHERE d.candidate_id = ?
		ORDER BY d.created_at DESC
	`, candidateID)
	if err != nil {
		log.Printf("Failed to fetch payment details: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch payment details"})
		return
	}
	defer rows.Close()

	type PaymentDetail struct {
		ID             int       `json:"id"`
		CardNumber     string    `json:"card_number"`
		CardholderName string    `json:"cardholder_name"`
		ExpiryMonth    int       `json:"expiry_month"`
		ExpiryYear     int       `json:"expiry_year"`
		Amount         float64   `json:"amount"`
		CreatedAt      time.Time `json:"created_at"`
		Status         string    `json:"status"`
	}

	var payments []PaymentDetail
	for rows.Next() {
		var p PaymentDetail
		err := rows.Scan(&p.ID, &p.CardNumber, &p.CardholderName, &p.ExpiryMonth, &p.ExpiryYear,
			&p.Amount, &p.CreatedAt, &p.Status)
		if err != nil {
			log.Printf("Failed to scan payment details: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to process payment details"})
			return
		}
		payments = append(payments, p)
	}

	c.JSON(http.StatusOK, gin.H{"payments": payments})
}
