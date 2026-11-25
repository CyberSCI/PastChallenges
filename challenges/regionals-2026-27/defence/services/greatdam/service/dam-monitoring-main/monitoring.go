package main

import (
	"compress/gzip"
	"encoding/json"
	"net/http"
	"strings"

	"github.com/gorilla/websocket"
)

func GetLogs(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	var decoder *json.Decoder
	var logRequests []string
	var err error

	decoder = json.NewDecoder(r.Body)
	err = decoder.Decode(&logRequests)

	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		return
	}

	var conn *websocket.Conn
	conn, _, err = websocket.DefaultDialer.Dial("ws://monitoringfs:4444/fs", nil)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	defer conn.Close()

	var log []byte
	var accumulatedLogs []byte
	for _, logRequest := range logRequests {
		if !strings.HasPrefix(logRequest, "./") {
			continue
		}

		err = conn.WriteMessage(websocket.TextMessage, []byte(logRequest))
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		_, log, err = conn.ReadMessage()
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		accumulatedLogs = append(accumulatedLogs, append(log, []byte(":::")...)...)
	}

	w.Header().Add("Vary", "Accept-Encoding")
	w.Header().Set("Content-Encoding", "gzip")
	w.WriteHeader(http.StatusOK)

	var gzipWriter *gzip.Writer
	gzipWriter = gzip.NewWriter(w)
	defer gzipWriter.Close()

	gzipWriter.Write(accumulatedLogs)
}
