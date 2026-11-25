package main

import "net/http"

func main() {
	http.HandleFunc("/fs", Fs)
	http.HandleFunc("/ping", Ping)
	_ = http.ListenAndServe(":4444", nil)
}
