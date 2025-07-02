package main

import (
	"ValidationServer/handlers"
	"log"
	"net/http"
)

func main() {

	http.HandleFunc("/api/check-ssh-key", handlers.CheckSSHKeyHandler)

	log.Println("Starting server on :8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("Could not start server: %s\n", err)
	}
}
