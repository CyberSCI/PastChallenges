from unittest.mock import patch

import pytest

from authentication import hasher as hasher_module
from authentication.hasher import ReclaimerPasswordHasher


@pytest.fixture
def hasher():
    """Returns a ReclaimerPasswordHasher instance."""
    return ReclaimerPasswordHasher()


class TestReclaimerPasswordHasher:
    """Test suite for ReclaimerPasswordHasher."""

    def test_encode_returns_prefixed_hash(
        self, hasher: ReclaimerPasswordHasher, mock_iterations
    ):
        """Hash starts with algorithm identifier."""
        password = "testpassword123"
        salt = hasher.salt()
        encoded = hasher.encode(password, salt)

        assert encoded.startswith("argon2")

    def test_encode_produces_valid_argon2_format(
        self, hasher: ReclaimerPasswordHasher, mock_iterations
    ):
        """Output is parseable argon2 hash."""
        password = "testpassword123"
        salt = hasher.salt()
        encoded = hasher.encode(password, salt)

        # Remove algorithm prefix and verify the rest is valid argon2
        hash_data = hasher.decode(encoded)
        assert "algorithm" in hash_data
        assert "hash" in hash_data
        assert "salt" in hash_data
        assert "time_cost" in hash_data
        assert "memory_cost" in hash_data
        assert "parallelism" in hash_data

    def test_verify_correct_password_returns_true(
        self, hasher: ReclaimerPasswordHasher, mock_iterations
    ):
        """Round-trip encode → verify works."""
        password = "correctpassword"
        salt = hasher.salt()
        encoded = hasher.encode(password, salt)

        assert hasher.verify(password, encoded) is True

    def test_verify_wrong_password_returns_false(
        self, hasher: ReclaimerPasswordHasher, mock_iterations
    ):
        """Wrong password rejected."""
        password = "correctpassword"
        wrong_password = "wrongpassword"
        salt = hasher.salt()
        encoded = hasher.encode(password, salt)

        assert hasher.verify(wrong_password, encoded) is False

    def test_verify_wrong_algorithm_raises(
        self, hasher: ReclaimerPasswordHasher, mock_iterations
    ):
        """Assertion fails if algorithm mismatch."""
        password = "testpassword"
        salt = hasher.salt()
        encoded = hasher.encode(password, salt)

        # Replace algorithm prefix with a wrong one
        wrong_encoded = "wrongalgo$" + encoded.split("$", 1)[1]

        with pytest.raises(AssertionError):
            _ = hasher.verify(password, wrong_encoded)

    def test_different_salts_produce_different_hashes(
        self, hasher: ReclaimerPasswordHasher, mock_iterations
    ):
        """Salt uniqueness."""
        password = "samepassword"
        salt1 = hasher.salt()
        salt2 = hasher.salt()

        # Salts should be different
        assert salt1 != salt2

        encoded1 = hasher.encode(password, salt1)
        encoded2 = hasher.encode(password, salt2)

        # Hashes should be different
        assert encoded1 != encoded2

    def test_same_inputs_produce_same_hash(
        self, hasher: ReclaimerPasswordHasher, mock_iterations
    ):
        """Deterministic hashing with same inputs."""
        password = "deterministictest"
        salt = "fixedsaltvalue"

        encoded1 = hasher.encode(password, salt)
        encoded2 = hasher.encode(password, salt)

        assert encoded1 == encoded2

    def test_unicode_password_handling(
        self, hasher: ReclaimerPasswordHasher, mock_iterations
    ):
        """Non-ASCII passwords work."""
        password = "пароль密码🔐"  # Russian + Chinese + emoji
        salt = hasher.salt()
        encoded = hasher.encode(password, salt)

        assert hasher.verify(password, encoded) is True

    def test_empty_password_handling(
        self, hasher: ReclaimerPasswordHasher, mock_iterations
    ):
        """Empty string password behavior."""
        password = ""
        salt = hasher.salt()
        encoded = hasher.encode(password, salt)

        assert hasher.verify(password, encoded) is True
        assert hasher.verify("notempty", encoded) is False

    def test_pepper_affects_hash(
        self, hasher: ReclaimerPasswordHasher, mock_iterations
    ):
        """Changing pepper changes output."""
        password = "peppertest"
        salt = "fixedsalt"

        encoded_default = hasher.encode(password, salt)

        # Hash with different pepper
        with patch.object(hasher_module, "PEPPER", "different-pepper"):
            encoded_different = hasher.encode(password, salt)

        assert encoded_default != encoded_different
