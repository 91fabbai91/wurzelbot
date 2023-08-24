import parsing_utils
import pytest


def test_generate_json_content_and_check_for_ok():
    content = """{"status":"ok"}"""
    jcontent = parsing_utils.generate_json_content_and_check_for_ok(content)
    assert jcontent["status"] == "ok"


def test_generate_json_content_and_check_not_ok():
    with pytest.raises(parsing_utils.JSONError, match="JSON not ok"):
        content = """{"status":"nok"}"""
        jcontent = parsing_utils.generate_json_content_and_check_for_ok(content)


def test_generate_json_content_and_check_for_success():
    content = """{"success":1}"""
    jcontent = parsing_utils.generate_json_content_and_check_for_success(content)
    assert jcontent["success"] == 1


def test_generate_json_content_and_check_for_not_success():
    with pytest.raises(parsing_utils.JSONError, match="JSON not successful"):
        content = """{"success":0}"""
        jcontent = parsing_utils.generate_json_content_and_check_for_success(content)
