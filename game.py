from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.config import Config
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from random import randint
from kivy.uix.popup import Popup
import json

class MainMenu(Screen):
    def __init__(self, **kwargs):
        super(MainMenu, self).__init__(**kwargs)
        self.create_layout()

    def create_layout(self):
        layout = BoxLayout(orientation='vertical')

        start_button = Button(text="Start Game", size_hint_y=None, height=50,
                              background_color=(0.2, 0.6, 0.2, 1),
                              color=(1, 1, 1, 1))
        start_button.bind(on_press=self.start_game)

        settings_button = Button(text="Settings", size_hint_y=None, height=50,
                                 background_color=(0.2, 0.4, 0.8, 1),
                                 color=(1, 1, 1, 1))
        settings_button.bind(on_press=self.show_settings)

        high_scores_button = Button(text="High Scores", size_hint_y=None, height=50,
                                    background_color=(0.8, 0.8, 0.2, 1),
                                    color=(1, 1, 1, 1))
        high_scores_button.bind(on_press=self.show_high_scores)

        exit_button = Button(text="Exit", size_hint_y=None, height=50,
                             background_color=(0.8, 0.2, 0.2, 1),
                             color=(1, 1, 1, 1))
        exit_button.bind(on_press=self.exit_app)

        layout.add_widget(Label(text="Snake Game", font_size=30))
        layout.add_widget(start_button)
        layout.add_widget(settings_button)
        layout.add_widget(high_scores_button)
        layout.add_widget(exit_button)

        self.add_widget(layout)

    def start_game(self, instance):
        self.manager.current = 'game'

    def show_settings(self, instance):
        self.manager.current = 'settings'

    def show_high_scores(self, instance):
        self.manager.current = 'high_scores'

    def exit_app(self, instance):
        App.get_running_app().stop()

class HighScoresScreen(Screen):
    def __init__(self, game_screen, **kwargs):
        super(HighScoresScreen, self).__init__(**kwargs)
        self.game_screen = game_screen
        self.create_layout()

    def create_layout(self):
        layout = BoxLayout(orientation='vertical')

        back_button = Button(text="Back to Main Menu", size_hint_y=None, height=50,
                             background_color=(0.2, 0.6, 0.2, 1),
                             color=(1, 1, 1, 1))
        back_button.bind(on_press=self.back_to_menu)

        layout.add_widget(Label(text="High Scores", font_size=30))

        # Load high scores from file
        self.game_screen.load_high_scores()

        for level, score in self.game_screen.high_scores.items():
            layout.add_widget(Label(text=f"Level {level}: {score}", font_size=20))

        layout.add_widget(back_button)

        self.add_widget(layout)

    def back_to_menu(self, instance):
        self.manager.current = 'main_menu'


