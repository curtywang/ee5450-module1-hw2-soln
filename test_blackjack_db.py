from blackjack_db import AsyncBlackjackGameDB
from user_db import UserDB
import pytest
import asyncio

TEST_USER = 'tester'


@pytest.fixture
def base_user_db():
    the_user_db = UserDB()
    username, passtoken = the_user_db.create_user(TEST_USER)
    return the_user_db, username, passtoken


@pytest.fixture
def base_game_db(base_user_db):
    return AsyncBlackjackGameDB(base_user_db[0])


@pytest.mark.asyncio
async def test_add_game(base_game_db):
    game_uuid, game_term_password, game_owner = await base_game_db.add_game(1, TEST_USER, 2)
    assert len(game_uuid) == 36
    assert len(game_term_password) == 36
    assert game_owner == TEST_USER
    assert base_game_db._current_games_info[game_uuid].termination_password == game_term_password
    assert base_game_db._current_games[game_uuid].num_players == 1


@pytest.fixture
async def single_game_db(base_game_db):
    game_uuid, game_term_password, game_owner = await base_game_db.add_game(1, TEST_USER)
    return base_game_db, game_uuid, game_term_password, game_owner


@pytest.mark.asyncio
async def test_list_games(single_game_db):
    list_of_games = await single_game_db[0].list_games()
    assert len(list_of_games) == 1


@pytest.mark.asyncio
async def test_get_game(single_game_db):
    assert await single_game_db[0].get_game(single_game_db[1]) is not None
    assert await single_game_db[0].get_game(single_game_db[1]) == single_game_db[0]._current_games[single_game_db[1]]


@pytest.mark.asyncio
async def test_del_game(single_game_db):
    assert await single_game_db[0].del_game(single_game_db[1], 'bad_password', 'baduser') is False
    assert await single_game_db[0].del_game(single_game_db[1], 'bad_password', TEST_USER) is False
    assert await single_game_db[0].del_game(single_game_db[1], single_game_db[2], TEST_USER) is True


if __name__ == '__main__':
    pytest.main()
