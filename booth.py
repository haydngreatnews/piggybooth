import os
import time
import shutil
import io
import email
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
import smtplib
import threading

## Grab the backported enums from python3.4
from enum import Enum

import piggyphoto
import pygame
from pygame.locals import *
import easygui
import PIL
import serial
import numpy
from scipy import ndimage

PREVIEW = '/mnt/tmp/preview.jpg'
STORE_DIR = 'images'
SAVE_PREFIX = 'Booth'
STRIP_SUFFIX = 'Strip'
CAPTION = "Python Photobooth"
FROM_ADDR = 'auto-mailer@newport.net.nz'
READY_WAIT = 5  # seconds for the 'Get Ready!' prompt
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
    def __init__(self, width=512, height=640, fps=5, fullscreen=True):
        """Initialize the bits"""
        pygame.init()
        pygame.display.set_caption(CAPTION)
        self.width = width
        self.height = height
        self.screen = None
        self.fullscreen = fullscreen
        if fullscreen:
            self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
            (self.width, self.height) = self.screen.get_size()
        else:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)
        self.background = pygame.Surface(self.screen.get_size()).convert()
        self.clock = pygame.time.Clock()
        self.base_fps = fps
        self.fps = fps
        self.countdown = READY_WAIT
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
        self.shot_counter = 0
        self.session_counter = 1
        self.images = []
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
                elif event.type == pygame.USEREVENT:
                    if event.action == 'button_pressed' and self.state == BoothState.waiting:
                        print('Actioning event from serial')
                        self.switch_state(BoothState.shooting)
            if not running:
                break
            if self.state == BoothState.waiting:
                self.wait_state()
            elif self.state == BoothState.shooting:
                self.shoot_state()
            elif self.state == BoothState.email:
                self.collect_email()
            elif self.state == BoothState.thanks:
                # Just quit for now
                self.switch_state(BoothState.waiting)

            self.clock.tick(self.fps)
            pygame.display.set_caption("{} FPS: {:6.3}".format(CAPTION, self.clock.get_fps()))
            pygame.display.flip()
        print('Exiting main loop')
        pygame.quit()

    def wait_state(self):
        # Maybe add some fancy image processing?
        self.update_image(blur=True)
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
                    filename = os.path.join(STORE_DIR, '{0}{1}-{2:04d}{3:02d}.jpg'.format(SAVE_PREFIX, self.pid,
                                                                                          self.session_counter,
                                                                                          self.shot_counter))
                    self.camera.capture_image(filename)
                    self.images.append(filename)
                    self.shot_counter += 1
                    self.shots_left -= 1
                    self.shoot_phase = self.shoot_phase.next()
                    # Add a double time to allow for the shot time
                    self.countdown = COUNTDOWN_WAIT * 2
                    if self.shots_left == 0:
                        self.switch_state(BoothState.email)
                        return
        if self.shoot_phase == ShootPhase.get_ready:
            self.draw_centered_text('Get Ready!', self.huge_font, outline=True)
        elif self.shoot_phase != ShootPhase.shoot:
            self.draw_centered_text(str(self.shoot_phase.value), self.huge_font, outline=True)

    def collect_email(self):
        start = time.time()
        strip_file = self.generate_strip()
        finish = time.time()
        print('Strip generation started {0}, finished {1}, elapsed {2}. Output {3}'.format(start, finish, finish - start, strip_file))
        if self.fullscreen:
            pygame.display.toggle_fullscreen()
        email = easygui.enterbox(
            "Enter your email address if you'd like a copy sent to you:",
            "Enter your email",
            ""
        )
        print(email)
        send_email = True
        if email is None or email.endswith('example.com'):
            send_email = False
        elif email in ('null@catalyst.net.nz', ''):
            send_email = False

        if send_email:
            email_thread = threading.Thread(target=BoothView.send_strip, args=[email, strip_file])
            email_thread.start()

        if self.fullscreen:
            pygame.display.toggle_fullscreen()
        self.switch_state(BoothState.thanks)

    def update_image(self, source=None, blur=False):
        if source is None:
            camera_file = self.camera.capture_preview()
            camera_file.save(PREVIEW)
            camera_file.__dealoc__(PREVIEW)

        picture = pygame.image.load(PREVIEW)
        (width, height) = picture.get_size()
        new_width = self.height*(float(width)/height)
        picture = pygame.transform.scale(picture, (int(new_width), self.height))
        # Smoothscale looks better, but is a ~30% speed hit
        # picture = pygame.transform.smoothscale(picture, (int(new_width), self.height))
        lr_crop = (new_width - self.width)/2
        if blur:
            surface_array = pygame.surfarray.pixels3d(picture)
            # Do the resize simultaneously with adding the shade
            surface_array = surface_array[:][lr_crop:new_width-lr_crop] / 2  # Gives appearance of dark overlay, ~30% speed hit
            lr_crop = 0
            # sigma = 3
            # Nice blur effect, but ~75% speed hit
            # surface_array = ndimage.filters.gaussian_filter(
            #     surface_array,
            #     sigma=(sigma, sigma, 0),
            #     order=0,
            #     mode='reflect'
            # )
            picture = pygame.surfarray.make_surface(surface_array)
        self.screen.blit(picture, (-lr_crop, 0))

    def generate_strip(self):
        canvas = PIL.Image.open('photobooth_template.jpg')
        i = 0
        piece_dims = (833, 533)
        for pos in [(60,60), (907,60), (60,607)]:
            img = PIL.Image.open(self.images[i])
            (iwidth, iheight) = img.size
            # Snip the left and right strips so it's the right proportions
            iratio = float(iwidth)/iheight
            new_height = int(round(piece_dims[0] / iratio))
            img = img.resize((piece_dims[0], new_height), resample=PIL.Image.BICUBIC)
            img = img.crop((0, (new_height - piece_dims[1])/2, piece_dims[0], piece_dims[1] + (new_height - piece_dims[1])/2))
            canvas.paste(img, box=pos)
            i += 1
        strip_file = os.path.join(STORE_DIR, '{0}{1}-{2:04d}-{3}.jpg'.format(SAVE_PREFIX, self.pid, self.session_counter, STRIP_SUFFIX))
        canvas.save(strip_file)
        return strip_file

    @staticmethod
    def send_strip(email_addr, filepath):
        start = time.time()
        msg = MIMEMultipart()
        msg['From'] = FROM_ADDR
        msg['To'] = email_addr
        msg['Subject'] = 'Your Photobooth Strip!'
        body = 'Thanks for coming along to our party!\nYour photobooth strip is attached'
        msg.attach(MIMEText(body, 'plain'))
        img = open(filepath, 'rb')
        mime_image = MIMEImage(img.read())
        mime_image.add_header('Content-Disposition', 'attachment', filename=os.path.split(filepath)[-1])
        msg.attach(mime_image)

        server = smtplib.SMTP('mail.newport.net.nz')
        server.ehlo('Python Photobooth')
        server.starttls()
        server.ehlo()
        server.login(FROM_ADDR, 'PASSWORD')
        server.sendmail(FROM_ADDR, email_addr, msg.as_string())
        finish = time.time()
        print('Email sending started {0}, finished {1}, elapsed {2}. Output {3}'.format(start, finish, finish - start, filepath))

    def draw_centered_text(self, text, font=None, color=(255, 255, 255), outline=False):
        """Center text in window"""
        if font == None:
            font = self.small_font
        fw, fh = font.size(text)
        if outline:
            textobj = font.render(text, True, (0, 0, 0))
            for xoffset in (-1, 1):
                for yoffset in (-1, 1):
                    textpos = textobj.get_rect(centerx=self.background.get_width() / 2 + xoffset,
                                               centery=self.background.get_height() / 2 + yoffset)
                    self.screen.blit(textobj, textpos)
        textobj = font.render(text, True, color)
        textpos = textobj.get_rect(centerx=self.background.get_width() / 2, centery=self.background.get_height() / 2)
        self.screen.blit(textobj, textpos)

    def switch_state(self, target):
        if target == BoothState.shooting:
            # Transition IN to shooting
            self.countdown = READY_WAIT
            self.fps = 60  # This is a placeholder for infinity in this case...
            self.shoot_phase = ShootPhase.get_ready
            self.shots_left = SHOT_COUNT
            self.images = []
            self.phase_start = time.time()
        elif target == BoothState.waiting:
            self.fps = self.base_fps
        if self.state == BoothState.thanks:
            # When transitioning OUT of thanks
            self.shot_counter = 0
            self.session_counter += 1
        self.state = target


def serial_listener():
    try:
        s = serial.Serial('/dev/ttyACM0', 9600)
    except serial.SerialException as e:
        print e
        return
    print('Serial listener attached')
    while True:
        command = s.readline().rstrip()
        if command == b'd':
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, action='button_pressed'))
        elif command == b'r':
            print('Ready signal received from Arduino')


if __name__ == '__main__':
    if not os.path.exists(STORE_DIR):
        os.mkdir(STORE_DIR)
    listener = threading.Thread(target=serial_listener)
    listener.daemon = True
    listener.start()
    BoothView().run()

def quit_pressed():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
    # Don't quit... someone might be messing around
    return False
