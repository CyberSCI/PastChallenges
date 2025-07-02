package service

import (
	"net"
	"testing"

	"google.golang.org/grpc/peer"

	"github.com/k4yt3x/valvota/proto"
)

func TestNewSubmitVotesServer(t *testing.T) {
	// Arrange & Act
	server := NewSubmitVotesServer()

	// Assert
	if server == nil {
		t.Fatal("NewSubmitVotesServer should not return nil")
	}
	if len(server.candidates) != 10 {
		t.Errorf("Expected 10 candidates, got %d", len(server.candidates))
	}

	// Verify candidate order and data
	expectedCandidates := []Candidate{
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
	}

	for i, expected := range expectedCandidates {
		if server.candidates[i] != expected {
			t.Errorf("Candidate %d: expected %+v, got %+v", i, expected, server.candidates[i])
		}
	}
}

func TestSubmitVotesServer_getTotalCandidates(t *testing.T) {
	// Arrange
	server := NewSubmitVotesServer()

	// Act
	total := server.getTotalCandidates()

	// Assert
	if total != 10 {
		t.Errorf("Expected 10 candidates, got %d", total)
	}
}

func TestSubmitVotesServer_getCandidateName(t *testing.T) {
	// Arrange
	server := NewSubmitVotesServer()

	tests := []struct {
		name     string
		index    int
		expected string
	}{
		{"Valid index 0", 0, "Esteban de Souza"},
		{"Valid index 5", 5, "Sofia da Silva"},
		{"Valid index 9", 9, "Pedro Galeano"},
		{"Invalid negative index", -1, "Unknown Candidate"},
		{"Invalid high index", 10, "Unknown Candidate"},
		{"Invalid very high index", 100, "Unknown Candidate"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Act
			result := server.getCandidateName(tt.index)

			// Assert
			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}

func TestGetVotersForRegion(t *testing.T) {
	tests := []struct {
		name     string
		region   float64
		expected float64
	}{
		{"Verdantia (region 0)", 0, Verdantia},
		{"Elarion (region 1)", 1, Elarion},
		{"Zepharion (region 2)", 2, Zepharion},
		{"Valtara (region 3)", 3, Valtara},
		{"Eryndor (region 4)", 4, Eryndor},
		{"Invalid region -1", -1, -1},
		{"Invalid region 5", 5, -1},
		{"Invalid region 10", 10, -1},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Act
			result := getVotersForRegion(tt.region)

			// Assert
			if result != tt.expected {
				t.Errorf("Expected %f, got %f", tt.expected, result)
			}
		})
	}
}

