"""Calc v0.4 — калькулятор с графическим интерфейсом на tkinter.

Запуск: python calc_app.py
Вся логика вычислений находится в calculator.py, здесь только окно и клавиатура.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox

from calculator import Calculator

TITLE = "Смирнов Calc v0.4"
WINDOW_SIZE = "320x500"

BUTTON_ROWS = (
    ("%", "CE", "C", "←"),
    ("1/x", "x²", "√", "÷"),
    ("7", "8", "9", "*"),
    ("4", "5", "6", "-"),
    ("1", "2", "3", "+"),
    ("±", "0", ".", "="),
)

# Порядок обхода кнопок клавишей Tab: сначала цифры, потом операции.
TAB_ORDER = (
    *"0123456789",
    *("+", "-", "*", "÷", "=", "."),
    *("%", "CE", "C", "←", "1/x", "x²", "√", "±"),
)

# Клавиши, которые узнаём по названию (keysym), и символы, которые узнаём по тексту.
KEYSYM_TO_BUTTON = {
    "Return": "=",
    "KP_Enter": "=",
    "BackSpace": "←",
    "Escape": "C",
    "Delete": "CE",
}
CHAR_TO_BUTTON = {
    **{digit: digit for digit in "0123456789"},
    ".": ".",
    ",": ".",
    "+": "+",
    "-": "-",
    "*": "*",
    "/": "÷",
    "=": "=",
    "%": "%",
}

HIGHLIGHT_COLOR = "#cde4ff"
MIN_DISPLAY_FONT = 10
MIN_BUTTON_FONT = 8

ABOUT_TEXT = (
    "Клавиатура:\n"
    "  цифры, + - * /, Enter — равно\n"
    "  Backspace — стереть цифру, Delete — CE, Esc — C\n"
    "  Tab / Shift+Tab — выбрать кнопку, пробел — нажать её\n\n"
    "(С) Смирнов Л.Д.\n"
    "Спасибо: Елене Викторовне и Денису Владимировичу за воспитание, "
    "бесконечную любовь и поддержку ❤"
)


class CalculatorApp:
    """Окно калькулятора: дисплей, кнопки и обработка клавиатуры."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.calculator = Calculator()
        self.display_text = tk.StringVar(value=self.calculator.display)
        self.display_font = tkfont.Font(family="Arial", size=36, weight="bold")
        self.button_font = tkfont.Font(family="Arial", size=15)
        self.buttons: dict[str, tk.Button] = {}
        self.highlighted: int | None = None  # индекс выбранной кнопки в TAB_ORDER

        root.title(TITLE)
        root.geometry(WINDOW_SIZE)
        self._build_display()
        self._build_buttons()
        self._bind_keys()
        root.focus_force()

    # --- Построение окна --------------------------------------------------

    def _build_display(self) -> None:
        # width=1: ширину задаёт сетка, а не размер шрифта
        self.display = tk.Entry(
            self.root,
            textvariable=self.display_text,
            font=self.display_font,
            width=1,
            justify="right",
            state="readonly",
            cursor="arrow",
            relief="sunken",
            bd=2,
        )
        self.display.grid(row=0, column=0, columnspan=4, padx=4, pady=4, sticky="nsew")

    def _build_buttons(self) -> None:
        for row, labels in enumerate(BUTTON_ROWS, start=1):
            for column, label in enumerate(labels):
                button = tk.Button(
                    self.root,
                    text=label,
                    font=self.button_font,
                    relief="raised",
                    takefocus=False,
                    command=lambda key=label: self.press(key),
                )
                button.grid(row=row, column=column, padx=2, pady=2, sticky="nsew")
                self.buttons[label] = button
        self.default_button_color = self.buttons["0"].cget("background")

        for column in range(4):
            self.root.grid_columnconfigure(column, weight=1)
        self.root.grid_rowconfigure(0, weight=3)
        for row in range(1, len(BUTTON_ROWS) + 1):
            self.root.grid_rowconfigure(row, weight=1)

    def _bind_keys(self) -> None:
        self.root.bind("<Key>", self._on_key)
        self.root.bind("<Tab>", lambda event: self._move_highlight(+1))
        self.root.bind("<Shift-Tab>", lambda event: self._move_highlight(-1))
        try:  # в Linux Shift+Tab приходит как отдельная клавиша
            self.root.bind("<ISO_Left_Tab>", lambda event: self._move_highlight(-1))
        except tk.TclError:
            pass
        self.root.bind("<space>", lambda event: self._press_highlighted())
        self.root.bind("<F1>", lambda event: messagebox.showinfo("Инфо", ABOUT_TEXT))
        self.root.bind("<Configure>", self._on_resize)

    # --- Действия ---------------------------------------------------------

    def press(self, key: str) -> None:
        self.display_text.set(self.calculator.press(key))
        self._fit_display_font()
        self.root.focus_set()

    def _on_key(self, event: tk.Event) -> None:
        # Shift, Ctrl, стрелки и т. п. не дают символа и сюда не подходят.
        key = KEYSYM_TO_BUTTON.get(event.keysym, CHAR_TO_BUTTON.get(event.char))
        if key is not None:
            self.press(key)

    def _move_highlight(self, step: int) -> str:
        if self.highlighted is None:
            self.highlighted = 0 if step > 0 else len(TAB_ORDER) - 1
        else:
            self._set_highlight(TAB_ORDER[self.highlighted], on=False)
            self.highlighted = (self.highlighted + step) % len(TAB_ORDER)
        self._set_highlight(TAB_ORDER[self.highlighted], on=True)
        return "break"  # не отдаём Tab стандартному переключению фокуса

    def _set_highlight(self, key: str, on: bool) -> None:
        self.buttons[key].config(
            relief="sunken" if on else "raised",
            background=HIGHLIGHT_COLOR if on else self.default_button_color,
        )

    def _press_highlighted(self) -> None:
        if self.highlighted is not None:
            self.press(TAB_ORDER[self.highlighted])

    # --- Размер шрифта ----------------------------------------------------

    def _on_resize(self, event: tk.Event) -> None:
        if event.widget is not self.root:
            return  # <Configure> приходит и от каждой кнопки, нужны только изменения окна
        self.button_font.configure(size=max(MIN_BUTTON_FONT, event.height // 22))
        self._fit_display_font()

    def _fit_display_font(self) -> None:
        """Подбирает самый крупный шрифт, при котором число помещается на дисплее целиком."""
        available_width = self.display.winfo_width() - 16
        text = self.display_text.get()
        size = max(MIN_DISPLAY_FONT, self.root.winfo_height() // 7)
        self.display_font.configure(size=size)
        while size > MIN_DISPLAY_FONT and self.display_font.measure(text) > available_width:
            size -= 2
            self.display_font.configure(size=size)


def main() -> None:
    root = tk.Tk()
    CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
