package handlers

import (
	"fmt"
	"io/ioutil"
	"net/http"
	"strings"

	"ValidationServer/services"
)

func CheckSSHKeyHandler(w http.ResponseWriter, r *http.Request) {
	header := w.Header()
	header.Add("Access-Control-Allow-Origin", "*")
	header.Add("Access-Control-Allow-Methods", "POST, OPTIONS")
	if r.Method == "OPTIONS" {
		fmt.Println("Received OPTIONS request")
		header.Add("Access-Control-Allow-Methods", "POST, OPTIONS")
		header.Add("Access-Control-Allow-Headers", "Content-Type")
		w.WriteHeader(http.StatusOK)
		return
	}
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Unable to read request body", http.StatusBadRequest)
		return
	}

	privateKey := strings.TrimSpace(string(body))
	isValid, _ := services.ValidateSSHKey(privateKey) // Check error

	if isValid {
		w.WriteHeader(http.StatusOK)
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"valid", "flag":"flag{divisive-gas-graceless-ogre}"}`))
	} else {
		w.WriteHeader(http.StatusOK)
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"invalid"}`))
	}
}