class SettingsScreen(Screen):
    def __init__(self, game_screen, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        self.game_screen = game_screen
        self.create_layout()

    def create_layout(self):
        layout = BoxLayout(orientation='vertical')

        difficulty_label = Label(text="Difficulty Level", font_size=20)
        difficulty_slider = Slider(min=1, max=3, value=2, step=1)

        save_button = Button(text="Save", size_hint_y=None, height=50)
        save_button.bind(on_press=lambda instance: self.save_settings(difficulty_slider.value))

        layout.add_widget(difficulty_label)
        layout.add_widget(difficulty_slider)
        layout.add_widget(save_button)

        self.add_widget(layout)

    def save_settings(self, difficulty_level):
        self.game_screen.difficulty_level = int(difficulty_level)
        Clock.unschedule(self.game_screen.update)
        Clock.schedule_interval(self.game_screen.update, 1.0 / self.game_screen.game_speeds[self.game_screen.difficulty_level - 1])
        self.manager.current = 'main_menu'


class GameOverScreen(Screen):
    def __init__(self, game_screen, current_score, **kwargs):
        super(GameOverScreen, self).__init__(**kwargs)
        self.game_screen = game_screen
        self.current_score = current_score
        self.create_layout()

    def create_layout(self):
        layout = BoxLayout(orientation='vertical')

        restart_button = Button(text="Try Again", size_hint_y=None, height=50,
                                background_color=(0.2, 0.6, 0.2, 1),
                                color=(1, 1, 1, 1))
        restart_button.bind(on_press=self.restart_game)

        back_to_menu_button = Button(text="Back to Main Menu", size_hint_y=None, height=50,
                                     background_color=(0.2, 0.4, 0.8, 1),
                                     color=(1, 1, 1, 1))
        back_to_menu_button.bind(on_press=self.back_to_menu)

        layout.add_widget(Label(text="Game Over", font_size=30))
        layout.add_widget(restart_button)
        layout.add_widget(back_to_menu_button)

        self.add_widget(layout)

    def restart_game(self, instance):
        self.game_screen.reset_game()
        self.manager.current = 'game'

    def back_to_menu(self, instance):
        self.game_screen.reset_game()
        self.manager.current = 'main_menu'

class SnakeGame(Screen):
    def __init__(self, difficulty_level=2, **kwargs):
        super(SnakeGame, self).__init__(**kwargs)
        self.high_scores_file = "high_scores.json"
        self.load_high_scores()

        self.snake_size = 20
        self.snake_pos = [(100, 100)]
        self.direction = (1, 0)
        self.food_pos = self.spawn_food()
        self.difficulty_level = difficulty_level
        self.game_speeds = [10, 15, 20]
        self.eat_sound = SoundLoader.load('food_G1U6tlb.mp3')
        self.game_over_sound = SoundLoader.load('game_over_sound.mp3')


        self.score = 0
        self.score_label = Label(text="Score: {}".format(self.score), font_size=20)
        self.high_scores = {1: 0, 2: 0, 3: 0}
        self.apples_eaten_for_record = {1: 0, 2: 0, 3: 0}

        self.game_canvas = Widget()
        self.create_layout()

        self.add_widget(self.game_canvas)

        Clock.schedule_interval(self.update, 1.0 / self.game_speeds[self.difficulty_level - 1])

    def create_layout(self):
        layout = BoxLayout(orientation='vertical')
        self.add_widget(layout)
        self.score_label.pos_hint = {'top': 1}
        layout.add_widget(self.score_label)

    def spawn_food(self):
        x = randint(0, (self.width - self.snake_size) // self.snake_size) * self.snake_size
        y = randint(0, (self.height - self.snake_size) // self.snake_size) * self.snake_size
        return x, y

    def load_high_scores(self):
        try:
            with open(self.high_scores_file, 'r') as file:
                self.high_scores = json.load(file)
        except FileNotFoundError:
            pass

    def save_high_scores(self):
        with open(self.high_scores_file, 'w') as file:
            json.dump(self.high_scores, file)

    def update_high_score(self):
        current_high_score = self.high_scores.get(self.difficulty_level, 0)
        if self.score > current_high_score:
            self.high_scores[self.difficulty_level] = self.score
            self.save_high_scores()

    def update_score(self, points):
        self.score += points
        self.score_label.text = "Score: {}".format(self.score)
        print(f"Score Updated: {self.score}")

    def update(self, dt):
        # Only update when the current screen is 'game'
        if self.manager.current == 'game':
            self.move_snake()
            self.check_collision()
            self.draw_snake()
            self.draw_food()

    def move_snake(self):
        new_head = (
            self.snake_pos[0][0] + self.direction[0] * self.snake_size,
            self.snake_pos[0][1] + self.direction[1] * self.snake_size
        )
        self.snake_pos.insert(0, new_head)
        self.snake_pos.pop()

    def draw_snake(self):
        self.game_canvas.canvas.clear()
        with self.game_canvas.canvas:
            Color(0, 1, 0)
            for pos in self.snake_pos:
                Rectangle(pos=pos, size=(self.snake_size, self.snake_size))

    def draw_food(self):
        with self.game_canvas.canvas:
            Color(1, 0, 0)
            Rectangle(pos=self.food_pos, size=(self.snake_size, self.snake_size))

    def reset_game(self):
        self.snake_pos = [(100, 100)]
        self.direction = (1, 0)
        self.food_pos = self.spawn_food()
        self.game_over_sound.stop()
        self.update_high_score()
        self.score = 0
        self.update_score(0)
        self.apples_eaten_for_record[self.difficulty_level] = 0
        print(f"Score Reset: {self.score}")

    def play_eat_sound(self):
        if self.eat_sound:
            self.eat_sound.play()

    def play_game_over_sound(self):
        pass

    def check_collision(self):
        if len(set(self.snake_pos)) < len(self.snake_pos):
            self.show_game_over_popup()
            self.play_game_over_sound()
            return

        head_x, head_y = self.snake_pos[0]
        if not (0 <= head_x < self.width) or not (0 <= head_y < self.height):
            self.show_game_over_popup()
            return

        if head_x == self.food_pos[0] and head_y == self.food_pos[1]:
            self.food_pos = self.spawn_food()
            self.snake_pos.append(self.snake_pos[-1])
            self.play_eat_sound()
            self.update_score(1)
            self.apples_eaten_for_record[self.difficulty_level] += 1

            if self.apples_eaten_for_record[self.difficulty_level] >= 18:
                self.break_record()
                self.apples_eaten_for_record[self.difficulty_level] = 0

    def break_record(self):
        message = f"Congratulations! You broke record {self.difficulty_level}!"
        self.show_break_record_popup(message)

    def show_break_record_popup(self, message):
        popup = Popup(title='New Record!', content=Label(text=message), size_hint=(None, None), size=(400, 200))
        popup.open()

    def show_game_over_popup(self):
        current_score = self.score
        print(f"Current Score (before reset): {current_score}")
        self.reset_game()
        print(f"Current Score (after reset): {self.score}")

        # Correct instantiation of GameOverScreen
        popup = GameOverScreen(game_screen=self , current_score=current_score , name='game_over')
        self.manager.add_widget(popup)
        self.manager.current = 'game_over'

    def on_touch_down(self, touch):
        head_x, head_y = self.snake_pos[0]
        touch_x, touch_y = touch.pos

        if abs(head_x - touch_x) > abs(head_y - touch_y):
            self.direction = (1 if touch_x > head_x else -1, 0)
        else:
            self.direction = (0, 1 if touch_y > head_y else -1)

    def on_key_down(self, window, key, *args):
        if key == 119:
            self.direction = (0, 1)
        elif key == 115:
            self.direction = (0, -1)
        elif key == 97:
            self.direction = (-1, 0)
        elif key == 100:
            self.direction = (1, 0)

        icon_path = '/home/mark_puhach/PycharmProjects/pythonProject2432/Blackvariant-Button-Ui-Requests-13-Snake.512 (4).png'
        Config.set('kivy' , 'window_icon' , icon_path)

class SnakeApp(App):
    def build(self):
        sm = ScreenManager()

        main_menu = MainMenu(name='main_menu')
        sm.add_widget(main_menu)

        game_screen = SnakeGame(name='game')
        sm.add_widget(game_screen)

        settings_screen = SettingsScreen(game_screen, name='settings')
        sm.add_widget(settings_screen)

        high_scores_screen = HighScoresScreen(game_screen, name='high_scores')
        sm.add_widget(high_scores_screen)

        game_over_screen = GameOverScreen(game_screen=game_screen , current_score=0 , name='game_over')
        sm.add_widget(game_over_screen)

        return sm

if __name__ == '__main__':
    SnakeApp().run()



