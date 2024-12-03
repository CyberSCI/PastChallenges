# secret rally

## CTFd

### Category

Web

### Description

```
Only authorized members know where the next rally is.

Flag format: `cybersci{[A-Za-z0-9_-]+}`
```

### Connection Info

```
https://10.0.2.61
```

### Files

[challenges/web/secret_rally/release_files/secret_rally.zip](./release_files/secret_rally.zip)

## Walkthrough

Flag to give to sponsors: `cybersci{s3cr3t_h1de0ut}`

```
This challenge is a web service two vulnerabilities:

1. An authentication bypass which allows a user to login without knowning a password.
2. An SQL injection vulnerability, only accessible to logged in users.

Using the first vulnerability, you can craft JSON Web Tokens (JWTs) to attempt to authenticate. For this service, in order for your JWT to be accepted, it needs to refer to a valid username.

By analyzing the code, you can find that a default account adminXXXX is created on startup (XXXX is a random number from 1000 to 1999). By crafting JWTs and trying every possible username, you can find the correct one. From here, you can access the dashboard.

In the dashboard, there is a list of rallies and a form to add an attendee to a rally. From here you can use the SQL injection to get the flag from the database. There are multiple valid ways to do this. One way is to set hidden=TRUE for all rows in the Rallies table. Then you will be able to see the flag in the dashboard.
```

## Deployment Instructions

Included in [SETUP.md](./SETUP.md).