import os
import time

import piggyphoto
import pygame
from pygame.locals import *

COUNTDOWN = 3
PREVIEW = '/tmp/preview.jpg'
MAX_FPS = 8

def quit_pressed():
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
        return True
  # Don't quit... someone might be being a dickhead
  return False

def show(file):
  picture = pygame.image.load(file)
  main_surface.blit(picture, (0,0))
  pygame.display.flip()
  text = "FPS: {0:.2f}".format(clock.get_fps())
  clock.tick()
  pygame.display.set_caption(text)

C = piggyphoto.camera()
C.leave_locked()
C.capture_preview(PREVIEW)

picture = pygame.image.load(PREVIEW)
pygame.display.set_mode(picture.get_size())
main_surface = pygame.display.get_surface()
clock = pygame.time.Clock()

while not quit_pressed():
  C.capture_preview(PREVIEW)
  show(PREVIEW)
