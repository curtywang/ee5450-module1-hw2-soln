# EE 5450 Module 1, Homework 2
Securing and Authenticating your FastAPI-based Web API for Multi-user, Multi-game Blackjack

# Introduction

In this assignment, you'll be making adding HTTPS/TLS support and user authentication (account creation/login) to your 
Blackjack server Web API.  To facilitate this, I've created a folder named `keys` where you should put your self-signed 
public/private keys made with [mkcert](https://github.com/FiloSottile/mkcert/releases), run on the Miniforge Prompt.  The public certificate 
should be named `public.pem` and the private key should be named `private.pem`.  Generally, you should not add these to
Git, so make sure you do not accidentally add them as part of the changes (the gitignore should prevent them from being) 
added.  Once you have added these, add the appropriate commands to the `uvicorn.run()` call at the end of 
`web_blackjack.py` so that uvicorn will run with HTTPS.  Note that your URLs will then be prefixed by `https://` 
instead of `http://`, since you are using the HTTPS protocol now. 

I've also made a new Python module named `user_db.py`, which will guide you through writing authentication middleware 
for your Web API.  Then, when you are done writing the authentication middleware, you will add usage of your 
authentication middleware to your Web API and Blackjack game database.

To get started, make sure all packages in `requirements.txt` are installed: `conda install --file requirements.txt`

Then, open up `user_db.py` and `test_user_db.py`.  The `UserDB` class consists of methods to create accounts and perform
authentication checks.  I have modified `blackjack_db.py` so that the `AsyncBlackjackGameDB` class contains 
interfaces for adding a game owner through a `UserDB` object.  Finally, we will modify `web_blackjack.py` 
with the paths below so that we can create user accounts and all game calls marked with `AUTH REQUIRED` are 
authenticated and restricted properly.

To save time, we will not be creating sessions (logging whether a user is logged in or not).  Instead, we will just
request that every API call be authenticated; thus, you will be passing HTTP Basic authentication headers, which 
you can test using Insomnia and TestClient.  Do NOT pass authentication information via the URL paths -- that is 
a surefire way to get your authentication information sniffed out!  All failed authentications should return 401.

The [FastAPI HTTP Basic Auth](https://fastapi.tiangolo.com/advanced/security/http-basic-auth/) docs go over the 
built-in modules for ensuring that Web API calls are made with credentials.  The `HTTPBasicCredentials` object type
contains the username and password data sent when using HTTP Basic Authentication.  The functions in 
`web_blackjack.py` should be modified to accept objects of this type.  You'll only need the shorter code on that
link, but you can also read the rest of the document to see how they approach it.  We're going to use `pynacl` to
generate, store, and compare password hashes instead of `secrets.compare_digest()`.


# **Updated** Web API HTTP Paths and Responses

## home()
```
GET /
returns: {'message': 'Welcome to Blackjack!'}
```
Just returns a friendly message.

## create_user()
```
POST /user/create?username=
returns: {'success': True, 'username': <the_username>, 'password': <the_password>}
```
Asks the UserDB object to create a new user with the username `the_username`, or return an HTTP 400 error that specifies
the username is taken.  Then, return the password for the user.

## create_game()
```
GET /game/create/{num_players: int}
AUTH REQUIRED
returns: {'success': True, 'game_id': game_uuid, 'termination_password': the_password, 'game_owner': <owner_username>}
```
Asks the database object to create a new game `game_id`, then returns the UUID of the game in the `game_id` key 
and the password needed for termination in the `termination_password` key.  The game's owner is always the first player
and the username will be taken from the HTTPBasicCredentials object passed in through HTTP Basic Auth.

## add_player_to_game()
```
POST /game/{game_id}/add_player?username=
AUTH REQUIRED
returns: {'success': True, 'game_id': game_uuid, 'player_username': player_username, 'player_idx': player_idx}
```
Asks the database object to add player with `username` to game `game_id`, then returns the `player_idx` of the added
player.  If the maximum number of players for the game has been reached, return an HTTP 400 error.  
Only the game owner can add a player.

## get_player_idx()
```
GET /game/{game_id}/get_player_idx?username=
AUTH REQUIRED
returns: {'success': True, 'game_id': game_uuid, 'player_username': player_username, 'player_idx': player_idx}
```
Asks the database object for the player_idx of the player with username `username`. 
Only the players or game owner can perform the lookup.

## init_game()
```
POST /game/{game_id}/initialize
AUTH REQUIRED
returns: {'success': True, 'dealer_stack': dealer_stack, 'player_stacks': player_stacks}
```
Asks the database for the pointer to the game `game_id`, calls `initial_deal()` on the game, then returns the 
stacks (hands) from `get_stacks()` on the game.  Only the game's owner can initialize the game.

## player_hit()
```
POST /game/{game_id}/player/{player_idx}/hit
AUTH REQUIRED
returns: {'player': player_idx, 'drawn_card': str(drawn_card), 'player_stack': player's stack}
```
Asks the database for the pointer to the game `game_id`, hits for the player `player_idx`, then returns the 
result of the hit and the new stack (hand).  Only the actual player can hit.

## player_stack()
```
GET /game/{game_id}/player/{player_idx}/stack
AUTH REQUIRED
returns: {'player': player_idx, 'player_stack': player's stack}
```
Returns the current stack (hand) of the player specified by `player_idx` in the game `game_id`.

## dealer_play()
```
POST /game/{game_id}/dealer/play
AUTH REQUIRED
returns: {'player': 'dealer', 'player_stack': dealer's stack}
```
Plays the dealer (call `dealer_draw()` on the game until the dealer can stop), then return the dealer's hand.

## get_winners()
```
GET /game/{game_id}/winners
returns: {'game_id': game_id, 'winners': winner_list}
```
Computes the winners of game `game_id` using `compute_winners()`, then returns the winners.

## delete_game()
```
POST /game/{game_id}/terminate?password=...
AUTH REQUIRED
returns: {'success': True, 'deleted_id': game_id}
```
Terminates the game `game_id` and authorizes the termination with the password provided as `password` query key.
