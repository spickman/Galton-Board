import pygame
import numpy as np
import random
import time
from pygame.locals import *
from TextBox import TextBox
from Button import Button
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
        self.x_start = int(self.windowWidth/2)
        self._running = True
        self._display_surf = None
        self._board_surf = None
        self.number_of_levels = 20

        self.pin_size = 8

        tmpball = GaltonBall(0)
        self.total_radius = self.pin_size + tmpball.radius

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
        self.number_of_results_text = self.font.render('Total Balls : ' + str(self.number_of_results), True, pygame.Color('white'))
        self.bin_text = self.font2.render(''.join([str(bin.value) for bin in self.bins]), True, pygame.Color('white'))

        self.status = 'Running'
        self.status_text = self.font.render('', True, pygame.Color('darkgrey'))

        self.UIComponents = list()
        self.ballinput = TextBox((400, self.board_height+40, 100, 20), command=self.change_number_of_balls,
                             clear_on_enter=False, inactive_on_enter=False, label="Number of balls")

        self.speedinput = TextBox((400, self.board_height+100, 100, 20), command=self.change_speed_of_balls,
                             clear_on_enter=False, inactive_on_enter=False, percentage=True, label="Ball delay")

        self.levelinput = TextBox((400, self.board_height+10, 100, 20), command=self.change_number_of_levels,
                             clear_on_enter=False, inactive_on_enter=False, label="Number of levels")

        self.dtinput = TextBox((400, self.board_height+70, 100, 20), command=self.change_dt,
                             clear_on_enter=False, inactive_on_enter=False, percentage=True, label="Ball speed")

        self.resetbutton = Button((600, self.board_height+10, 100, 20), command=self.reset_command, label="Reset")
        self.pausebutton = Button((720, self.board_height+10, 100, 20), command=self.pause_command, label="Pause", latching_label="Continue", active_color=pygame.Color("darkred"))
        self.preset1button = Button((600, self.board_height+40, 100, 20), command=self.preset1_command, label="Preset1")
        self.preset2button = Button((600, self.board_height+70, 100, 20), command=self.preset2_command, label="Preset2")
        self.preset3button = Button((600, self.board_height+100, 100, 20), command=self.preset3_command, label="Preset3")

        self.change_dt(-1)
        self.change_number_of_balls(-1)
        self.change_number_of_levels(-1)
        self.change_speed_of_balls(-1)
        self.load_preset_labels()
        self.setup_board()

    def pause_command(self):
        if self.paused:
            self.paused = False
            self.change_number_of_balls(self.unpause_number_of_balls, set=True)
            self.unpause_number_of_balls = None
        else:
            self.unpause_number_of_balls = self.number_of_balls
            self.change_number_of_balls(0, set=False)
            self.paused = True

    def setup_board(self):
        self.setup_pins(self.number_of_levels, self.total_radius)
        self.setup_graph(self.number_of_levels+1, self.total_radius)
        self.setup_balls()

    def reset_command(self):
        print("Resetting")
        self.setup_board()

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
            self.change_number_of_balls(self.ConfigSectionMap(config, "SectionOne")['number_of_balls'], set=True)
            self.change_dt(self.ConfigSectionMap(config, "SectionOne")['speed_of_balls%'], set=True)
            self.change_speed_of_balls(self.ConfigSectionMap(config, "SectionOne")['ball_delay%'], set=True)
            self.change_number_of_levels(self.ConfigSectionMap(config, "SectionOne")['number_of_levels'], set=True)
        except:
            self.status = 'Bad config file : ' + filename

    def load_preset_labels(self):
        config = configparser.ConfigParser()
        config.read('preset1config.ini')
        self.preset1button.label = self.ConfigSectionMap(config, "SectionOne")['label']
        config.read('preset2config.ini')
        self.preset2button.label = self.ConfigSectionMap(config, "SectionOne")['label']
        config.read('preset3config.ini')
        self.preset3button.label = self.ConfigSectionMap(config, "SectionOne")['label']


    def ConfigSectionMap(self, config, section):
        dict1 = {}
        options = config.options(section)
        for option in options:
            try:
                dict1[option] = config.get(section, option)
                if dict1[option] == -1:
                    print("skip: %s" % option)
            except:
                print("exception on %s!" % option)
                dict1[option] = None
        return dict1

    def on_event(self, event):
        if event.type == QUIT:
            self._running = False
        self.ballinput.get_event(event)
        self.speedinput.get_event(event)
        self.levelinput.get_event(event)
        self.dtinput.get_event(event)
        self.resetbutton.get_event(event)
        self.preset1button.get_event(event)
        self.preset2button.get_event(event)
        self.pausebutton.get_event(event)
        self.preset3button.get_event(event)

    def change_dt(self, num, set=False):
        dt_min = 0.002
        dt_max = 0.03
        dt_range = dt_max - dt_min
        try:
            if 0 <= int(num) <= 100:
                self.dt = dt_max - dt_range * float(num)/100
                if set:
                    self.dtinput.buffer = list(str(num))
            else:
                self.dtinput.buffer = list(str(int((dt_max - self.dt)*100/dt_range)))
        except:
            self.dtinput.buffer = list(str(int((dt_max - self.dt)*100/dt_range)))
        finally:
            pass

    def change_number_of_balls(self, num, set=False):
        number_of_balls_max = 1000
        number_of_balls_min = 0
        try:
            if number_of_balls_min <= int(num) <= number_of_balls_max:
                if self.paused:
                    self.unpause_number_of_balls = int(num)
                else:
                    self.number_of_balls = int(num)
                if set:
                    self.ballinput.buffer = list(str(int(num)))
            else:
                self.ballinput.buffer = list(str(int(self.number_of_balls)))
        except:
            self.ballinput.buffer = list(str(int(self.number_of_balls)))
        finally:
            pass

    def change_speed_of_balls(self, num, set=False):
        speed_of_balls_min = 0
        speed_of_balls_max = 99
        speed_of_balls_range = speed_of_balls_max - speed_of_balls_min
        try:
            if 0 <= int(num) <= 100:
                self.delay_time = speed_of_balls_min + speed_of_balls_range * float(num)/100
                if set:
                    self.speedinput.buffer = list(str(num))
            else:
                self.speedinput.buffer = list(str(int((speed_of_balls_min+self.delay_time)*100/speed_of_balls_range)))
        except:
            self.speedinput.buffer = list(str(int((speed_of_balls_min+self.delay_time)*100/speed_of_balls_range)))
        finally:
            pass

    def change_number_of_levels(self, num, set=False):
        number_of_levels_max = 40
        number_of_levels_min = 1
        try:
            if number_of_levels_min <= int(num) <= number_of_levels_max:
                self.number_of_levels = int(num)
                if self.number_of_levels <= 20:
                    self.pin_size = 8
                else:
                    self.pin_size = 8 - int(5 - (40 - self.number_of_levels) / 5)
                    print(self.pin_size)

                tmpball = GaltonBall(1)
                self.total_radius = tmpball.radius + self.pin_size
                self.reset_command()

                if set:
                    self.levelinput.buffer = list(str(int(num)))
            else:
                self.levelinput.buffer = list(str(self.number_of_levels))
        except:
            self.levelinput.buffer = list(str(self.number_of_levels))
        finally:
            pass

    def setup_balls(self):
        self.balls = list()

    def create_ball(self):
        tmpBall = GaltonBall(self.total_radius)
        tmpBall.x = self.x_start
        self.balls.append(tmpBall)

    def on_loop(self):

        for ball in self.balls:
            ball.update(self.collision_with_pin(ball))
            self.isBallOffScreen(ball)

        if len(self.balls) < self.number_of_balls:
            if self.ball_delay < 0:
                self.create_ball()
                self.ball_delay = self.delay_time

        self.ball_delay -= 1

    def isBallOffScreen(self, ball):
        if ball.y > self.board_height:
            for tmpbin in self.bins:
                if tmpbin.trigger == ball.x:
                    tmpbin.value += 1
                    self.number_of_results += 1
                    break
            self.balls.remove(ball)

    def on_render(self):
        self._display_surf.fill(pygame.Color('black'))
        self._display_surf.blit(self._board_surf, (0, 0))

        self.number_of_results_text = self.font.render('Total Balls : ' + str(self.number_of_results), True, pygame.Color('white'))
        self._display_surf.blit(self.number_of_results_text, (20, self.board_height+10))

        self.status_text = self.font.render(self.status, True, pygame.Color('darkgrey'))
        self._display_surf.blit(self.status_text, (10, self.windowHeight-30))
        if self.number_of_levels <= 20:
            bin_string = ' | '.join(['{:^2}'.format(bin.value) for bin in self.bins])
        else:
            bin_string = "Data only shown for <=20 levels"

        self.bin_text = self.font2.render(bin_string, True, pygame.Color('white'))
        bin_pos = (self.windowWidth/2.0 - self.bin_text.get_width()/2.0)
        self._display_surf.blit(self.bin_text, (bin_pos, 10))

        self.update_graph()

        for ball in self.balls:
            pygame.draw.circle(self._display_surf, (255, 255, 255), (ball.x, ball.y), ball.radius)

        self.ballinput.update()
        self.speedinput.update()
        self.levelinput.update()
        self.dtinput.update()
        self.resetbutton.update()
        self.preset1button.update()
        self.preset2button.update()
        self.pausebutton.update()
        self.preset3button.update()


        self.ballinput.draw(self._display_surf)
        self.speedinput.draw(self._display_surf)
        self.levelinput.draw(self._display_surf)
        self.dtinput.draw(self._display_surf)
        self.resetbutton.draw(self._display_surf)
        self.preset2button.draw(self._display_surf)
        self.preset1button.draw(self._display_surf)
        self.pausebutton.draw(self._display_surf)
        self.preset3button.draw(self._display_surf)
        pygame.display.update()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        accumulator = 0.0
        t = 0.0
        current_time = time.clock() - 1

        while self._running:
            new_time = time.clock()
            frame_time = new_time - current_time
            current_time = time.clock()

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
        self._board_surf.fill(pygame.Color("black"))
        self.pins = list()
        start_y = 80
        start_x = self.x_start
        x = start_x
        y = start_y
        for i in range(1, levels+1):
            tmplevel = list()
            for j in range(0, i):
                tmplevel.append(GaltonPin(x, y, self.pin_size))
                x += int(total_radius*2)
            self.pins.append(tmplevel)
            start_x -= total_radius
            start_y += total_radius*2
            x = start_x
            y = start_y
        for i in range(0, self.number_of_levels):
            for pin in self.pins[i]:
                pygame.draw.circle(self._board_surf, (100, 100, 100), (pin.x, pin.y), pin.radius)

    def setup_graph(self, bins, total_radius):
        self.bins = list()
        self.number_of_results = 0
        x = self.x_start
        for i in range(0, self.number_of_levels):
            x -= total_radius

        for i in range(0, bins):
            tmpbin = GaltonBin()
            tmpbin.trigger = x
            tmpbin.width = total_radius*2
            tmpbin.x = x - total_radius
            self.bins.append(tmpbin)
            x += total_radius *2

    def update_graph(self):
        x = 0
        bin_max = max(bin.value for bin in self.bins)
        if bin_max == 0:
            bin_max = 1
        for galtonBin in self.bins:
            pygame.draw.rect(self._display_surf, (0, 128, 255), (galtonBin.x, self.board_height, galtonBin.width, -1*(125/bin_max)*(galtonBin.value)))

    def collision_with_pin(self, ball):
        if ball.level < self.number_of_levels:
            pin = self.pins[ball.level][ball.nextpin]
            if pin.x == ball.x and (pin.y-self.total_radius) == ball.y:
                return True
            if pin.x == ball.x and (pin.y-self.total_radius) < ball.y:
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
        self.animation_frames = list()
        self.animation_direction = 0
        self.level = 0
        self.nextpin = 0
        self.y_speed = 1
        self.total_radius = total_radius
        self.setup_animation()
        self.animation_frame = len(self.animation_frames)

    def update(self, collision):

        if self.animation_frame < len(self.animation_frames):
            if self.animation_direction == 0:
                self.x += self.animation_frames[self.animation_frame][0]
            elif self.animation_direction == 1:
                self.x -= self.animation_frames[self.animation_frame][0]

            self.y += self.animation_frames[self.animation_frame][1]
            self.animation_frame += 1

        elif collision:
            self.animation_frame = 0
            self.level += 1
            self.animation_direction = random.randint(0, 1)
            if self.animation_direction == 0:
                self.nextpin += 1
        else:
            self.y += self.y_speed

    def setup_animation(self):
        prev_x_animation = 0
        x_animation = np.sqrt(self.total_radius ** 2 - (self.total_radius - 0) ** 2)
        for i in range(1, self.total_radius+2, 1):
            x_difference = x_animation - prev_x_animation
            self.animation_frames.append((int(x_difference), 1))
            prev_x_animation = x_animation - (x_difference - int(x_difference))
            x_animation = np.sqrt(self.total_radius ** 2 - (self.total_radius - i) ** 2)


class GaltonPin:
    def __init__(self, x, y, pin_size):
        self.x = x
        self.y = y
        self.radius = pin_size


if __name__ == "__main__":
    theApp = App()
    theApp.on_execute()