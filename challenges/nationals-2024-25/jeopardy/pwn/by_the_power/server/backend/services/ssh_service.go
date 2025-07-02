package services

import (
	"encoding/json"
	"io/ioutil"
	"strings"
)

type Request struct {
	Input string `json:"input"`
}
type Response struct {
	Valid bool   `json:"valid"`
	Flag  string `json:"flag,omitempty"`
}

// ValidateSSHKey compares the provided SSH private key with the stored key.
func ValidateSSHKey(providedKeyJSON string) (bool, error) {
	storedKey, err := readStoredKey("/app/files/stored_key.pem")
	if err != nil {
		return false, err // Propagate error from readStoredKey
	}
	// Normalize stored key: remove newlines and trim whitespace
	storedKeyNormalized := strings.ReplaceAll(storedKey, "\n", "")
	storedKeyNormalized = strings.ReplaceAll(storedKeyNormalized, " ", "")

	r := &Request{}
	err = json.Unmarshal([]byte(providedKeyJSON), r) // Check potential error during unmarshalling
	if err != nil {
		return false, err // Invalid JSON input
	}
	providedKey := r.Input

	// Normalize provided key: remove newlines and trim whitespace
	providedKeyNormalized := strings.ReplaceAll(providedKey, "\n", "")
	providedKeyNormalized = strings.ReplaceAll(providedKeyNormalized, " ", "")

	return providedKeyNormalized == storedKeyNormalized, nil
}

// readStoredKey reads the stored SSH private key from the specified file.
func readStoredKey(filePath string) (string, error) {
	keyData, err := ioutil.ReadFile(filePath)
	if err != nil {
		return "", err
	}

	// block, _ := pem.Decode(keyData)
	// if block == nil || block.Type != "PRIVATE KEY" {
	// 	return "", errors.New("failed to decode PEM block containing the private key")
	// }

	return string(keyData), nil
}
