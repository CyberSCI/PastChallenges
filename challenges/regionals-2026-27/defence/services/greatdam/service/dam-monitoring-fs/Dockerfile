FROM golang:1.27-alpine

WORKDIR /app

COPY go.mod ./
RUN go mod download

COPY main.go fs.go ping.go ./
RUN go mod tidy
RUN CGO_ENABLED=0 GOOS=linux go build -o app .

COPY logs.tar.gz ./
RUN tar -xzf logs.tar.gz

ENTRYPOINT ["./app"]
