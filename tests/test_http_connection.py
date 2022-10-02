from http_connection import HTTPConnection


def test_singleton():
    assert HTTPConnection() == HTTPConnection()
