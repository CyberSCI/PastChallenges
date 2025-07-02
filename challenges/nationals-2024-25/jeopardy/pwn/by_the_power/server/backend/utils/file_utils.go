package utils

import (
    "io/ioutil"
    "os"
)

// ReadSSHKey reads the stored SSH private key from the filesystem.
func ReadSSHKey(filePath string) (string, error) {
    key, err := ioutil.ReadFile(filePath)
    if err != nil {
        return "", err
    }
    return string(key), nil
}

// KeyExists checks if the specified file exists.
func KeyExists(filePath string) bool {
    _, err := os.Stat(filePath)
    return !os.IsNotExist(err)
}