func TestGetRegionName(t *testing.T) {
	tests := []struct {
		name     string
		region   float64
		expected string
	}{
		{"Verdantia (region 0)", 0, "Verdantia"},
		{"Elarion (region 1)", 1, "Elarion"},
		{"Zepharion (region 2)", 2, "Zepharion"},
		{"Valtara (region 3)", 3, "Valtara"},
		{"Eryndor (region 4)", 4, "Eryndor"},
		{"Invalid region -1", -1, "Unknown Region"},
		{"Invalid region 5", 5, "Unknown Region"},
		{"Invalid region 10", 10, "Unknown Region"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Act
			result := getRegionName(tt.region)

			// Assert
			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}

func TestSubmitVotesServer_validateVoteCounts(t *testing.T) {
	// Arrange
	server := NewSubmitVotesServer()

	tests := []struct {
		name        string
		voteCounts  []float64
		expectError bool
	}{
		{"Valid vote counts (10 elements)", make([]float64, 10), false},
		{"Too few vote counts (5 elements)", make([]float64, 5), true},
		{"Too many vote counts (15 elements)", make([]float64, 15), true},
		{"Empty vote counts", []float64{}, true},
		{"Single vote count", []float64{100}, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Act
			err := server.validateVoteCounts(tt.voteCounts)

			// Assert
			if tt.expectError && err == nil {
				t.Error("Expected error but got none")
			}
			if !tt.expectError && err != nil {
				t.Errorf("Expected no error but got: %v", err)
			}
		})
	}
}

func TestSubmitVotesServer_SubmitVotes(t *testing.T) {
	// Arrange
	server := NewSubmitVotesServer()

	tests := []struct {
		name            string
		region          float64
		voteCounts      []float64
		expectedSuccess bool
		expectedMessage string
		description     string
	}{
		{
			name:   "Valid votes within voter limit",
			region: 0, // Verdantia
			voteCounts: []float64{
				42,
				84,
				126,
				168,
				210,
				252,
				294,
				336,
				378,
				420,
			}, // Total after division: 25
			expectedSuccess: true,
			expectedMessage: "",
			description:     "Normal case with valid vote counts",
		},
		{
			name:   "Votes exceeding voter limit - should return flag",
			region: 4, // Eryndor (smallest region: 1,543,210 voters)
			voteCounts: []float64{
				42000000,
				42000000,
				42000000,
				42000000,
				42000000,
				42000000,
				42000000,
				42000000,
				42000000,
				42000000,
			}, // Total after division: 10,000,000
			expectedSuccess: true,
			expectedMessage: Flag,
			description:     "Votes exceed region population, should return flag",
		},
		{
			name:            "Invalid vote counts array length",
			region:          0,
			voteCounts:      []float64{42, 84, 126}, // Only 3 candidates instead of 10
			expectedSuccess: false,
			expectedMessage: "expected 10 vote counts, got 3",
			description:     "Invalid array length should cause validation error",
		},
		{
			name:            "Invalid region",
			region:          10, // Invalid region
			voteCounts:      []float64{42, 84, 126, 168, 210, 252, 294, 336, 378, 420},
			expectedSuccess: false,
			expectedMessage: "Invalid region specified",
			description:     "Invalid region should return error",
		},
		{
			name:   "Negative vote counts",
			region: 0,
			voteCounts: []float64{
				-42,
				84,
				126,
				168,
				210,
				252,
				294,
				336,
				378,
				420,
			}, // Total: -1 + 24 = 23
			expectedSuccess: true,
			expectedMessage: "",
			description:     "Negative votes should still process normally if total is positive",
		},
		{
			name:   "All negative votes",
			region: 0,
			voteCounts: []float64{
				-42,
				-84,
				-126,
				-168,
				-210,
				-252,
				-294,
				-336,
				-378,
				-420,
			}, // Total: -25
			expectedSuccess: false,
			expectedMessage: "Invalid vote count",
			description:     "All negative votes should return invalid vote count",
		},
		{
			name:            "Zero votes",
			region:          1, // Elarion
			voteCounts:      []float64{0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
			expectedSuccess: true,
			expectedMessage: "",
			description:     "Zero votes should process successfully",
		},
		{
			name:            "Empty vote counts array",
			region:          0,
			voteCounts:      []float64{},
			expectedSuccess: false,
			expectedMessage: "expected 10 vote counts, got 0",
			description:     "Empty array should cause validation error",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange - Create context with peer information
			ctx := t.Context()
			addr, _ := net.ResolveTCPAddr("tcp", "127.0.0.1:12345")
			p := &peer.Peer{Addr: addr}
			ctx = peer.NewContext(ctx, p)

			req := &proto.SubmitVotesRequest{
				Region:     tt.region,
				VoteCounts: tt.voteCounts,
			}

			// Act
			response, err := server.SubmitVotes(ctx, req)

			// Assert
			if err != nil {
				t.Fatalf("SubmitVotes returned unexpected error: %v", err)
			}
			if response == nil {
				t.Fatal("Response should not be nil")
			}
			if response.GetSuccess() != tt.expectedSuccess {
				t.Errorf(
					"Expected success=%t, got success=%t",
					tt.expectedSuccess,
					response.GetSuccess(),
				)
			}
			if tt.expectedMessage != "" && response.GetMessage() != tt.expectedMessage {
				t.Errorf(
					"Expected message=%q, got message=%q",
					tt.expectedMessage,
					response.GetMessage(),
				)
			}
		})
	}
}

func TestSubmitVotesServer_SubmitVotes_ContextWithoutPeer(t *testing.T) {
	// Arrange
	server := NewSubmitVotesServer()
	ctx := t.Context() // No peer information
	req := &proto.SubmitVotesRequest{
		Region:     0,
		VoteCounts: []float64{42, 84, 126, 168, 210, 252, 294, 336, 378, 420},
	}

	// Act
	response, err := server.SubmitVotes(ctx, req)

	// Assert
	if err != nil {
		t.Fatalf("SubmitVotes returned unexpected error: %v", err)
	}
	if response == nil {
		t.Fatal("Response should not be nil")
	}
	// Should still work without peer information
	if !response.GetSuccess() {
		t.Error("Expected success=true even without peer information")
	}
}

func TestSubmitVotesServer_SubmitVotes_EdgeCaseVoteTotals(t *testing.T) {
	// Arrange
	server := NewSubmitVotesServer()

	tests := []struct {
		name            string
		region          float64
		voteCounts      []float64
		expectedSuccess bool
		description     string
	}{
		{
			name:   "Exactly at voter limit",
			region: 4, // Eryndor: 1,543,210 voters
			voteCounts: []float64{
				1543210 * 42,
				0,
				0,
				0,
				0,
				0,
				0,
				0,
				0,
				0,
			}, // Exactly 1,543,210 votes after division
			expectedSuccess: true,
			description:     "Votes exactly equal to voter limit should succeed",
		},
		{
			name:   "One vote over limit",
			region: 4, // Eryndor: 1,543,210 voters
			voteCounts: []float64{
				(1543210 * 42) + 42,
				0,
				0,
				0,
				0,
				0,
				0,
				0,
				0,
				0,
			}, // 1,543,211 votes after division
			expectedSuccess: true,
			description:     "One vote over limit should return flag",
		},
		{
			name:   "Large region with valid votes",
			region: 0, // Verdantia: 12,125,863 voters
			voteCounts: []float64{
				1000 * 42,
				2000 * 42,
				3000 * 42,
				4000 * 42,
				5000 * 42,
				6000 * 42,
				7000 * 42,
				8000 * 42,
				9000 * 42,
				10000 * 42,
			}, // Total: 55,000 votes
			expectedSuccess: true,
			description:     "Large region with reasonable vote distribution",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			ctx := t.Context()
			req := &proto.SubmitVotesRequest{
				Region:     tt.region,
				VoteCounts: tt.voteCounts,
			}

			// Act
			response, err := server.SubmitVotes(ctx, req)

			// Assert
			if err != nil {
				t.Fatalf("SubmitVotes returned unexpected error: %v", err)
			}
			if response.GetSuccess() != tt.expectedSuccess {
				t.Errorf(
					"Expected success=%t, got success=%t",
					tt.expectedSuccess,
					response.GetSuccess(),
				)
			}
		})
	}
}

