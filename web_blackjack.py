import uvicorn
from typing import Optional, Tuple
from fastapi import FastAPI, HTTPException, Path, status, Query, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from blackjack_db import AsyncBlackjackGameDB, Blackjack, BlackjackGameInfo
from user_db import UserDB


USER_DB = UserDB()
BLACKJACK_DB = AsyncBlackjackGameDB(USER_DB)
app = FastAPI(
    title="Blackjack Server",
    description="Implementation of a simultaneous multi-game Blackjack server by[Your name here]."
)
security = HTTPBasic()


async def get_game(game_id: str) -> Tuple[Blackjack, BlackjackGameInfo]:
    """
    Get a game from the blackjack game database, otherwise raise a 404.

    :param game_id: the uuid in str of the game to retrieve
    :return: (the blackjack game, the game's info)
    """
    the_game, the_game_info = await BLACKJACK_DB.get_game(game_id)
    if the_game is None:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found.")
    return the_game, the_game_info


async def check_user(username: str, password: str) -> bool:
    """
    Check if a user is valid, otherwise raise the HTTPException 401 Unauthorized.

    :param username: the attempted username
    :param password: the attempted password
    :return: True if valid, otherwise raises exception
    """
    if USER_DB.is_valid(username, password):
        return True
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found with those credentials")


@app.get('/')
async def home():
    return {"message": "Welcome to Blackjack!"}


@app.get('/game/create/{num_players}', status_code=status.HTTP_201_CREATED)
async def create_game(num_players: int = Path(..., gt=0, description='the number of players'),
                      num_decks: Optional[int] = Query(2, description='the number of decks to use'),
                      credentials: HTTPBasicCredentials = Depends(security)):
    await check_user(credentials.username, credentials.password)
    new_uuid, new_term_pass, game_owner = await BLACKJACK_DB.add_game(num_players=num_players,
                                                                      owner=credentials.username,
                                                                      num_decks=num_decks)
    return {'success': True, 'game_id': new_uuid, 'termination_password': new_term_pass}


@app.post('/user/create', status_code=status.HTTP_201_CREATED)
async def create_user(username: str = Query(..., description='the number of decks to use')):
    username, password = USER_DB.create_user(username)
    return {'success': True, 'username': username, 'password': password}


@app.post('/game/{game_id}/initialize')
async def init_game(game_id: str = Path(..., description='the unique game id'),
                    credentials: HTTPBasicCredentials = Depends(security)):
    await check_user(credentials.username, credentials.password)
    the_game, the_game_info = await get_game(game_id)
    if the_game_info.owner != credentials.username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not owner of game")
    the_game.initial_deal()
    dealer_stack, player_stacks = the_game.get_stacks()
    return {'success': True, 'dealer_stack': dealer_stack, 'player_stacks': player_stacks}


@app.post('/game/{game_id}/add_player')
async def add_player_to_game(game_id: str = Path(..., description='the unique game id'),
                             username: str = Query(..., description='the user to add as a player'),
                             credentials: HTTPBasicCredentials = Depends(security)):
    await check_user(credentials.username, credentials.password)
    the_game, the_game_info = await get_game(game_id)
    if the_game_info.owner != credentials.username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not owner of game")
    player_idx = await BLACKJACK_DB.add_player(game_id, username)
    return {'success': True, 'game_id': game_id, 'player_username': username, 'player_idx': player_idx}


@app.post('/game/{game_id}/player/{player_idx}/hit')
async def player_hit(game_id: str = Path(..., description='the unique game id'),
                     player_idx: int = Path(..., description='the player index (zero-indexed)'),
                     credentials: HTTPBasicCredentials = Depends(security)):
    await check_user(credentials.username, credentials.password)
    the_game, the_game_info = await get_game(game_id)
    if credentials.username != the_game_info.players[player_idx]:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"not player at index {player_idx}")
    drawn_card = the_game.player_draw(player_idx)
    return {'player': player_idx,
            'drawn_card': str(drawn_card),
            'player_stack': the_game.get_stacks()[1][player_idx]}


@app.post('/game/{game_id}/get_player_idx')
async def get_player_idx(game_id: str = Path(..., description='the unique game id'),
                         username: str = Path(..., description='the username of the player'),
                         credentials: HTTPBasicCredentials = Depends(security)):
    await check_user(credentials.username, credentials.password)
    the_game, the_game_info = await get_game(game_id)
    if credentials.username not in the_game_info.players:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"not player in game {game_id}")
    try:
        player_idx = the_game_info.players.index(username)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"player {username} not in game {game_id}")
    return {'success': True, 'game_id': game_id, 'player_username': username, 'player_idx': player_idx}


@app.get('/game/{game_id}/player/{player_idx}/stack')
async def player_stack(game_id: str = Path(..., description='the unique game id'),
                       player_idx: int = Path(..., description='the player index (zero-indexed)'),
                       credentials: HTTPBasicCredentials = Depends(security)):
    await check_user(credentials.username, credentials.password)
    the_game, the_game_info = await get_game(game_id)
    if credentials.username != the_game_info.players[player_idx]:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"not the player at {player_idx}")
    return {'player': player_idx, 'player_stack': the_game.get_stacks()[1][player_idx]}


@app.post('/game/{game_id}/dealer/play')
async def dealer_play(game_id: str = Path(..., description='the unique game id'),
                      credentials: HTTPBasicCredentials = Depends(security)):
    await check_user(credentials.username, credentials.password)
    the_game, the_game_info = await get_game(game_id)
    if the_game_info.owner != credentials.username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not owner of game")
    dealer_stop = the_game.dealer_draw()
    while dealer_stop is False:
        dealer_stop = the_game.dealer_draw()
    return {'player': 'dealer',
            'player_stack': the_game.get_stacks()[0]}


@app.get('/game/{game_id}/winners')
async def get_winners(game_id: str = Path(..., description='the unique game id')):
    the_game, _ = await get_game(game_id)
    winner_list = the_game.compute_winners()
    return {'game_id': game_id,
            'winners': winner_list}


@app.post('/game/{game_id}/terminate')
async def delete_game(game_id: str = Path(..., description='the unique game id'),
                      password: str = Query(..., description='the termination password'),
                      credentials: HTTPBasicCredentials = Depends(security)):
    await check_user(credentials.username, credentials.password)
    the_game, the_game_info = await get_game(game_id)
    if the_game_info.owner != credentials.username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not owner of game")
    the_game = await BLACKJACK_DB.del_game(game_id, password, credentials.username)
    if the_game is False:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found.")
    return {'success': True, 'deleted_id': game_id}


if __name__ == '__main__':
    # running from main instead of terminal allows for debugger
    uvicorn.run('web_blackjack:app', port=8000, log_level='info', reload=True,
                ssl_keyfile='key/localhost+2-key.pem', ssl_certfile='key/localhost+2.pem')
