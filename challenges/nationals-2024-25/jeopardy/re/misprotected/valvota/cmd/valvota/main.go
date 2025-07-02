package main

import (
	"flag"
	"net"
	"os"
	"path/filepath"
	"strconv"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"google.golang.org/grpc"

	"github.com/k4yt3x/valvota/internal/service"
	"github.com/k4yt3x/valvota/proto"
)

func main() {
	// Parse command line flags
	address := flag.String("a", "0.0.0.0:5741", "Address to listen on")
	flag.Parse()

	// Setup zerolog for structured logging
	zerolog.CallerMarshalFunc = func( //nolint:reassign // Customize caller format
		_ uintptr, file string, line int,
	) string {
		return filepath.Base(file) + ":" + strconv.Itoa(line)
	}
	log.Logger = log.Output( //nolint:reassign // Replace the default logger
		zerolog.ConsoleWriter{Out: os.Stderr}).
		With().
		Caller().
		Timestamp().
		Logger()
	log.Info().Msgf("Initializing ValVota Server")

	log.Info().
		Str("address", *address).
		Msg("Opening listening socket")

	// Create a listening socket on the specified address
	socket, err := net.Listen("tcp", *address)
	if err != nil {
		log.Fatal().
			Str("address", *address).Msg("Failed to create listening socket")
	}

	log.Info().Msg("Starting gRPC server")

	// Create a new gRPC server and register the service
	grpcServer := grpc.NewServer()
	proto.RegisterSubmitVotesServiceServer(grpcServer, service.NewSubmitVotesServer())

	// Start serving the gRPC server
	err = grpcServer.Serve(socket)
	if err != nil {
		log.Fatal().Msg("Failed to start gRPC server")
	}
}
