from milo.text import normalize_text


def test_lowercases_text() -> None:
    assert normalize_text("Combustivel ENTREGAS 30") == "combustivel entregas 30"


def test_collapses_repeated_spaces() -> None:
    assert normalize_text("uber    27") == "uber 27"


def test_strips_leading_and_trailing_whitespace() -> None:
    assert normalize_text("   entregas 160 \n") == "entregas 160"


def test_empty_text_stays_empty() -> None:
    assert normalize_text("   ") == ""
