import os
import time

import piggyphoto
import pygame
from pygame.locals import *

COUNTDOWN = 3
PREVIEW = '/tmp/preview.jpg'
MAX_FPS = 8

class BoothView(object):


  def __init__(self, width=640, height=480, fps=10, fullscreen=False):
    """Initialize the bits"""
    pygame.init()
    pygame.display.set_caption("Python Photobooth")
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

  def run(self):
    running = True
    while running:
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          running = False
        elif event.type == pygame.KEYDOWN:
          if event.key == pygame.K_ESCAPE:
            running = False
      milliseconds = self.clock.tick(self.fps)
      self.playtime += milliseconds / 1000.0
      self.update_image()
      self.draw_text("FPS: {:6.3}{}PLAYTIME: {:6.3} SECONDS".format(self.clock.get_fps(), " "*5, self.playtime))
      pygame.display.flip()
      self.screen.blit(self.background, (0,0))

    pygame.quit()

  def update_image(self):
    self.camera.capture_preview(PREVIEW)
    picture = pygame.image.load(PREVIEW)
    self.background.blit(picture, (0,0))

  def draw_text(self, text):
    """Center text in window"""
    fw, fh = self.font.size(text)
    surface = self.font.render(text, True, (0,255,0))
    self.screen.blit(surface, ((self.width - fw) / 2, (self.height - fh) / 2))

if __name__ == '__main__':
  BoothView().run()


def quit_pressed():
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
        return True
  # Don't quit... someone might be being a dickhead
  return False
