import os
import time

## Grab the backported enums from python3.4
from enum import Enum

import piggyphoto
import pygame
from pygame.locals import *

COUNTDOWN = 3
PREVIEW = '/mnt/tmp/preview.jpg'
MAX_FPS = 8
CAPTION = "Python Photobooth"
WAITING = 'waiting'
BEGIN = 'begin'
QUIT = 'quit'

class BoothState(Enum):
  waiting = 1
  shooting = 2
  quit = 3


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
    self.playtime = 0.0
    self.font = pygame.font.SysFont('Arial', 20, bold=True)

    self.camera = piggyphoto.camera()
    self.camera.leave_locked()
    self.camera.capture_preview(PREVIEW)

    self.state = BoothState.waiting

  def run(self):
    running = True
    while running:
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          running = False
        elif event.type == pygame.KEYDOWN:
          if event.key == pygame.K_ESCAPE:
            running = False
      milliseconds = self.clock.tick()
      self.playtime += milliseconds / 1000.0
      self.update_image()
      pygame.display.set_caption("{} FPS: {:6.3}".format(CAPTION, self.clock.get_fps()))
      pygame.display.flip()
      #self.screen.blit(self.background, (0,0))

    pygame.quit()

  def wait_state(self):
    for event in pygame.event.get():
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ENTER:
          self.state = BoothState.shooting
    self.update_image()
    self.draw_centered_text('PRESS THE BIG RED BUTTON TO START')



  def update_image(self):
    self.camera.capture_preview(PREVIEW)
    picture = pygame.image.load(PREVIEW)
    picture = pygame.transform.scale(picture, (self.width, self.height))
    self.screen.blit(picture, (0,0))

  def draw_centered_text(self, text):
    """Center text in window"""
    fw, fh = self.font.size(text)
    textobj = self.font.render(text, True, (255,255,255))
    textpos = textobj.get_rect(centerx=self.background.get_width()/2, centery=self.background.get_height()/2)
    self.screen.blit(textobj, textpos)

if __name__ == '__main__':
  BoothView().run()


def quit_pressed():
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
        return True
  # Don't quit... someone might be messing around
  return False
