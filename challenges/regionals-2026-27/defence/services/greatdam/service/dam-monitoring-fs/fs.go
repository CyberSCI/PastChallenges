package main

import (
	"io"
	"net/http"
	"os"
	"time"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{}

func Fs(w http.ResponseWriter, r *http.Request) {
	var conn *websocket.Conn
	var err error

	conn, err = upgrader.Upgrade(w, r, nil)
	if err != nil {
		http.Error(w, "", http.StatusInternalServerError)
		return
	}
	defer conn.Close()

	var msgType int
	var message []byte
	var msgStr string
	var file *os.File
	for {
		msgType, message, err = conn.ReadMessage()
		if err != nil || msgType != websocket.TextMessage {
			return
		}

		msgStr = string(message)

		file, err = os.Open(msgStr)

		if err != nil {
			conn.WriteControl(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseInternalServerErr, ""), time.Now().Add(time.Second))
			return
		}

		message, err = io.ReadAll(file)
		file.Close()
		if err != nil {
			conn.WriteControl(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseInternalServerErr, ""), time.Now().Add(time.Second))
			return
		}

		conn.WriteMessage(websocket.TextMessage, message)
	}
}
