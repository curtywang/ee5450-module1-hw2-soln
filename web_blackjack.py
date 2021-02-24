import uvicorn
from typing import Optional
from fastapi import FastAPI, HTTPException, Path, status, Query
from blackjack_db import AsyncBlackjackGameDB, Blackjack
from user_db import UserDB


USER_DB = UserDB()
BLACKJACK_DB = AsyncBlackjackGameDB(USER_DB)
app = FastAPI(
    title="Blackjack Server",
    description="Implementation of a simultaneous multi-game Blackjack server by[Your name here]."
)


async def get_game(game_id: str) -> Blackjack:
    """
    Get a game from the blackjack game database, otherwise raise a 404.

    :param game_id: the uuid in str of the game to retrieve
    """
    the_game = await BLACKJACK_DB.get_game(game_id)
    if the_game is None:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found.")
    return the_game


@app.get('/')
async def home():
    return {"message": "Welcome to Blackjack!"}


@app.get('/game/create/{num_players}', status_code=status.HTTP_201_CREATED)
async def create_game(num_players: int = Path(..., gt=0, description='the number of players'),
                      num_decks: Optional[int] = Query(2, description='the number of decks to use')):
    new_uuid, new_term_pass, game_owner = await BLACKJACK_DB.add_game(num_players=num_players, num_decks=num_decks)
    return {'success': True, 'game_id': new_uuid, 'termination_password': new_term_pass}


@app.post('/game/{game_id}/initialize')
async def init_game(game_id: str = Path(..., description='the unique game id')):
    the_game = await get_game(game_id)
    the_game.initial_deal()
    dealer_stack, player_stacks = the_game.get_stacks()
    return {'success': True, 'dealer_stack': dealer_stack, 'player_stacks': player_stacks}


@app.post('/game/{game_id}/player/{player_idx}/hit')
async def player_hit(game_id: str = Path(..., description='the unique game id'),
                     player_idx: int = Path(..., description='the player index (zero-indexed)')):
    the_game = await get_game(game_id)
    drawn_card = the_game.player_draw(player_idx)
    return {'player': player_idx,
            'drawn_card': str(drawn_card),
            'player_stack': the_game.get_stacks()[1][player_idx]}


@app.get('/game/{game_id}/player/{player_idx}/stack')
async def player_stack(game_id: str = Path(..., description='the unique game id'),
                       player_idx: int = Path(..., description='the player index (zero-indexed)')):
    the_game = await get_game(game_id)
    return {'player': player_idx,
            'player_stack': the_game.get_stacks()[1][player_idx]}


@app.post('/game/{game_id}/dealer/play')
async def dealer_play(game_id: str = Path(..., description='the unique game id')):
    the_game = await get_game(game_id)
    dealer_stop = the_game.dealer_draw()
    while dealer_stop is False:
        dealer_stop = the_game.dealer_draw()
    return {'player': 'dealer',
            'player_stack': the_game.get_stacks()[0]}


@app.get('/game/{game_id}/winners')
async def get_winners(game_id: str = Path(..., description='the unique game id')):
    the_game = await get_game(game_id)
    winner_list = the_game.compute_winners()
    return {'game_id': game_id,
            'winners': winner_list}


@app.post('/game/{game_id}/terminate')
async def delete_game(game_id: str = Path(..., description='the unique game id'),
                      password: str = Query(..., description='the termination password')):
    the_game = await BLACKJACK_DB.del_game(game_id, password)
    if the_game is False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Game not found.")
    return {'success': True, 'deleted_id': game_id}


if __name__ == '__main__':
    # running from main instead of terminal allows for debugger
    # TODO: modify the below to add HTTPS (SSL/TLS) support
    uvicorn.run('web_blackjack:app', port=8000, log_level='info', reload=True)
