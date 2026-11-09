"""Тесты логики калькулятора. Запуск: pytest"""

import pytest

from calculator import ERROR_TEXT, Calculator, format_number


def press_all(keys):
    """Нажимает клавиши по очереди и возвращает то, что осталось на дисплее."""
    calculator = Calculator()
    for key in keys:
        calculator.press(key)
    return calculator.display


@pytest.mark.parametrize(
    "keys, expected",
    [
        (["2", "+", "3", "="], "5"),
        (["9", "-", "1", "2", "="], "-3"),
        (["6", "*", "7", "="], "42"),
        (["7", "÷", "2", "="], "3.5"),
        (["2", "+", "3", "*", "4", "="], "20"),  # вычисление по порядку нажатия
        (["0", ".", "1", "+", "0", ".", "2", "="], "0.3"),
        (["5", "+", "="], "10"),  # второе число не введено — берётся первое
    ],
)
def test_arithmetic(keys, expected):
    assert press_all(keys) == expected


@pytest.mark.parametrize(
    "keys, expected",
    [
        (["9", "√"], "3"),
        (["4", "x²"], "16"),
        (["4", "1/x"], "0.25"),
        (["5", "±"], "-5"),
        (["2", "0", "0", "+", "1", "0", "%"], "20"),
        (["2", "0", "0", "+", "1", "0", "%", "="], "220"),
    ],
)
def test_unary_operations(keys, expected):
    assert press_all(keys) == expected


@pytest.mark.parametrize("operation", ["x²", "√", "%"])
def test_unary_result_zero_is_kept(operation):
    # В v0.3 результат 0 терялся, и вместо него подставлялась отложенная операция.
    assert press_all(["5", "+", "0", operation]) == "0"
    assert press_all(["5", "+", "0", operation, "="]) == "5"


def test_two_operations_in_a_row_replace_each_other():
    # В v0.3 "5 + + 3 =" давало 13.
    assert press_all(["5", "+", "+", "3", "="]) == "8"
    assert press_all(["5", "+", "*", "3", "="]) == "15"


def test_operation_after_unary_uses_its_result():
    assert press_all(["5", "+", "3", "x²", "="]) == "14"


@pytest.mark.parametrize(
    "keys",
    [
        ["7", "÷", "0", "="],
        ["0", "1/x"],
        ["4", "±", "√"],
    ],
)
def test_errors(keys):
    assert press_all(keys) == ERROR_TEXT


def test_error_blocks_operations_until_new_number():
    calculator = Calculator()
    for key in ["7", "÷", "0", "=", "+", "√"]:
        calculator.press(key)
    assert calculator.display == ERROR_TEXT
    calculator.press("4")
    calculator.press("+")
    calculator.press("1")
    assert calculator.press("=") == "5"


def test_overflow_is_an_error():
    keys = ["9"] * 15 + ["x²"] * 6
    assert press_all(keys) == ERROR_TEXT


def test_input_editing():
    assert press_all([".", "5"]) == "0.5"
    assert press_all(["1", ".", ".", "5"]) == "1.5"
    assert press_all(["0", "0", "7"]) == "7"
    assert press_all(["1", "2", "3", "←"]) == "12"
    assert press_all(["5", "←"]) == "0"
    assert press_all(["5", "±", "←"]) == "0"
    assert press_all(["2", "+", "3", "=", "←"]) == "5"  # результат не стирается
    assert press_all(["0", "±"]) == "0"


def test_input_length_is_limited():
    assert press_all(["1"] * 20) == "1" * 15


def test_clear_entry_keeps_pending_operation():
    assert press_all(["8", "+", "5", "CE", "2", "="]) == "10"


def test_clear_all_resets_everything():
    assert press_all(["8", "+", "5", "C", "2", "="]) == "2"


def test_unknown_key():
    with pytest.raises(ValueError):
        Calculator().press("sin")


@pytest.mark.parametrize(
    "value, expected",
    [
        (5.0, "5"),
        (-0.0, "0"),
        (0.1 + 0.2, "0.3"),
        (1 / 3, "0.333333333333333"),
        (123456789012345.0, "123456789012345"),
        (1e20, "1e+20"),
    ],
)
def test_format_number(value, expected):
    assert format_number(value) == expected
