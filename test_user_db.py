import pytest
from user_db import UserDB


@pytest.fixture
def empty_userdb():
    return UserDB()


def test_create_user(empty_userdb):
    test_username = 'jimbo'
    username, passtoken = empty_userdb.create_user(test_username)
    assert username == test_username
    assert passtoken != empty_userdb._accounts[username]


def test_check_login(empty_userdb):
    test_username = 'rdwrer'
    username, passtoken = empty_userdb.create_user(test_username)
    assert username == test_username
    assert passtoken != empty_userdb._accounts[username]
    assert empty_userdb.is_valid(
        test_username, 'baddpasstoken') is False
    assert empty_userdb.is_valid(
        test_username, passtoken) is True


if __name__ == '__main__':
    pytest.main()
