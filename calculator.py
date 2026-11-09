"""Логика калькулятора без графического интерфейса.

Класс Calculator принимает нажатия клавиш (строки вроде "7", "+", "√")
и хранит текст, который должен быть на дисплее. Интерфейс только передаёт
ему нажатия и показывает результат, поэтому логику можно проверять
автоматическими тестами без окна.
"""

from __future__ import annotations

import math
import operator

DIGITS = "0123456789"
ERROR_TEXT = "Error"
MAX_INPUT_DIGITS = 15  # дальше точности float уже не хватает
SIGNIFICANT_DIGITS = 15  # сколько значащих цифр показывать в результате


class CalcError(Exception):
    """Операция не имеет результата: деление на ноль, корень из отрицательного числа и т. п."""


def divide(a: float, b: float) -> float:
    if b == 0:
        raise CalcError("деление на ноль")
    return a / b


def reciprocal(x: float) -> float:
    if x == 0:
        raise CalcError("деление на ноль")
    return 1 / x


def square_root(x: float) -> float:
    if x < 0:
        raise CalcError("корень из отрицательного числа")
    return math.sqrt(x)


BINARY_OPERATIONS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "÷": divide,
}

UNARY_OPERATIONS = {
    "1/x": reciprocal,
    "x²": lambda x: x * x,
    "√": square_root,
}


def format_number(value: float) -> str:
    """Превращает число в текст для дисплея: 5.0 -> "5", 0.1 + 0.2 -> "0.3"."""
    if not math.isfinite(value):
        raise CalcError("слишком большое число")
    if value == 0:
        return "0"  # чтобы не показывать "-0"
    return f"{value:.{SIGNIFICANT_DIGITS}g}"


class Calculator:
    """Калькулятор с последовательным вычислением: 2 + 3 * 4 = 20, как в простом калькуляторе."""

    def __init__(self) -> None:
        self._clear_all()

    @property
    def is_error(self) -> bool:
        return self.display == ERROR_TEXT

    def press(self, key: str) -> str:
        """Обрабатывает одну клавишу и возвращает новый текст дисплея."""
        if self.is_error and key not in DIGITS and key not in (".", "C", "CE"):
            return self.display  # после ошибки ждём новое число или сброс

        try:
            if key in DIGITS:
                self._input_digit(key)
            elif key == ".":
                self._input_point()
            elif key == "C":
                self._clear_all()
            elif key == "CE":
                self._clear_entry()
            elif key == "←":
                self._backspace()
            elif key == "±":
                self._negate()
            elif key == "%":
                self._show_result(self._accumulator * self._current_value() / 100)
                self._operand_entered = True
            elif key in UNARY_OPERATIONS:
                self._show_result(UNARY_OPERATIONS[key](self._current_value()))
                self._operand_entered = True
            elif key in BINARY_OPERATIONS:
                self._press_operation(key)
            elif key == "=":
                self._calculate_pending()
                self._pending_operation = None
            else:
                raise ValueError(f"Неизвестная клавиша: {key!r}")
        except CalcError:
            self._show_error()
        return self.display

    # --- Ввод числа ---------------------------------------------------------

    def _input_digit(self, digit: str) -> None:
        if self._start_new_number or self.display == "0":
            self.display = digit
            self._start_new_number = False
        elif self._digit_count() < MAX_INPUT_DIGITS:
            self.display += digit
        self._operand_entered = True

    def _input_point(self) -> None:
        if self._start_new_number:
            self.display = "0."
            self._start_new_number = False
        elif "." not in self.display:
            self.display += "."
        self._operand_entered = True

    def _backspace(self) -> None:
        if self._start_new_number:
            return  # результат вычисления не редактируется, только введённое число
        self.display = self.display[:-1]
        if self.display in ("", "-"):
            self.display = "0"

    def _negate(self) -> None:
        if self.display == "0":
            return
        if self.display.startswith("-"):
            self.display = self.display[1:]
        else:
            self.display = "-" + self.display
        self._operand_entered = True

    def _digit_count(self) -> int:
        return sum(char.isdigit() for char in self.display)

    # --- Сброс ------------------------------------------------------------

    def _clear_all(self) -> None:
        self.display = "0"
        self._accumulator = 0.0  # результат предыдущих действий
        self._pending_operation: str | None = None  # операция, которая ждёт второе число
        self._start_new_number = True  # следующая цифра начинает новое число
        self._operand_entered = False  # после операции уже введено второе число

    def _clear_entry(self) -> None:
        self.display = "0"
        self._start_new_number = True

    # --- Вычисления -------------------------------------------------------

    def _current_value(self) -> float:
        return float(self.display)

    def _press_operation(self, operation: str) -> None:
        if self._pending_operation is not None and not self._operand_entered:
            # Нажали две операции подряд ("5 + *"): просто меняем операцию.
            self._pending_operation = operation
            return
        self._calculate_pending()
        self._pending_operation = operation
        self._operand_entered = False

    def _calculate_pending(self) -> None:
        value = self._current_value()
        if self._pending_operation is not None:
            value = BINARY_OPERATIONS[self._pending_operation](self._accumulator, value)
        self._show_result(value)
        self._accumulator = value

    def _show_result(self, value: float) -> None:
        self.display = format_number(value)
        self._start_new_number = True

    def _show_error(self) -> None:
        self._clear_all()
        self.display = ERROR_TEXT