func TestConstants(t *testing.T) {
	// Arrange & Act & Assert
	// Test that all region voter constants are positive
	regions := map[string]float64{
		"Verdantia": Verdantia,
		"Elarion":   Elarion,
		"Zepharion": Zepharion,
		"Valtara":   Valtara,
		"Eryndor":   Eryndor,
	}

	for name, voters := range regions {
		if voters <= 0 {
			t.Errorf("Region %s should have positive voter count, got %f", name, voters)
		}
	}

	// Test flag constant
	if Flag == "" {
		t.Error("Flag constant should not be empty")
	}
	expectedFlag := "flag{g1mm3_g1mm3_g1mm3_an_ex7r4_v0t3_aft3r_m1dnight}"
	if Flag != expectedFlag {
		t.Errorf("Expected flag=%q, got flag=%q", expectedFlag, Flag)
	}
}

// Benchmark test for performance validation.
func BenchmarkSubmitVotes(b *testing.B) {
	// Arrange
	server := NewSubmitVotesServer()
	ctx := b.Context()
	req := &proto.SubmitVotesRequest{
		Region:     0,
		VoteCounts: []float64{42, 84, 126, 168, 210, 252, 294, 336, 378, 420},
	}

	b.ResetTimer()
	// for i := 0; i < b.N; i++ {
	for b.Loop() {
		// Act
		_, err := server.SubmitVotes(ctx, req)

		// Assert
		if err != nil {
			b.Fatalf("SubmitVotes returned error: %v", err)
		}
	}
}
