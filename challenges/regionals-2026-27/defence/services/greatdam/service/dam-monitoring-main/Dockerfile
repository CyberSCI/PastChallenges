FROM golang:1.27-alpine

WORKDIR /app

COPY go.mod ./
RUN go mod download

COPY main.go routes.go ping.go monitoring.go ./
RUN go mod tidy
RUN CGO_ENABLED=0 GOOS=linux go build -o app .

ENTRYPOINT ["./app"]
