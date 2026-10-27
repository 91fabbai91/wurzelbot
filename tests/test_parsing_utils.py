import pytest

import parsing_utils


def test_generate_json_content_and_check_for_ok():
    content = """{"status":"ok", "data": 123}"""
    jcontent = parsing_utils.generate_json_content_and_check_for_ok(content)
    assert jcontent["status"] == "ok"
    assert jcontent["data"] == 123


def test_generate_json_content_and_check_not_ok():
    with pytest.raises(parsing_utils.JSONError, match="JSON not ok"):
        content = """{"status":"nok", "message": "Invalid credentials"}"""
        parsing_utils.generate_json_content_and_check_for_ok(content)

    with pytest.raises(parsing_utils.JSONError, match="JSON not ok"):
        content = """{"status":"error"}"""
        parsing_utils.generate_json_content_and_check_for_ok(content)


def test_generate_json_content_and_check_for_success():
    content = """{"success":1, "data": "yes"}"""
    jcontent = parsing_utils.generate_json_content_and_check_for_success(content)
    assert jcontent["success"] == 1


def test_generate_json_content_and_check_for_not_success():
    with pytest.raises(parsing_utils.JSONError, match="JSON not successful"):
        content = """{"success":0, "errorMsg": "Failed to buy"}"""
        parsing_utils.generate_json_content_and_check_for_success(content)

    with pytest.raises(parsing_utils.JSONError, match="JSON not successful"):
        content = """{"status": "failure"}"""
        parsing_utils.generate_json_content_and_check_for_success(content)


def test_generate_json_content_and_check_for_status_success():
    content = """{"status":"SUCCESS", "value": 42}"""
    jcontent = parsing_utils.generate_json_content_and_check_for_status_success(content)
    assert jcontent["status"] == "SUCCESS"
    assert jcontent["value"] == 42


def test_generate_json_content_and_check_for_status_not_success():
    with pytest.raises(parsing_utils.JSONError, match="JSON not successful"):
        content = """{"status":"FAILED"}"""
        parsing_utils.generate_json_content_and_check_for_status_success(content)


def test_generate_yaml_content_and_check_status_for_ok():
    yaml_content = "status: ok"
    # Doesn't raise when status == "ok"
    parsing_utils.generate_yaml_content_and_check_status_for_ok(yaml_content)

    with pytest.raises(parsing_utils.YAMLError, match="YAMLError"):
        parsing_utils.generate_yaml_content_and_check_status_for_ok("status: nok")


def test_generate_yaml_content_and_check_for_success():
    yaml_content = "success: 1"
    # Doesn't raise when success == 1
    parsing_utils.generate_yaml_content_and_check_for_success(yaml_content)

    with pytest.raises(parsing_utils.YAMLError, match="YAML Error"):
        parsing_utils.generate_yaml_content_and_check_for_success("success: 0")


def test_custom_exceptions():
    err_json = parsing_utils.JSONError("json issue")
    assert str(err_json) == "'json issue'"

    err_http = parsing_utils.HTTPStateError("http code 500")
    assert str(err_http) == "'http code 500'"

    err_yaml = parsing_utils.YAMLError("yaml issue")
    assert str(err_yaml) == "'yaml issue'"
