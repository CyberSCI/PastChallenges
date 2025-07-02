package auth

import (
    "errors"
    "time"

    "github.com/golang-jwt/jwt/v5"
)

var (
    ErrInvalidToken = errors.New("invalid token")
    ErrExpiredToken = errors.New("token has expired")
)

const (
    TokenExpiration = 24 * time.Hour
    SecretKey      = "your-secret-key" // In production, use environment variable
)

type Claims struct {
    UserID   int    `json:"user_id"`
    UserType string `json:"user_type"` // "voter" or "candidate"
    jwt.RegisteredClaims
}

func GenerateToken(userID int, userType string) (string, error) {
    claims := Claims{
        UserID:   userID,
        UserType: userType,
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(TokenExpiration)),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
            NotBefore: jwt.NewNumericDate(time.Now()),
        },
    }

    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString([]byte(SecretKey))
}

func ValidateToken(tokenString string) (*Claims, error) {
    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
        return []byte(SecretKey), nil
    })

    if err != nil {
        if errors.Is(err, jwt.ErrTokenExpired) {
            return nil, ErrExpiredToken
        }
        return nil, ErrInvalidToken
    }

    if claims, ok := token.Claims.(*Claims); ok && token.Valid {
        return claims, nil
    }

    return nil, ErrInvalidToken
} 