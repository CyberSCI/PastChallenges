package service

import (
	"context"
	"fmt"

	"github.com/rs/zerolog/log"
	"google.golang.org/grpc/peer"

	"github.com/k4yt3x/valvota/proto"
)

const Flag = "flag{g1mm3_g1mm3_g1mm3_an_ex7r4_v0t3_aft3r_m1dnight}"

// Number of voters in each region.
const (
	Verdantia = 12_125_863
	Elarion   = 3_456_789
	Zepharion = 8_765_432
	Valtara   = 10_234_567
	Eryndor   = 1_543_210
)

// Candidate represents a candidate with their ID and name.
type Candidate struct {
	ID   int
	Name string
}

// SubmitVotesServer implements the SubmitVotesService defined in the proto file.
type SubmitVotesServer struct {
	proto.UnimplementedSubmitVotesServiceServer
	candidates []Candidate
}

// NewSubmitVotesServer creates a new SubmitVotesServer with the candidate list.
// The order must match the order of vote_counts in the protobuf message.
func NewSubmitVotesServer() *SubmitVotesServer {
	return &SubmitVotesServer{
		candidates: []Candidate{
			{ID: 0, Name: "Esteban de Souza"},
			{ID: 1, Name: "Arius Perez"},
			{ID: 2, Name: "Raphael Velasquez"},
			{ID: 3, Name: "Gen Ramon Esperanza"},
			{ID: 4, Name: "Joel Plata"},
			{ID: 5, Name: "Sofia da Silva"},
			{ID: 6, Name: "Ana Paula Espinoza"},
			{ID: 7, Name: "Vera Gomes"},
			{ID: 8, Name: "Xavier Gonzalez"},
			{ID: 9, Name: "Pedro Galeano"},
		},
	}
}

// getTotalCandidates returns the expected number of candidates.
func (s *SubmitVotesServer) getTotalCandidates() int {
	return len(s.candidates)
}

// getCandidateName returns the name of a candidate by their index.
func (s *SubmitVotesServer) getCandidateName(index int) string {
	if index < 0 || index >= len(s.candidates) {
		return "Unknown Candidate"
	}
	return s.candidates[index].Name
}

// getVotersForRegion returns the number of voters in a given region.
func getVotersForRegion(region float64) float64 {
	switch region {
	case 0:
		return Verdantia
	case 1:
		return Elarion
	case 2:
		return Zepharion
	case 3:
		return Valtara
	case 4:
		return Eryndor
	default: // Invalid region
		return -1
	}
}

func getRegionName(region float64) string {
	switch region {
	case 0:
		return "Verdantia"
	case 1:
		return "Elarion"
	case 2:
		return "Zepharion"
	case 3:
		return "Valtara"
	case 4:
		return "Eryndor"
	default: // Invalid region
		return "Unknown Region"
	}
}

// validateVoteCounts checks if the vote counts array has the correct length.
func (s *SubmitVotesServer) validateVoteCounts(voteCounts []float64) error {
	expectedCount := s.getTotalCandidates()
	if len(voteCounts) != expectedCount {
		return fmt.Errorf("expected %d vote counts, got %d", expectedCount, len(voteCounts))
	}
	return nil
}

// SubmitVotes processes the votes submitted by the user for a specific region.
func (s *SubmitVotesServer) SubmitVotes(
	ctx context.Context,
	req *proto.SubmitVotesRequest,
) (*proto.SubmitVotesResponse, error) {
	// Log client IP and port along with region
	clientAddr := "unknown"
	if addr, ok := peer.FromContext(ctx); ok {
		clientAddr = addr.Addr.String()
	}
	log.Debug().
		Float64("region", req.GetRegion()).
		Str("client_addr", clientAddr).
		Msg("Processing votes from client")

	// Validate vote counts array
	voteCounts := req.GetVoteCounts()
	if err := s.validateVoteCounts(voteCounts); err != nil {
		log.Error().Err(err).Msg("Invalid vote counts")
		return &proto.SubmitVotesResponse{
			Success: false,
			Message: err.Error(),
		}, nil
	}

	// Process votes for each candidate (divide by 42 as in original logic)
	processedVotes := make([]float64, len(voteCounts))
	var totalVotes float64

	for i, rawVotes := range voteCounts {
		processedVotes[i] = rawVotes / 42
		totalVotes += processedVotes[i]

		// Log individual candidate votes
		log.Debug().
			Int("candidate_id", i).
			Str("candidate_name", s.getCandidateName(i)).
			Float64("processed_votes", processedVotes[i]).
			Msg("Candidate vote processing")
	}

	// Log the total votes
	log.Info().
		Float64("votes", totalVotes).
		Str("region", getRegionName(req.GetRegion())).
		Msg("Total votes in region")

	success := false
	responseMessage := ""

	// Get the total number of voters in the region
	votersInRegion := getVotersForRegion(req.GetRegion())

	// Assign the response message based on different conditions
	switch {
	case totalVotes < 0:
		log.Error().Msg("Received negative vote count")
		responseMessage = "Invalid vote count"
	case votersInRegion < 0:
		log.Error().Msg("Invalid region specified")
		responseMessage = "Invalid region specified"
	case totalVotes > votersInRegion:
		log.Warn().Msg("Total votes exceed number of voters in region, returning the flag")
		success = true
		responseMessage = Flag
	default:
		log.Info().Msg("Votes processed successfully, but no flag is returned")
		success = true
	}

	return &proto.SubmitVotesResponse{
		Success: success,
		Message: responseMessage,
	}, nil
}
