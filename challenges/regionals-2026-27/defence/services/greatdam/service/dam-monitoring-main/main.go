package main

import (
	"net/http"
)

func main() {
	BindRoutes()
	_ = http.ListenAndServe(":3333", nil)
}
