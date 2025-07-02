# SSH Key Validation Project

This project consists of a Go backend and a React frontend that allows users to check if a provided SSH private key matches a stored key.

## Project Structure

```
server
├── backend
│   ├── main.go                # Entry point for the Go backend application
│   ├── handlers
│   │   └── ssh_handler.go      # Handles requests for SSH key validation
│   ├── services
│   │   └── ssh_service.go      # Contains logic for validating SSH keys
│   ├── utils
│   │   └── file_utils.go       # Utility functions for file operations
│   └── files
│       └── stored_key.pem      # Stored SSH private key for comparison
├── frontend
│   ├── public
│   │   └── index.html          # Main HTML file for the frontend application
│   ├── src
│   │   ├── App.js              # Main component of the React application
│   │   ├── components
│   │   │   └── SSHKeyInput.js   # Component for user input of SSH key
│   │   └── styles
│   │       └── App.css         # CSS styles for the frontend application
│   ├── package.json            # Configuration file for npm
│   └── vite.config.js          # Configuration file for Vite
└── README.md                   # Documentation for the project
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd server
   ```

2. **Backend Setup:**
   - Navigate to the `backend` directory.
   - Ensure you have Go installed.
   - Run the backend server:
     ```
     go run main.go
     ```
