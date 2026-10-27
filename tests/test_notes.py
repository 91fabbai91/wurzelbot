from unittest.mock import MagicMock
from notes import Notes


def test_notes_init_and_parsing(mock_http, sample_notes_html):
    mock_http.get_notes.return_value = sample_notes_html
    notes_obj = Notes(mock_http)

    assert notes_obj.get_min_stock() == 25
    assert notes_obj.get_min_stock("Salat") == 100
    assert notes_obj.get_min_stock("Möhre") == 50
    assert notes_obj.get_min_stock("Unbekannt") == 0


def test_notes_get_notes_text(mock_http, sample_notes_html):
    mock_http.get_notes.return_value = sample_notes_html
    notes_obj = Notes(mock_http)
    content = notes_obj.get_notes()
    assert "minStock: 25" in content
    assert "minStock(Salat): 100" in content


def test_notes_empty_string(mock_http):
    mock_http.get_notes.return_value = ""
    notes_obj = Notes(mock_http)
    assert notes_obj.get_notes() == ""
    assert notes_obj.get_min_stock() == 0


def test_notes_empty_textarea(mock_http):
    html_without_text = "<html><body><form><div><textarea id='notiztext'></textarea></div></form></body></html>"
    mock_http.get_notes.return_value = html_without_text
    notes_obj = Notes(mock_http)
    assert notes_obj.get_notes() is None
    assert notes_obj.get_min_stock() == 0
    assert notes_obj.get_min_stock("Salat") == 0


def test_notes_windows_line_endings(mock_http):
    html_crlf = (
        "<html><body><form><div><textarea id='notiztext'>\r\n"
        "minStock: 10\r\n"
        "minStock(Gurke): 30\r\n"
        "</textarea></div></form></body></html>"
    )
    mock_http.get_notes.return_value = html_crlf
    notes_obj = Notes(mock_http)
    assert notes_obj.get_min_stock() == 10
    assert notes_obj.get_min_stock("Gurke") == 30

