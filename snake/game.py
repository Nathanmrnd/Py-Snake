import importlib.resources
import pygame
import typing
import logging

from .board import Board
from .checkerboard import Checkerboard
from .dir import Dir
from .exceptions import GameOver
from .fruit import Fruit
from .game_object import GameObject
from .score import Score
from .scores import Scores  # Importation des scores
from .snake import Snake
from .state import State

# constantes
SK_START_LENGTH = 3
MAX_LENGHT = 8
MAX_SCORES = 5
logger = logging.getLogger("foo")

class Game:
    """The main class of the game."""

    def __init__(self, width: int, height: int, tile_size: int,  # noqa: PLR0913
                 fps: int,
                 *,
                 fruit_color: pygame.Color,
                 snake_head_color: pygame.Color,
                 snake_body_color: pygame.Color,
                 gameover_on_exit: bool,
                 scores
                 ) -> None:
        """Object initialization."""
        self._width = width
        self._height = height
        self._tile_size = tile_size
        self._fps = fps
        self._fruit_color = fruit_color
        self._snake_head_color = snake_head_color
        self._snake_body_color = snake_body_color
        self._gameover_on_exit = gameover_on_exit
        self._snake = None
        self._new_high_score = None | Score

        # chargement des scores depuis le fichier YAML
        self._scores = Scores.load("high_scores.yaml")

    def _reset_snake(self) -> None:
        """Reset the snake."""
        logger.setLevel(logging.INFO)
        logger.info("We reset the snake")
        if self._snake is not None:
            self._board.detach_obs(self._snake)
            self._board.remove_object(self._snake)
        self._snake = Snake.create_random(
                nb_lines=self._height,
                nb_cols=self._width,
                length=SK_START_LENGTH,
                head_color=self._snake_head_color,
                body_color=self._snake_body_color,
                gameover_on_exit=self._gameover_on_exit,
        )
        self._board.add_object(self._snake)
        self._board.attach_obs(self._snake)

    def _init(self) -> None:
        """Initialize the game."""
        # create a display screen
        screen_size = (self._width * self._tile_size,
                       self._height * self._tile_size)
        self._screen = pygame.display.set_mode(screen_size)

        # create the clock
        self._clock = pygame.time.Clock()

        # create the main board
        self._board = Board(screen=self._screen,
                            nb_lines=self._height,
                            nb_cols=self._width,
                            tile_size=self._tile_size)

        # create checkerboard
        logger.setLevel(logging.INFO)
        logger.info("Checkerboard is created")
        self._checkerboard = Checkerboard(nb_lines=self._height,
                                          nb_cols=self._width)
        self._board.add_object(self._checkerboard)

        # create snake
        
        logger.info("The snake is created")
        self._reset_snake()

        # create fruit
        logger.info("The fruit is created")
        Fruit.color = self._fruit_color
        self._board.create_fruit()

        # download font
        with importlib.resources.path("snake", "DejaVuSansMono-Bold.ttf") as f:
            self._font_1 = pygame.font.Font(f, 32)
            self._font_2 = pygame.font.Font(f, 64)

    def _drawgameover(self) -> None:
        """Draw the gameover's sentence."""
        text_gameover = self._font_2.render("GAME OVER", True, pygame.Color("red"))
        x, y = 80, 160  # Define the position where to write text.
        self._screen.blit(text_gameover, (x, y))

    def _draw_scores(self) -> None:
        """Put a highscore's line."""
        x, y = 80, 10  # Define the position where to write text.
        for score in self._scores:
            text_scores = self._font_1.render(score.name.ljust(Score.MAX_LENGTH) + f" {score.score: >8}", True, pygame.Color("red"))
            self._screen.blit(text_scores, (x, y))
            y += 32
        pygame.display.update()

    def _draw_inputname(self) -> None:
        """Draw the input name screen."""
        text = self._font_1.render(f"Enter your name: {self._new_high_score.name}", True, pygame.Color("red"))
        x, y = 80, 10  # Position of the text
        self._screen.blit(text, (x, y))
        pygame.display.update()

    def _process_scores_event(self, event: pygame.event.Event) -> None:
        """Switch to the state Play if needed."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self._state = State.PLAY

    def _process_play_event(self, event: pygame.event.Event) -> None:
        """Change the direction of the snake if needed."""
        if event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_UP:
                    self._snake.dir = Dir.UP
                case pygame.K_DOWN:
                    self._snake.dir = Dir.DOWN
                case pygame.K_LEFT:
                    self._snake.dir = Dir.LEFT
                case pygame.K_RIGHT:
                    self._snake.dir = Dir.RIGHT

    def _process_inputname(self, event: pygame.event.Event) -> None:
        """The player enters his/her name in the ranking list of highscores."""
        logger.info("The player enters his/her name.")
        if self._new_high_score is not None and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:  # validate the name
                # save the score with the player's name
                self._scores.add_score(self._new_high_score)  # add the score with the name
                self._scores.save("high_scores.yaml")  # save the scores in the YAML file
                self._state = State.SCORES  # return to the scores screen, not quit
            elif event.key == pygame.K_BACKSPACE:  # correct a mistake
                self._new_high_score.name = self._new_high_score.name[:-1]
            else:
                # add a character to the name
                self._new_high_score.name += event.unicode

    def _process_events(self) -> None:
        """Process pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._state = State.QUIT  # properly handle quit event
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:  # press 'Q' to quit
                    self._state = State.QUIT
                # handle other states
                match self._state:
                    case State.SCORES:
                        self._process_scores_event(event)
                    case State.PLAY:
                        self._process_play_event(event)
                    case State.INPUT_NAME:
                        self._process_inputname(event)

    def start(self) -> None:
        """Start the game."""
        # initialize pygame
        pygame.init()

        # initialize game
        self._init()

        # start pygame loop
        self._state = State.SCORES
        while self._state != State.QUIT:

            # wait 1/FPS second
            self._clock.tick(self._fps)

            # listen for events
            self._process_events()

            # update objects
            try:
                if self._state == State.PLAY:
                    self._snake.move()

            except GameOver:
                self._state = State.GAMEOVER
                countdown = self._fps

            # clear the screen before drawing the next frame
            self._screen.fill(pygame.Color("black"))

            # draw
            self._board.draw()
            match self._state:
                case State.GAMEOVER:
                    self._drawgameover()
                    countdown -= 1
                    if countdown == 0:
                        score = self._snake.score
                        self._reset_snake()
                        if self._scores.is_highscore(score):
                            self._new_high_score = Score(name="", score=score)
                            self._state = State.INPUT_NAME  # Switch to name input state
                        else:
                            self._state = State.SCORES
                case State.SCORES:
                    self._draw_scores()
                case State.INPUT_NAME:
                    self._draw_inputname()

            # display
            pygame.display.update()

        # terminate pygame
        pygame.quit()
