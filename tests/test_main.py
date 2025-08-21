import pytest
from src.my_project.main import greet


def test_greet():
    """Test the greet function."""
    assert greet("World") == "Hello, World!"
    assert greet("Python") == "Hello, Python!"
