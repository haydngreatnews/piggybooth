import os
import time

## Grab the backported enums from python3.4
from enum import Enum

import piggyphoto
import pygame
from pygame.locals import *

PREVIEW = '/mnt/tmp/preview.jpg'
STORE_DIR = 'images'
SAVE_PREFIX = 'Booth'
CAPTION = "Python Photobooth"
READY_WAIT = 5      # seconds for the 'Get Ready!' prompt
COUNTDOWN_WAIT = 1  # seconds between 3..2..1
SHOT_COUNT = 3

class BoothState(Enum):
    waiting = 1
    shooting = 2
    email = 3
    thanks = 4
    quit = 5


class ShootPhase(Enum):
    get_ready = 4
    countdown_three = 3
    countdown_two = 2
    countdown_one = 1
    shoot = 5

    def next(self):
        if self == ShootPhase.shoot:
            return ShootPhase.countdown_three
        elif self == ShootPhase.countdown_one:
            return ShootPhase.shoot
        return ShootPhase(self.value - 1)


class BoothView(object):

    def __init__(self, width=640, height=480, fps=10, fullscreen=False):
        """Initialize the bits"""
        pygame.init()
        pygame.display.set_caption(CAPTION)
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)
        self.background = pygame.Surface(self.screen.get_size()).convert()
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.countdown = 3000
        self.small_font = pygame.font.SysFont('Arial', 20, bold=True)
        self.large_font = pygame.font.SysFont('Arial', 40, bold=True)
        self.huge_font = pygame.font.SysFont('Arial', 150, bold=True)

        self.camera = piggyphoto.camera()
        self.camera.leave_locked()
        self.camera.capture_preview(PREVIEW)

        self.state = BoothState.waiting
        self.shoot_phase = ShootPhase.get_ready
        self.phase_start = time.time()
        self.shots_left = SHOT_COUNT
        self.counter = 0
        self.pid = os.getpid()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RETURN and self.state == BoothState.waiting:
                        self.switch_state(BoothState.shooting)
            if self.state == BoothState.waiting:
                self.wait_state()
            elif self.state == BoothState.shooting:
                self.shoot_state()
            elif self.state in (BoothState.email, BoothState.thanks):
                # Just quit for now
                self.switch_state(BoothState.waiting)

            self.clock.tick(self.fps)
            pygame.display.set_caption("{} FPS: {:6.3}".format(CAPTION, self.clock.get_fps()))
            pygame.display.flip()

        pygame.quit()

    def wait_state(self):
        # Maybe add some fancy image processing?
        self.update_image()
        self.draw_centered_text('PRESS THE BIG RED BUTTON TO START', self.large_font, outline=True)

    def shoot_state(self):
        self.update_image()
        frame_time = time.time()
        if frame_time > self.phase_start + self.countdown:
            self.phase_start = time.time()
            if self.shoot_phase != ShootPhase.shoot:
                self.countdown = COUNTDOWN_WAIT
                self.shoot_phase = self.shoot_phase.next()
            else:
                if self.shots_left:
                    self.camera.capture_image(os.path.join(STORE_DIR, '{0}{1}-{2:05d}.jpg'.format(SAVE_PREFIX, self.pid, self.counter)))
                    self.counter += 1
                    self.shots_left -= 1
                    self.shoot_phase = self.shoot_phase.next()
                    # Add a double time to allow for the shot time
                    self.countdown = COUNTDOWN_WAIT * 2
                    if not self.shots_left:
                        self.switch_state(BoothState.email)
        if self.shoot_phase == ShootPhase.get_ready:
            self.draw_centered_text('Get Ready!', self.huge_font, outline=True)
        elif self.shoot_phase != ShootPhase.shoot:
            self.draw_centered_text(str(self.shoot_phase.value), self.huge_font, outline=True)

    def update_image(self):
        self.camera.capture_preview(PREVIEW)
        picture = pygame.image.load(PREVIEW)
        picture = pygame.transform.scale(picture, (self.width, self.height))
        self.screen.blit(picture, (0,0))

    def draw_centered_text(self, text, font=None, color=(255,255,255), outline=False):
        """Center text in window"""
        if font == None:
            font = self.small_font
        fw, fh = font.size(text)
        if outline:
            textobj = font.render(text, True, (0,0,0))
            for xoffset in (-1,1):
                for yoffset in (-1,1):
                    textpos = textobj.get_rect(centerx=self.background.get_width()/2 + xoffset, centery=self.background.get_height()/2 + yoffset)
                    self.screen.blit(textobj, textpos)
        textobj = font.render(text, True, color)
        textpos = textobj.get_rect(centerx=self.background.get_width()/2, centery=self.background.get_height()/2)
        self.screen.blit(textobj, textpos)

    def switch_state(self, target):
        if target == BoothState.shooting:
            self.countdown = READY_WAIT
            self.fps = 60  # This is a placeholder for infinity in this case...
            self.shoot_phase = ShootPhase.get_ready
            self.shots_left = SHOT_COUNT
            self.phase_start = time.time()

        self.state = target

if __name__ == '__main__':
    if not os.path.exists(STORE_DIR):
        os.mkdir(STORE_DIR)
    BoothView().run()


def quit_pressed():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
    # Don't quit... someone might be messing around
    return False
