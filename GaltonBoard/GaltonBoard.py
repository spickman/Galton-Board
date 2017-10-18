import pygame
import numpy as np
import random
import time
from pygame.locals import *
from TextBox_class import TextBox
from Button_class import Button
from Slider_class import Slider
import csv
import configparser


class App:
    windowWidth = 1000
    windowHeight = 850
    x = 10
    y = 10


    def __init__(self):
        self.menu_height = 100
        self.dt = 0.01
        self.board_height = 700
        self.x_start = int(self.windowWidth / 2)
        self._running = True
        self._display_surf = None
        self._board_surf = None
        self.number_of_levels = 20
        self.cp = ColourPalette()
        self.pin_size = 8

        tmp_ball = GaltonBall(0)
        self.total_radius = self.pin_size + tmp_ball.radius

        self._board_surf = pygame.Surface((self.windowWidth, self.board_height))
        self.balls = None
        self.pins = None
        self.bins = list()
        self.unpause_number_of_balls = None
        self.paused = False
        self.bin_length = 0
        pygame.init()
        self._display_surf = pygame.display.set_mode((self.windowWidth, self.windowHeight))
        pygame.display.set_caption('Galton Board')
        self._running = True
        self.number_of_balls = 20
        self.delay_time = 0
        self.ball_delay = self.delay_time
        self.number_of_results = 0
        self.font = pygame.font.Font(None, 24)
        self.font2 = pygame.font.SysFont("Consolas", 12, )
        self.number_of_results_text = self.font.render('Total Balls : ' + str(self.number_of_results), True,
                                                       self.cp.white)
        self.bin_text = self.font2.render(''.join([str(tmp_bin.value) for tmp_bin in self.bins]), True,
                                          self.cp.white)

        self.status_bar = StatusBar(pop_time=2)
        self.status_text = self.font.render('', True, self.cp.grey)

        self.UIComponents = dict()
        self.UIComponents['ball_input'] = TextBox((475, self.board_height + 40, 50, 20),
                                                  command=self.change_number_of_balls,
                                                  clear_on_enter=False, inactive_on_enter=False,
                                                  label="Number of balls")

        self.UIComponents['speed_input'] = TextBox((475, self.board_height + 100, 50, 20),
                                                   command=self.change_speed_of_balls,
                                                   clear_on_enter=False, inactive_on_enter=False, percentage=True,
                                                   label="Ball delay")

        self.UIComponents['level_input'] = TextBox((475, self.board_height + 10, 50, 20),
                                                   command=self.change_number_of_levels,
                                                   clear_on_enter=False, inactive_on_enter=False,
                                                   label="Number of levels")

        self.UIComponents['dt_input'] = TextBox((475, self.board_height + 70, 50, 20), command=self.change_dt,
                                                clear_on_enter=False, inactive_on_enter=False, percentage=True,
                                                label="Ball speed")

        self.UIComponents['ResetButton'] = Button((800, self.board_height + 40, 100, 20), command=self.reset_command,
                                                  label="Reset")
        self.UIComponents['PauseButton'] = Button((800, self.board_height + 10, 100, 20), command=self.pause_command,
                                                  label="Pause", latching_label="Continue",
                                                  active_color=self.cp.red)
        self.UIComponents['Preset1Button'] = Button((675, self.board_height + 10, 100, 20),
                                                    command=self.preset1_command, label="Preset1")
        self.UIComponents['Preset2Button'] = Button((675, self.board_height + 40, 100, 20),
                                                    command=self.preset2_command,
                                                    label="Preset2")
        self.UIComponents['Preset3Button'] = Button((675, self.board_height + 70, 100, 20),
                                                    command=self.preset3_command, label="Preset3")
        self.UIComponents['SaveDataButton'] = Button((800, self.board_height + 70, 100, 20),
                                                     command=self.save_data_command, label="Save Data")
        self.UIComponents['level_slider'] = Slider((550, self.board_height + 10, 100, 20),
                                                   command=self.level_slider_command)
        self.UIComponents['ball_slider'] = Slider((550, self.board_height + 40, 100, 20),
                                                  command=self.ball_slider_command)
        self.UIComponents['dt_slider'] = Slider((550, self.board_height + 70, 100, 20),
                                                command=self.dt_slider_command)
        self.UIComponents['speed_slider'] = Slider((550, self.board_height + 100, 100, 20),
                                                   command=self.speed_slider_command)

        self.change_dt(-1)
        self.change_number_of_balls(-1)
        self.change_number_of_levels(-1)
        self.change_speed_of_balls(-1)
        self.load_preset_labels()
        self.preset3_command()
        self.setup_board()

    def pause_command(self):
        if self.paused:
            self.paused = False
            self.change_number_of_balls(self.unpause_number_of_balls, set_value=True)
            self.unpause_number_of_balls = None
            self.status_bar.set_status("Running")
        else:
            self.unpause_number_of_balls = self.number_of_balls
            self.change_number_of_balls(0, set_value=False)
            self.balls = list()
            self.paused = True
            self.status_bar.set_status("Paused")

    def save_data_command(self):
        if self.bins:
            with open("data.txt", 'w') as f:
                writer = csv.writer(f, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                writer.writerow(['position', 'count'])
                for tmp_bin in self.bins:
                    writer.writerow([(tmp_bin.x - self.windowWidth / 2) / tmp_bin.width + 0.5, tmp_bin.value])
            self.status_bar.add_item("Saved Data")

    def setup_board(self):
        self.setup_pins(self.number_of_levels, self.total_radius)
        self.setup_graph(self.number_of_levels + 1, self.total_radius)
        self.setup_balls()

    def reset_command(self):
        self.setup_board()
        return

    def level_slider_command(self):
        self.change_number_of_levels(self.UIComponents['level_slider'].value, set_value=True, percent=True)

    def ball_slider_command(self):
        self.change_number_of_balls(self.UIComponents['ball_slider'].value, set_value=True, percent=True)

    def speed_slider_command(self):
        self.change_speed_of_balls(self.UIComponents['speed_slider'].value, set_value=True, percent=True)

    def dt_slider_command(self):
        self.change_dt(self.UIComponents['dt_slider'].value, set_value=True, percent=True)

    def preset1_command(self):
        self.load_preset('preset1config.ini')
        self.reset_command()

    def preset2_command(self):
        self.load_preset('preset2config.ini')
        self.reset_command()

    def preset3_command(self):
        self.load_preset('preset3config.ini')
        self.reset_command()

    def load_preset(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)
        try:
            self.change_number_of_balls(float(self.config_section_map(config, "SectionOne")['number_of_balls']),set_value=True)
            self.change_dt(float(self.config_section_map(config, "SectionOne")['speed_of_balls%']), set_value=True, percent=True)
            self.change_speed_of_balls(float(self.config_section_map(config, "SectionOne")['ball_delay%']), set_value=True, percent=True)
            self.change_number_of_levels(float(self.config_section_map(config, "SectionOne")['number_of_levels']),set_value=True)
        except Exception as e:
            print("load_preset : ", e)
            self.status_bar.add_item('Bad config file : ' + filename)

    def load_preset_labels(self):
        config = configparser.ConfigParser()
        config.read('preset1config.ini')
        self.UIComponents['Preset1Button'].label = self.config_section_map(config, "SectionOne")['label']
        config.read('preset2config.ini')
        self.UIComponents['Preset2Button'].label = self.config_section_map(config, "SectionOne")['label']
        config.read('preset3config.ini')
        self.UIComponents['Preset3Button'].label = self.config_section_map(config, "SectionOne")['label']

    def config_section_map(self, config, section):
        dict1 = {}
        options = config.options(section)
        for option in options:
            try:
                dict1[option] = config.get(section, option)
                if dict1[option] == -1:
                    print("skip: %s" % option)
            except Exception as e:
                print(e)
                dict1[option] = None
        return dict1

    def on_event(self, event):
        if event.type == QUIT:
            self._running = False

        for element in self.UIComponents:
            self.UIComponents[element].get_event(event)

    def change_dt(self, num, set_value=False, percent=False):
        dt_min = 0.002
        dt_max = 0.03
        value_to_set = self.on_change('dt_input', 'dt_slider', dt_min, dt_max, num, percent=percent, display_percent=True, set_value=set_value, reverse=True)
        if value_to_set is not None:
            self.dt = value_to_set

    def change_number_of_balls(self, num, set_value=False, percent=False):
        number_of_balls_max = 1000
        number_of_balls_min = 0
        value_to_set = self.on_change('ball_input', 'ball_slider', number_of_balls_min, number_of_balls_max, num, percent=percent, set_value=set_value)
        if value_to_set is not None:
            if self.paused:
                self.number_of_balls = 0
            else:
                self.number_of_balls = int(value_to_set)

    def change_speed_of_balls(self, num, set_value=False, percent=False):
        speed_of_balls_min = 0
        speed_of_balls_max = 100
        value_to_set = self.on_change('speed_input', 'speed_slider', speed_of_balls_min, speed_of_balls_max, num, percent=percent, set_value=set_value)
        if value_to_set is not None:
            self.delay_time = value_to_set

    def change_number_of_levels(self, num, set_value=False, percent=False):
        number_of_levels_max = 40
        number_of_levels_min = 1

        value_to_set = self.on_change('level_input', 'level_slider', number_of_levels_min, number_of_levels_max, num, percent=percent, set_value=set_value)
        if value_to_set is not None:
            self.number_of_levels = int(value_to_set)
            if self.number_of_levels <= 20:
                self.pin_size = 8
            else:
                self.pin_size = 8 - int(5 - (40 - self.number_of_levels) / 5)

            tmpball = GaltonBall(1)
            self.total_radius = tmpball.radius + self.pin_size
            self.reset_command()

    def on_change(self, textbox, slider, minimum, maximum, value, percent=False, display_percent=False, set_value=False, reverse=False):
        value_range = maximum - minimum
        value_to_set = None
        if percent:
            value *= value_range
            value += minimum
        try:
            if minimum <= float(value) <= maximum:
                value_to_set = float(value)
            elif float(value) < minimum:
                value_to_set = minimum
            elif float(value) > maximum:
                value_to_set = maximum

            if value_to_set is not None:
                if set_value:
                    if display_percent:
                        self.UIComponents[textbox].buffer = list(str(int(round(100*(value_to_set-minimum)/value_range, 1))))
                    else:
                        self.UIComponents[textbox].buffer = list(str(int(value_to_set)))
                    self.UIComponents[slider].value = float(float(value_to_set)-minimum)/value_range

        except Exception as e:
            print("on_change : ", e)
        if reverse and value_to_set:
            value_to_set = maximum - (value_to_set-minimum)
        return value_to_set

    def setup_balls(self):
        self.balls = list()

    def create_ball(self):
        tmp_ball = GaltonBall(self.total_radius)
        tmp_ball.x = self.x_start
        self.balls.append(tmp_ball)

    def on_loop(self):

        for ball in self.balls:
            ball.update(self.collision_with_pin(ball))
            self.is_ball_off_screen(ball)

        if len(self.balls) < self.number_of_balls:
            if self.ball_delay < 0:
                self.create_ball()
                self.ball_delay = self.delay_time

        self.ball_delay -= 1

    def is_ball_off_screen(self, ball):
        if ball.y > self.board_height:
            for tmp_bin in self.bins:
                if tmp_bin.trigger == ball.x:
                    tmp_bin.value += 1
                    self.number_of_results += 1
                    break
            self.balls.remove(ball)

    def on_render(self):
        self.status_bar.update()
        self._display_surf.fill(pygame.Color('black'))
        self._display_surf.blit(self._board_surf, (0, 0))

        self.number_of_results_text = self.font.render('Total Balls : ' + str(self.number_of_results), True,
                                                       self.cp.white)
        self._display_surf.blit(self.number_of_results_text, (20, self.board_height + 10))

        self.status_text = self.font.render(self.status_bar.current_status(), True, self.cp.grey)
        self._display_surf.blit(self.status_text, (10, self.windowHeight - 30))
        if self.number_of_levels <= 20:
            bin_string = ' | '.join(['{:^2}'.format(tmp_bin.value) for tmp_bin in self.bins])
        else:
            bin_string = "Data only shown for <=20 levels"

        self.bin_text = self.font2.render(bin_string, True, self.cp.white)
        bin_pos = (self.windowWidth / 2.0 - self.bin_text.get_width() / 2.0)
        self._display_surf.blit(self.bin_text, (bin_pos, 10))

        self.update_graph()

        for ball in self.balls:
            pygame.draw.circle(self._display_surf, self.cp.ball, (ball.x, ball.y), ball.radius)

        for element in self.UIComponents:
            self.UIComponents[element].update()
            self.UIComponents[element].draw(self._display_surf)

        pygame.display.update()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        accumulator = 0.0
        t = 0.0
        current_time = time.perf_counter() - 1

        while self._running:
            new_time = time.perf_counter()
            frame_time = new_time - current_time
            current_time = time.perf_counter()

            accumulator += frame_time

            for event in pygame.event.get():
                self.on_event(event)

            while accumulator >= self.dt:
                self.on_loop()
                accumulator -= self.dt
                t += self.dt
            self.on_render()

        self.on_cleanup()

    def setup_pins(self, levels, total_radius):
        self._board_surf.fill(self.cp.black)
        self.pins = list()
        start_y = 80
        start_x = self.x_start
        x = start_x
        y = start_y
        for i in range(1, levels + 1):
            tmp_level = list()
            for j in range(0, i):
                tmp_level.append(GaltonPin(x, y, self.pin_size))
                x += int(total_radius * 2)
            self.pins.append(tmp_level)
            start_x -= total_radius
            start_y += total_radius * 2
            x = start_x
            y = start_y
        for i in range(0, self.number_of_levels):
            for pin in self.pins[i]:
                pygame.draw.circle(self._board_surf, self.cp.pin, (pin.x, pin.y), pin.radius)

    def setup_graph(self, bins, total_radius):
        self.bins = list()
        self.number_of_results = 0
        x = self.x_start
        for i in range(0, self.number_of_levels):
            x -= total_radius

        for i in range(0, bins):
            tmpbin = GaltonBin()
            tmpbin.trigger = x
            tmpbin.width = total_radius * 2
            tmpbin.x = x - total_radius
            self.bins.append(tmpbin)
            x += total_radius * 2

    def update_graph(self):
        bin_max = max(tmp_bin.value for tmp_bin in self.bins)
        if bin_max == 0:
            bin_max = 1
        for galtonBin in self.bins:
            pygame.draw.rect(self._display_surf, self.cp.graph, (galtonBin.x, self.board_height, galtonBin.width,
                                                                 -1 * (125 / bin_max) * galtonBin.value))

    def collision_with_pin(self, ball):
        if ball.level < self.number_of_levels:
            pin = self.pins[ball.level][ball.next_pin]
            if pin.x == ball.x and (pin.y - self.total_radius) == ball.y:
                return True
            if pin.x == ball.x and (pin.y - self.total_radius) < ball.y:
                return True
        return False


class GaltonBin:
    def __init__(self):
        self.value = 0
        self.trigger = 0
        self.x = 0
        self.width = 0


class GaltonBall:
    def __init__(self, total_radius):
        self.x = 300
        self.y = 50
        self.x_speed = 25
        self.radius = 2
        self._animation_frames = list()
        self._animation_direction = 0
        self.level = 0
        self.next_pin = 0
        self.y_speed = 1
        self.total_radius = total_radius
        self._setup_animation()
        self._animation_frame_length = len(self._animation_frames)

    def update(self, collision):

        if self._animation_frame_length < len(self._animation_frames):
            if self._animation_direction == 0:
                self.x += self._animation_frames[self._animation_frame_length][0]
            elif self._animation_direction == 1:
                self.x -= self._animation_frames[self._animation_frame_length][0]

            self.y += self._animation_frames[self._animation_frame_length][1]
            self._animation_frame_length += 1

        elif collision:
            self._animation_frame_length = 0
            self.level += 1
            self._animation_direction = random.randint(0, 1)
            if self._animation_direction == 0:
                self.next_pin += 1
        else:
            self.y += self.y_speed

    def _setup_animation(self):
        prev_x_animation = 0
        x_animation = np.sqrt(self.total_radius ** 2 - (self.total_radius - 0) ** 2)
        for i in range(1, self.total_radius + 2, 1):
            x_difference = x_animation - prev_x_animation
            self._animation_frames.append((int(x_difference), 1))
            prev_x_animation = x_animation - (x_difference - int(x_difference))
            x_animation = np.sqrt(self.total_radius ** 2 - (self.total_radius - i) ** 2)


class GaltonPin:
    def __init__(self, x, y, pin_size):
        self.x = x
        self.y = y
        self.radius = pin_size


class StatusBar:
    def __init__(self, initial_text="Running", pop_time=1):
        self._pop_time = pop_time
        self._status_items = list()
        self._status_items.append(initial_text)
        self._timer = time.perf_counter()
        self._item_time = self._pop_time

    def update(self):
        elapsed_time = time.perf_counter() - self._timer
        self._timer = time.perf_counter()
        if len(self._status_items) > 1:
            if self._item_time < 0:
                self._status_items.pop(-1)
                self._item_time = self._pop_time
            else:
                self._item_time -= elapsed_time

    def current_status(self):
        return self._status_items[-1]

    def set_status(self, status):
        if isinstance(status, str):
            self._status_items = [status]
        else:
            raise TypeError("StatusBar cannot add object of type {}.".format(type(status)))

    def add_item(self, item):
        if isinstance(item, str):
            self._status_items.append(item)
        else:
            raise TypeError("StatusBar cannot add object of type {}.".format(type(item)))


class ColourPalette:
    white = pygame.Color('white')
    black = pygame.Color('black')
    grey = pygame.Color(120, 120, 120, 0)
    red = pygame.Color(180, 5, 5, 0)
    ball = pygame.Color('white')
    graph = pygame.Color(0, 128, 255, 0)
    pin = pygame.Color(100, 100, 100, 0)


if __name__ == "__main__":
    theApp = App()
    theApp.on_execute()
