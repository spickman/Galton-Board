import pygame as pg

class Slider(object):
    def __init__(self, rect, **kwargs):
        self.rect = pg.Rect(rect)
        self.rendered = None
        self.rendered_bar = None
        self.trigger_rect = None
        self.active = False
        self.value = 0.4
        self.process_kwargs(kwargs)
        self.setup_bars()
        self.update_trigger()

    def process_kwargs(self, kwargs):
        defaults = {'id': None,
                    'color': pg.Color('grey'),
                    'trigger_width': 10,
                    'bar_height': int(self.rect.height/6),
                    'value': 0.4
                    }
        for kwarg in kwargs:
            if kwarg in defaults:
                defaults[kwarg] = kwargs[kwarg]
            else:
                raise KeyError("Slider does not accept keyword {}.".formate(kwarg))
        self.__dict__.update(defaults)

    def get_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.x + self.trigger_rect.x < event.pos[0] < self.rect.x + self.trigger_rect.x + self.trigger_rect.width \
                    and self.rect.y < event.pos[1] < self.rect.y + self.trigger_rect.height:
                self.active = True
        elif self.active and event.type == pg.MOUSEBUTTONUP:
            self.active = False

    def execute(self):
        pass

    def update_value(self):
        if self.active:
            self.value = (pg.mouse.get_pos()[0] - self.rect.x - self.trigger_rect.width/2) / self.rect.width
            if self.value > 1:
                self.value = 1
            elif self.value < 0:
                self.value = 0

    def update_trigger(self):
        self.trigger_rect = pg.Rect((int(self.value*self.rect.width - self.trigger_width/2), 0, self.trigger_width,
                                     self.rect.height))

    def setup_bars(self):
        self.rendered_bar = pg.Surface((self.rect.width, self.rect.height))
        #self.rendered_bar.fill(pg.Color('white')) # For Testing Only
        pg.draw.rect(self.rendered_bar, pg.Color('red'), (0, int(self.rect.height/2 - self.bar_height/2),
                                                          self.rect.width, self.bar_height))

    def update(self):
        self.update_value()
        self.update_trigger()
        pass

    def draw(self, surface):
        self.rendered = pg.Surface((self.rect.width, self.rect.height))
        self.rendered.blit(self.rendered_bar, (0, 0))
        pg.draw.rect(self.rendered, pg.Color('blue'), self.trigger_rect)
        if self.rendered:
            surface.blit(self.rendered, (self.rect.x, self.rect.y))

