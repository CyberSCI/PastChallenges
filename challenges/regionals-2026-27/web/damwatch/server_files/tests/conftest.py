import pytest

from server_files.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        flag_1="test-one",
        flag_2="test-two",
        flag_3="test-three",
        public_origin="https://damwatch.test",
    )
