package main

import (
	"net/http"
)

func BindRoutes() {
	http.HandleFunc("/ping", Ping)
	http.HandleFunc("/logs", GetLogs)
}
