import pygame
import numpy as np
from scipy.stats import norm

import random
import time
from pygame.locals import *
from TextBox_class import TextBox
from Button_class import Button
from Slider_class import Slider
import csv
import configparser
import logging


class App:
    windowWidth = 1000
    windowHeight = 850

    def __init__(self):
        # Config
        self.config_filename = 'GaltonBoard_config.ini'
        self.config = {'logging_level': 'DEBUG'}
        self.config_error = None
        self.load_config()

        self.logger = None
        self.setup_logger()

        if self.config_error is not None:
            self.logger.error('Failed to load config file. Using defaults : ' + str(self.config_error)
                              + " was searching for file : " + self.config_filename, exc_info=True)

        self.logger.info('__init__ started')
        self.board_height = 700
        self.ball_x_start = int(self.windowWidth / 2)
        self.ball_y_start = 50
        self._running = True

        self.pin_radius = 8
        tmp_ball = GaltonBall(1)
        self.total_radius = self.pin_radius + tmp_ball.radius

        self._board_surf = pygame.Surface((self.windowWidth, self.board_height))
        self._display_surf = pygame.display.set_mode((self.windowWidth, self.windowHeight))

        pygame.init()
        self.font = pygame.font.Font(None, 24)
        self.font2 = pygame.font.SysFont("Consolas", 12)

        self.status_bar = StatusBar(pop_time=2)

        self.balls = None
        self.pins = None
        self.bins = None
        self.unpause_number_of_balls = None
        self.UIComponents = None
        self.is_normal_visible = False
        self.paused = False

        pygame.display.set_caption('Galton Board')

        # Defaults for safety
        self.number_of_levels = 1
        self.number_of_balls = 0
        self.delay_time = 1
        self.delta_time_step = 0.03

        self.number_of_results = 0

        self.statistics = None

        self.preset_filenames = ['preset1config.ini', 'preset2config.ini', 'preset3config.ini']
        self.create_ui_elements()
        self.setup_board()
        self.load_preset_labels()
        self.preset3_command()
        self.logger.info('__init__ completed')

    def load_config(self):
        config = configparser.ConfigParser()
        try:
            config.read(self.config_filename)
            for key in self.config:
                value_to_set = self.config_section_map(config, "Config")[key]
                self.config[key] = value_to_set
        except Exception as e:
            # Failed to read in config file, however defaults have already been set.
            self.config_error = e
            pass

    def setup_logger(self):
        log_level_dict = {'DEBUG': logging.DEBUG,
                          'INFO': logging.INFO}
        logging.basicConfig()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level_dict[self.config['logging_level']])
        handler = logging.FileHandler('galton_board.log', 'w')
        handler.setLevel(log_level_dict[self.config['logging_level']])
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def create_ui_elements(self):
        self.UIComponents = dict()
        self.UIComponents['ball_input'] = TextBox((475, self.board_height + 40, 50, 20),
                                                  command=self.change_number_of_balls,
                                                  clear_on_enter=False, inactive_on_enter=False,
                                                  label="Number of balls")

        self.UIComponents['delay_input'] = TextBox((475, self.board_height + 100, 50, 20),
                                                   command=self.change_delay_between_balls,
                                                   clear_on_enter=False, inactive_on_enter=False, percentage=True,
                                                   label="Ball delay")

        self.UIComponents['level_input'] = TextBox((475, self.board_height + 10, 50, 20),
                                                   command=self.change_number_of_levels,
                                                   clear_on_enter=False, inactive_on_enter=False,
                                                   label="Number of levels")

        self.UIComponents['speed_input'] = TextBox((475, self.board_height + 70, 50, 20), command=self.change_speed,
                                                    clear_on_enter=False, inactive_on_enter=False, percentage=True,
                                                    label="Ball speed")

        self.UIComponents['ResetButton'] = Button((800, self.board_height + 40, 100, 20), command=self.reset_command,
                                                  label="Reset")

        self.UIComponents['PauseButton'] = Button((800, self.board_height + 10, 100, 20), command=self.pause_command,
                                                  label="Pause", latching_label="Continue",
                                                  active_color=ColourPalette.red)

        self.UIComponents['Preset1Button'] = Button((675, self.board_height + 10, 100, 20),
                                                    command=self.preset1_command, label="Preset1")

        self.UIComponents['Preset2Button'] = Button((675, self.board_height + 40, 100, 20),
                                                    command=self.preset2_command,
                                                    label="Preset2")

        self.UIComponents['Preset3Button'] = Button((675, self.board_height + 70, 100, 20),
                                                    command=self.preset3_command, label="Preset3")

        self.UIComponents['SaveDataButton'] = Button((800, self.board_height + 70, 100, 20),
                                                     command=self.save_data_command, label="Save Data")

        self.UIComponents['NormalToggle'] = Button((800, self.board_height + 100, 100, 20),
                                                   command=self.toggle_normal, label="Normal", latching_label="Normal",
                                                   active_color=ColourPalette.red)

        self.UIComponents['level_slider'] = Slider((550, self.board_height + 10, 100, 20),
                                                   command=self.level_slider_command)

        self.UIComponents['ball_slider'] = Slider((550, self.board_height + 40, 100, 20),
                                                  command=self.ball_slider_command)

        self.UIComponents['speed_slider'] = Slider((550, self.board_height + 70, 100, 20),
                                                    command=self.speed_slider_command)

        self.UIComponents['delay_slider'] = Slider((550, self.board_height + 100, 100, 20),
                                                   command=self.delay_slider_command)

    def toggle_normal(self):
        if self.is_normal_visible:
            self.is_normal_visible = False
        else:
            self.is_normal_visible = True

    def pause_command(self):
        if self.paused:
            self.paused = False
            self.change_number_of_balls(self.unpause_number_of_balls, set_value=True)
            self.unpause_number_of_balls = None
            self.status_bar.set_status("Running")
            self.logger.info('Un-paused')
        else:
            self.unpause_number_of_balls = self.number_of_balls
            self.change_number_of_balls(0, set_value=False)
            self.balls = list()
            self.paused = True
            self.status_bar.set_status("Paused")
            self.logger.info('Paused')

    def save_data_command(self):
        self.logger.info('Saving data')
        try:
            if self.bins:
                with open("data.txt", 'w') as f:
                    writer = csv.writer(f, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                    writer.writerow(['position', 'count'])
                    for tmp_bin in self.bins:
                        writer.writerow([(tmp_bin.x - self.windowWidth / 2) / tmp_bin.width + 0.5, tmp_bin.value])
                self.status_bar.add_item("Saved Data")
                self.logger.debug('Data saved success')
            else:
                self.logger.error('No data to find in self.bins=' + str(self.bins))
        except FileExistsError:
            self.logger.error('The file exists and cannot be replaced')
        except Exception as e:
            self.logger.error('Failed to save data : ' + str(e), exc_info=True)

    def setup_board(self):
        self.setup_pins(self.number_of_levels, self.total_radius)
        self.setup_graph(self.number_of_levels + 1, self.total_radius)
        self.setup_balls()
        self.statistics = None

    def reset_command(self):
        self.logger.info('Resetting')
        self.setup_board()

    def level_slider_command(self):
        self.change_number_of_levels(self.UIComponents['level_slider'].value, set_value=True, percent=True)

    def ball_slider_command(self):
        self.change_number_of_balls(self.UIComponents['ball_slider'].value, set_value=True, percent=True)

    def delay_slider_command(self):
        self.change_delay_between_balls(self.UIComponents['delay_slider'].value, set_value=True, percent=True)

    def speed_slider_command(self):
        self.change_speed(self.UIComponents['speed_slider'].value, set_value=True, percent=True)

    def preset1_command(self):
        self.logger.debug('preset1_command')
        self.load_preset(self.preset_filenames[0])
        self.reset_command()

    def preset2_command(self):
        self.logger.debug('preset2_command')
        self.load_preset(self.preset_filenames[1])
        self.reset_command()

    def preset3_command(self):
        self.logger.debug('preset3_command')
        self.load_preset(self.preset_filenames[2])
        self.reset_command()

    def load_preset(self, filename):
        self.logger.debug('Loading preset from : ' + filename)
        config = configparser.ConfigParser()
        config.read(filename)
        try:
            self.change_number_of_balls(float(self.config_section_map(config, "SectionOne")['number_of_balls']),
                                        set_value=True)
            self.change_speed(float(self.config_section_map(config, "SectionOne")['ball_speed%'])/100,
                              set_value=True, percent=True)
            self.change_delay_between_balls(
                float(self.config_section_map(config, "SectionOne")['delay_between_balls%']) / 100,
                set_value=True, percent=True)
            self.change_number_of_levels(float(self.config_section_map(config, "SectionOne")['number_of_levels']),
                                         set_value=True)
            self.logger.debug('Preset load completed')
        except Exception as e:
            self.logger.error("Cannot load preset file : " + str(e), exc_info=True)
            self.status_bar.add_item('Bad config file : ' + filename)

    def load_preset_labels(self):
        self.logger.debug('Loading preset labels')
        config = configparser.ConfigParser()
        preset_buttons = ['Preset1Button', 'Preset2Button', 'Preset3Button']
        try:
            for filename, button in zip(self.preset_filenames, preset_buttons):
                config.read(filename)
                self.UIComponents[button].label = self.config_section_map(config, "SectionOne")['label']
        except Exception as e:
            self.logger.error('Failed to load preset labels : ' + str(e), exc_info=True)
            self.status_bar.add_item('Bad config file or button name')

    def config_section_map(self, config, section):
        dict1 = {}
        options = config.options(section)
        for option in options:
            try:
                dict1[option] = config.get(section, option)
            except Exception as e:
                dict1[option] = None
        return dict1

    def on_event(self, event):
        if event.type == QUIT:
            self._running = False
        for element in self.UIComponents:
            self.UIComponents[element].get_event(event)

    def change_speed(self, num, set_value=False, percent=False):
        dt_min = 0.002
        dt_max = 0.03
        value_to_set = self.on_change('speed_input', 'speed_slider', dt_min, dt_max,
                                      num, percent=percent, display_percent=True, set_value=set_value, reverse=True)
        if value_to_set is not None:
            self.delta_time_step = value_to_set

    def change_number_of_balls(self, num, set_value=False, percent=False):
        number_of_balls_max = 1000
        number_of_balls_min = 0
        value_to_set = self.on_change('ball_input', 'ball_slider', number_of_balls_min, number_of_balls_max,
                                      num, percent=percent, set_value=set_value)
        if value_to_set is not None:
            if self.paused:
                self.number_of_balls = 0
            else:
                self.number_of_balls = int(value_to_set)

    def change_delay_between_balls(self, num, set_value=False, percent=False):
        delay_between_balls_min = 0
        delay_between_balls_max = 1
        value_to_set = self.on_change('delay_input', 'delay_slider', delay_between_balls_min, delay_between_balls_max,
                                      num, percent=percent, display_percent=True, set_value=set_value)
        if value_to_set is not None:
            self.delay_time = value_to_set

    def change_number_of_levels(self, num, set_value=False, percent=False):
        number_of_levels_max = 40
        number_of_levels_min = 1

        value_to_set = self.on_change('level_input', 'level_slider', number_of_levels_min, number_of_levels_max, num,
                                      percent=percent, set_value=set_value)
        if value_to_set is not None:
            self.number_of_levels = int(value_to_set)
            if self.number_of_levels <= 20:
                self.pin_radius = 8
            else:
                self.pin_radius = 8 - int(5 - (40 - self.number_of_levels) / 5)

            tmp_ball = GaltonBall(1)
            self.total_radius = tmp_ball.radius + self.pin_radius
            self.reset_command()

    def on_change(self, textbox, slider, minimum, maximum, value, percent=False, display_percent=False,
                  set_value=False, reverse=False):
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
                        self.UIComponents[textbox].buffer = \
                            list(str(int(round(100*(value_to_set-minimum)/value_range, 1))))
                    else:
                        self.UIComponents[textbox].buffer = list(str(int(value_to_set)))
                    self.UIComponents[slider].value = float(float(value_to_set)-minimum)/value_range

        except Exception as e:
            self.logger.error('on_change failed : ' + str(e), exc_info=True)
        if reverse and value_to_set:
            value_to_set = maximum - (value_to_set-minimum)
        return value_to_set

    def setup_balls(self):
        self.logger.debug('Setting up balls')
        self.balls = list()

    def create_ball(self):
        tmp_ball = GaltonBall(self.total_radius)
        tmp_ball.x = self.ball_x_start
        tmp_ball.y = self.ball_y_start
        self.balls.append(tmp_ball)

    def on_loop(self):
        for ball in self.balls:
            ball.update(self.collision_with_pin(ball))
            self.is_ball_off_screen(ball)

        if self.balls:
            if len(self.balls) < self.number_of_balls:
                if time.perf_counter() - self.balls[-1].birth_time > self.delay_time:
                    self.create_ball()
        else:
            if self.number_of_balls != 0:
                self.create_ball()

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

        number_of_results_text = self.font.render('Total Balls : ' + str(self.number_of_results), True,
                                                       ColourPalette.white)
        self._display_surf.blit(number_of_results_text, (20, self.board_height + 10))

        status_text = self.font.render(self.status_bar.current_status(), True, ColourPalette.grey)
        self._display_surf.blit(status_text, (10, self.windowHeight - 30))
        if self.number_of_levels <= 20:
            bin_string = ' | '.join(['{:^2}'.format(tmp_bin.value) for tmp_bin in self.bins])
        else:
            bin_string = "Data only shown for <=20 levels"

        bin_text = self.font2.render(bin_string, True, ColourPalette.white)
        bin_pos = (self.windowWidth / 2.0 - bin_text.get_width() / 2.0)
        self._display_surf.blit(bin_text, (bin_pos, 10))

        if self.statistics and self.is_normal_visible:
            stat_string = ("Mean : " + str(round(self.statistics[0], 2)),
                           "StdDev : " + str(round(self.statistics[1], 2)),
                           "Unexplained data : " + str(("{:3.2f}%".format(self.statistics[2]))))
            for i, stat in enumerate(stat_string):
                stat_text = self.font2.render(stat, True, ColourPalette.white)
                self._display_surf.blit(stat_text, (20, 30 + 20*i))

        self.update_graph()

        for ball in self.balls:
            pygame.draw.circle(self._display_surf, ball.colour, (ball.x, ball.y), ball.radius)

        for element in self.UIComponents:
            self.UIComponents[element].update()
            self.UIComponents[element].draw(self._display_surf)

        pygame.display.update()

    def on_cleanup(self):
        self.logger.info('Cleanup')
        pygame.quit()

    def on_execute(self):
        self.logger.info('Executing main loop')
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

            while accumulator >= self.delta_time_step:
                self.on_loop()
                accumulator -= self.delta_time_step
                t += self.delta_time_step
            self.on_render()
        self.on_cleanup()

    def setup_pins(self, levels, total_radius):
        self.logger.debug('Setting up pins')
        self._board_surf.fill(ColourPalette.black)
        self.pins = list()
        start_y = 80
        start_x = self.ball_x_start
        x = start_x
        y = start_y
        for i in range(1, levels + 1):
            tmp_level = list()
            for j in range(0, i):
                tmp_level.append(GaltonPin(x, y, self.pin_radius))
                x += int(total_radius * 2)
            self.pins.append(tmp_level)
            start_x -= total_radius
            start_y += total_radius * 2
            x = start_x
            y = start_y
        for i in range(0, self.number_of_levels):
            for pin in self.pins[i]:
                pygame.draw.circle(self._board_surf, ColourPalette.pin, (pin.x, pin.y), pin.radius)

    def setup_graph(self, bins, total_radius):
        self.logger.debug('Setting up graph')
        self.bins = list()
        self.number_of_results = 0
        x = self.ball_x_start
        for i in range(0, self.number_of_levels):
            x -= total_radius

        for i in range(0, bins):
            tmp_bin = GaltonBin()
            tmp_bin.trigger = x
            tmp_bin.width = total_radius * 2
            tmp_bin.x = x - total_radius
            self.bins.append(tmp_bin)
            x += total_radius * 2

    def update_graph(self):
        bin_values = [tmp_bin.value for tmp_bin in self.bins]
        bin_max = max(bin_values)
        if bin_max == 0:
            bin_max = 1
        if self.number_of_results:
            for galtonBin in self.bins:
                pygame.draw.rect(self._display_surf,
                                 ColourPalette.graph,
                                 (galtonBin.x, self.board_height, galtonBin.width,
                                  -150 * (galtonBin.value / bin_max)))
        if self.is_normal_visible and self.number_of_results > 1:
            try:
                number_of_bins = self.number_of_levels + 1
                normal_x_axis = np.subtract(range(0, number_of_bins), self.number_of_levels/2)
                mean_estimate = np.sum(np.multiply(normal_x_axis, bin_values))/self.number_of_results
                std_estimate = np.sqrt(np.sum(np.multiply(normal_x_axis, np.multiply(normal_x_axis, bin_values)))
                                       / self.number_of_results - mean_estimate * mean_estimate)
                unexplained_data_percent = np.sum(
                    np.abs(
                        np.subtract(bin_values,
                                    np.multiply(norm.pdf(normal_x_axis, loc=mean_estimate, scale=std_estimate),
                                                self.number_of_results))))\
                                           * 100 / self.number_of_results

                self.statistics = (mean_estimate, std_estimate, unexplained_data_percent)
                if not np.isnan(mean_estimate) and not np.isnan(std_estimate) and std_estimate > 0:
                    norm_max = norm.pdf(0, loc=0, scale=std_estimate)
                    for x_point, norm_point in zip(np.linspace(self.bins[0].x+self.bins[0].width/2,
                                                               self.bins[-1].x+self.bins[-1].width/2,
                                                               (number_of_bins*2)),
                                                   np.linspace(-0.5*(self.number_of_levels+1),
                                                               0.5*(self.number_of_levels+1),
                                                               (number_of_bins*2))):
                        pygame.draw.circle(self._display_surf,
                                           ColourPalette.red,
                                           (int(x_point),
                                            int(self.board_height-150*norm.pdf(norm_point,
                                                                               loc=mean_estimate,
                                                                               scale=std_estimate)/norm_max)),
                                           3)

                    # points = [(x_point, norm_point) for x_point, norm_point
                        # in zip(np.linspace(self.bins[0].x+self.bins[0].width/2,
                        #  self.bins[-1].x+self.bins[-1].width/2,
                        #  (number_of_bins*2)),
                        #  np.linspace(-0.5*(self.number_of_levels+1),
                        #  0.5*(self.number_of_levels+1), (number_of_bins)*2))]
                    # pygame.draw.lines(self._display_surf, ColourPalette.red, False, points, 2)
            except Exception as e:
                self.logger.error("Calculation of Normal statistics has failed with error : " + str(e), exc_info=True)

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
    change_colour = False

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
        self.birth_time = time.perf_counter()
        self.colour = ColourPalette.ball
        # For fun
        # self.colour = pygame.Color(random.randint(0,255), random.randint(0,255), random.randint(0,255),255)

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
        prev_animation = (0, 0)
        animation = (0, 0)
        for i in np.linspace(1, self.total_radius, self.total_radius/self.y_speed):
            difference = np.subtract(animation, prev_animation)
            self._animation_frames.append([int(a) for a in difference])
            prev_animation = np.subtract(animation, np.subtract(difference, [int(a) for a in difference]))
            animation = (np.sqrt(self.total_radius ** 2 - (self.total_radius - i) ** 2), i)
        difference = np.subtract(animation, prev_animation)
        self._animation_frames.append([int(a) for a in difference])


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
