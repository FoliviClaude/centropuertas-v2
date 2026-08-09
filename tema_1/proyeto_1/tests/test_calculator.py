from src.calculator import add, subtract, multiply, divide
import pytest

def test_add():
    assert add(2, 3) == 5

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(1, 0)