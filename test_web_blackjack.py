import pytest
from fastapi.testclient import TestClient
from requests.auth import HTTPBasicAuth
from web_blackjack import app

TEST_USER = 'testah'
TEST_USER2 = 'playah'


@pytest.fixture
def base_client():
    return TestClient(app)


def test_create_user(base_client):
    response = base_client.post(f'/user/create?username={TEST_USER}')
    resp = response.json()
    assert 'username' in resp
    assert 'password' in resp


@pytest.fixture
def base_user(base_client):
    response = base_client.post(f'/user/create?username={TEST_USER}')
    resp = response.json()
    tester_auth = HTTPBasicAuth(username=resp['username'], password=resp['password'])
    return tester_auth


@pytest.fixture
def base_user2(base_client):
    response = base_client.post(f'/user/create?username={TEST_USER2}')
    resp = response.json()
    tester_auth = HTTPBasicAuth(username=resp['username'], password=resp['password'])
    return tester_auth


def test_home(base_client):
    response = base_client.get('/')
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Blackjack!"}


def test_create(base_client, base_user):
    response = base_client.get('/game/create/1', auth=base_user)
    response_json = response.json()
    assert response.status_code == 201
    assert response_json['success'] is True
    assert len(response_json['game_id']) == 36
    assert len(response_json['termination_password']) == 36


@pytest.fixture
def get_empty_game(base_client, base_user):
    resp = base_client.get('/game/create/1', auth=base_user)
    resp_json = resp.json()
    return resp_json


@pytest.fixture
def get_base_game(base_client, base_user, base_user2):
    response = base_client.get('/game/create/2', auth=base_user)
    game_resp = response.json()
    return game_resp


def test_add_player(get_base_game, base_user, base_user2, base_client):
    game_id = get_base_game['game_id']
    response = base_client.post(f'/game/{game_id}/add_player?username={TEST_USER2}', auth=base_user)
    resp = response.json()
    assert resp['game_id'] == game_id
    assert resp['player_username'] == base_user2.username
    assert 'player_idx' in resp


@pytest.fixture
def get_game(get_base_game, base_client, base_user, base_user2):
    game_id = get_base_game['game_id']
    response = base_client.post(f'/game/{game_id}/add_player?username={TEST_USER2}', auth=base_user)
    player_resp = response.json()
    return player_resp


def test_initialize(get_game, base_user, base_user2, base_client):
    game_id = get_game['game_id']
    resp = base_client.post(f'/game/{game_id}/initialize', auth=base_user)
    resp_json = resp.json()
    assert resp_json['success'] is True
    assert len(resp_json['dealer_stack']) == 2
    assert len(resp_json['player_stacks']) == 2
    assert len(resp_json['player_stacks'][0]) == 2
    assert len(resp_json['player_stacks'][1]) == 2


@pytest.fixture
def get_init_game(get_game, base_user, base_user2, base_client):
    resp = base_client.post(f'/game/{get_game["game_id"]}/initialize', auth=base_user)
    return get_game


def test_player_hit(get_init_game, base_user, base_user2, base_client):
    game_id = get_init_game['game_id']
    resp = base_client.post(f'/game/{game_id}/player/0/hit', auth=base_user)
    resp_json = resp.json()
    assert int(resp_json['player']) == 0
    assert len(resp_json['player_stack']) == 3


def test_player_hit_unauthorized(get_init_game, base_user, base_user2, base_client):
    game_id = get_init_game['game_id']
    resp = base_client.post(f'/game/{game_id}/player/1/hit', auth=base_user)
    assert resp.status_code == 401


def test_player_stack(get_init_game, base_user, base_client):
    game_id = get_init_game['game_id']
    resp = base_client.get(f'/game/{game_id}/player/0/stack', auth=base_user)
    resp_json = resp.json()
    assert int(resp_json['player']) == 0
    assert len(resp_json['player_stack']) == 2


def test_player_stack_unauthorized(get_init_game, base_user, base_client):
    game_id = get_init_game['game_id']
    resp = base_client.get(f'/game/{game_id}/player/1/stack', auth=base_user)
    assert resp.status_code == 401


def test_dealer_play(get_init_game, base_user, base_client):
    game_id = get_init_game['game_id']
    resp = base_client.post(f'/game/{game_id}/dealer/play', auth=base_user)
    resp_json = resp.json()
    assert resp_json['player'] == 'dealer'
    assert len(resp_json['player_stack']) >= 2


@pytest.fixture
def get_dealer_won_game(get_init_game, base_user, base_client):
    resp = base_client.post(f'/game/{get_init_game["game_id"]}/dealer/play', auth=base_user)
    return get_init_game


def test_get_winners(get_dealer_won_game, base_client):
    game_id = get_dealer_won_game['game_id']
    resp = base_client.get(f'/game/{game_id}/winners')
    resp_json = resp.json()
    assert resp_json['game_id'] == game_id
    assert len(resp_json['winners']) >= 1
    assert resp_json['winners'][0] in ['NONE', 'DEALER', 'PLAYER']


def test_delete_game(get_dealer_won_game, base_user, base_user2, get_base_game, base_client):
    game_id = get_dealer_won_game['game_id']
    term_pass = get_base_game['termination_password']
    resp = base_client.post(f'/game/{game_id}/terminate', auth=base_user)
    assert resp.status_code == 422
    resp = base_client.post(f'/game/{game_id}/terminate?password=fail', auth=base_user)
    assert resp.status_code == 401
    resp = base_client.post(f'/game/{game_id}/terminate?password={term_pass}', auth=base_user2)
    assert resp.status_code == 401
    resp = base_client.post(f'/game/{game_id}/terminate?password={term_pass}', auth=base_user)
    resp_json = resp.json()
    assert resp_json['success'] is True
    assert resp_json['deleted_id'] == game_id


if __name__ == '__main__':
    pytest.main()
