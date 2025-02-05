# ruff: noqa: D100,S311

# standard
import sys
import logging



# sirst party
from .cmd_line import read_args
from .exceptions import SnakeError
from .game import Game
from .score import Score
from .scores import Scores  # Assure-toi que cette importation est correcte

logger = logging.getLogger("foo")





def main() -> None:  # noqa: D103
    try:
        # read command line arguments
        args = read_args()

        # we define a custom named logger
        logger = logging.getLogger("foo")
        # Registration of the new handler
        handler = logging.StreamHandler(sys.stderr)
        logger.addHandler(handler) 

        # load scores from the YAML file
        scores = Scores.load("high_scores.yaml")  # Charge les scores du fichier YAML

        # start game and pass the current scores to it
        game = Game(width=args.width, height=args.height,
                    tile_size=args.tile_size, fps=args.fps,
                    fruit_color=args.fruit_color,
                    snake_head_color=args.snake_head_color,
                    snake_body_color=args.snake_body_color,
                    gameover_on_exit=args.gameover_on_exit,
                    scores=scores)  # Passe les scores à la logique du jeu

        # start the game
        game.start()

        # after the game, handle the player's score
        if game.is_game_over():  # assure-toi d’avoir une méthode `is_game_over` dans Game
            # ask for player's name and add score to the scores list
            player_name = input("Enter your name: ")
            player_score = game.get_player_score()  # Récupère le score du joueur
            player_score_obj = Score(score=player_score, name=player_name)
            scores.add_score(player_score_obj)

            # save updated scores to the file
            scores.save("high_scores.yaml")

    except SnakeError as e:
        logger.critical("This is a FATAL level log message. Something terrible happened.")
        sys.exit(1)
