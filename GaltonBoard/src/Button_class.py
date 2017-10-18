import string
import pygame as pg

class Button(object):
    def __init__(self, rect, **kwargs):
        self.rect = pg.Rect(rect)
        self.buffer = []
        self.final = None
        self.rendered = None
        self.render_rect = None
        self.render_area = None
        self.process_kwargs(kwargs)

    def process_kwargs(self,kwargs):
        defaults = {"id": None,
                    "command": None,
                    "active": False,
                    "color": pg.Color("grey"),
                    "font_color": pg.Color("black"),
                    "outline_color": pg.Color("grey"),
                    "outline_width": 2,
                    "active_color": pg.Color("blue"),
                    "font": pg.font.Font(None, self.rect.height+4),
                    "label": "Button",
                    "latching_label": None}
        for kwarg in kwargs:
            if kwarg in defaults:
                defaults[kwarg] = kwargs[kwarg]
            else:
                raise KeyError("InputBox accepts no keyword {}.".format(kwarg))
        self.__dict__.update(defaults)

    def get_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.x < event.pos[0] < self.rect.x + self.rect.width and self.rect.y < event.pos[1] < self.rect.y + self.rect.height:
                if self.latching_label:
                    if self.active == True:
                        self.active = False
                    else:
                        self.active = True
                else:
                    self.active = True
                self.execute()
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            if self.rect.x < event.pos[0] < self.rect.x + self.rect.width and self.rect.y < event.pos[1] < self.rect.y + self.rect.height:
                if not self.latching_label:
                    self.active = False

    def execute(self):
        if self.command:
            self.command()

    def update(self):
        if self.latching_label:
            self.rendered = self.font.render(self.latching_label if self.active else self.label, True, self.active_color if self.active else self.font_color)
        else:
            self.rendered = self.font.render(self.label, True, self.active_color if self.active else self.font_color)

        self.render_rect = self.rendered.get_rect(x=self.rect.x, center=self.rect.center)

    def draw(self, surface):
        outline_color = self.outline_color
        outline = self.rect.inflate(self.outline_width*2, self.outline_width*2)
        surface.fill(outline_color, outline)
        surface.fill(self.color, self.rect)
        if self.rendered:
            surface.blit(self.rendered, self.render_rect, self.render_area)
