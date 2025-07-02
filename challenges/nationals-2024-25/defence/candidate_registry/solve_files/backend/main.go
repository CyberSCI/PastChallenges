package main

import (
	"database/sql"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"

	"voter-registry/backend/handlers"

	"github.com/gin-gonic/gin"
	_ "github.com/mattn/go-sqlite3"
)

var db *sql.DB

func initDB(dbPath string) error {
	var err error
	db, err = sql.Open("sqlite3", dbPath)
	if err != nil {
		return err
	}

	// Create data directory if it doesn't exist
	dataDir := filepath.Dir(dbPath)
	if err := os.MkdirAll(dataDir, 0755); err != nil {
		return err
	}

	// Read and execute schema
	schema, err := ioutil.ReadFile("/app/db/schema.sql")
	if err != nil {
		return err
	}

	_, err = db.Exec(string(schema))
	return err
}

func main() {
	// Initialize database
	dbPath := os.Getenv("DB_PATH")
	if dbPath == "" {
		dbPath = "./data/voter.db"
	}

	if err := initDB(dbPath); err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// Initialize handlers
	handlers.InitHandlers(db)

	// Initialize router
	r := gin.Default()

	// Public routes
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status": "ok",
		})
	})

	// Auth routes
	auth := r.Group("/auth")
	{
		auth.POST("/register/candidate", handlers.RegisterCandidate)
		auth.POST("/register/voter", handlers.RegisterVoter)
		auth.POST("/login/candidate", handlers.LoginCandidate)
		auth.POST("/login/voter", handlers.LoginVoter)
	}

	// Protected routes
	protected := r.Group("/api")
	protected.Use(handlers.AuthMiddleware())
	{
		// Candidate routes
		candidates := protected.Group("/candidates")
		{
			candidates.GET("/", handlers.GetCandidates)
			candidates.GET("/:id", handlers.GetCandidate)
			candidates.PUT("/:id", handlers.UpdateCandidate)
			candidates.GET("/:id/questions", handlers.GetCandidateQuestions)
			candidates.GET("/:id/payments", handlers.GetCandidatePayments)
		}

		// Voter routes
		voters := protected.Group("/voters")
		{
			voters.GET("/:id/donations", handlers.GetVoterDonations)
			voters.GET("/:id/questions", handlers.GetVoterQuestions)
		}

		// Donation routes
		donations := protected.Group("/donations")
		{
			donations.POST("/", handlers.CreateDonation)
		}

		// Question routes
		questions := protected.Group("/questions")
		{
			questions.GET("/", handlers.GetQuestions)
			questions.POST("/", handlers.CreateQuestion)
		}

		// Answer routes
		answers := protected.Group("/answers")
		{
			answers.POST("/", handlers.CreateAnswer)
		}
	}

	// Start server
	if err := r.Run(":8080"); err != nil {
		log.Fatal(err)
	}
}
