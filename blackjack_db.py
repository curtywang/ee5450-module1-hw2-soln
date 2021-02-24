from uuid import uuid4
from typing import List, Tuple, Dict, Union
from blackjack.blackjack import Blackjack
from user_db import UserDB
from dataclasses import dataclass
from fastapi import HTTPException, status
import asyncio


@dataclass
class BlackjackGameInfo:
    num_players: int
    owner: str
    players: List[str]
    termination_password: str


class AsyncBlackjackGameDB(object):
    def __init__(self, user_db: UserDB):
        self._current_games: Dict[str, Blackjack] = {}
        self._current_games_info: Dict[str, BlackjackGameInfo] = {}
        self._QUERY_TIME: float = 0.05
        self._user_db = user_db  # pointer to the Web API's UserDB

    async def add_game(self, num_players: int, owner: str,
                       num_decks: int = 2) -> Tuple[str, str, str]:
        """
        Asks the database to create a new game.

        :param num_players: number of players
        :param owner: username of the owner of the game
        :param num_decks: number of decks to use, default 2
        :return: the UUID (universally-unique ID) of the game, termination password, and owner username
        """
        await asyncio.sleep(self._QUERY_TIME)  # simulate query time
        game_uuid = str(uuid4())
        game_term_password = str(uuid4())
        self._current_games[game_uuid] = Blackjack(num_decks, num_players)
        self._current_games_info[game_uuid] = BlackjackGameInfo(
            num_players,
            owner,
            list(),
            game_term_password)
        return game_uuid, game_term_password, owner

    async def list_games(self) -> List[Tuple[str, int]]:
        """
        Asks the database for a list of all active games.

        :return: list of (game_id, number of players in game)
        """
        await asyncio.sleep(self._QUERY_TIME)  # simulate query time
        return [(game_id, game.num_players) for game_id, game in self._current_games.items()]

    async def get_game(self, game_id: str) -> Union[Blackjack, None]:
        """
        Asks the database for a pointer to a specific game.

        :param game_id: the UUID of the specific game
        :return: None if the game was not found, otherwise pointer to the Blackjack object
        """
        await asyncio.sleep(self._QUERY_TIME)  # simulate query time
        return self._current_games.get(game_id, None)

    async def del_game(self, game_id: str, term_pass: str, attempter: str) -> bool:
        """
        Asks the database to terminate a specific game.

        :param game_id: the UUID of the specific game
        :param term_pass: the termination password for the game
        :param attempter: the username of the person attempting the delete
        :return: False or exception if not found, True if success
        """
        try:
            await asyncio.sleep(self._QUERY_TIME)  # simulate query time
            if self._current_games_info[game_id].termination_password == term_pass \
                    and self._current_games_info[game_id].owner == attempter:
                del self._current_games[game_id]
                return True
            else:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not authorized")
        except KeyError:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "game_id not found")
