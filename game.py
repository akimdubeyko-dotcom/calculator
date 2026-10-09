"""Дерби у стадиона — a small, self-contained Pygame cartoon."""

import argparse
from array import array
import math
import os
from pathlib import Path
import random
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from model import CLUBS, FANS, ITEMS, GameState


WIDTH, HEIGHT = 1200, 800
INK = (34, 48, 67)
MUTED = (110, 121, 130)
PAPER = (247, 246, 240)
WHITE = (255, 255, 249)
MINT = (182, 222, 198)
CORAL = (234, 115, 85)
BLUE = (54, 90, 153)
MAROON = (167, 52, 83)
BUTTON = pygame.Rect(824, 692, 336, 64)
TEAM_BUTTON = pygame.Rect(40, 112, 800, 36)
TEAM_DONE = pygame.Rect(450, 697, 300, 48)
TEAM_CHOICES = [(role, i, pygame.Rect(x, 175 + i * 49, 420, 43))
                for role, x in (("throwers", 160), ("target", 620))
                for i in range(len(CLUBS))]
ITEM_RECTS = [pygame.Rect(40 + i * 202, 692, 190, 64) for i in range(3)]


class Text:
    def __init__(self):
        self.path = pygame.font.match_font("notosans,dejavusans,arial")
        self.fonts = {}

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self.fonts:
            font = pygame.font.Font(self.path, size)
            font.set_bold(bold)
            self.fonts[key] = font
        return self.fonts[key]

    def draw(self, surface, value, position, size=18, color=INK, bold=False, center=False):
        image = self.font(size, bold).render(str(value), True, color)
        rect = image.get_rect(center=position) if center else image.get_rect(topleft=position)
        surface.blit(image, rect)
        return rect


def line(surface, color, start, end, width=2):
    pygame.draw.line(surface, color, start, end, width)


def round_rect(surface, color, rect, radius=12, border=0):
    pygame.draw.rect(surface, color, rect, width=border, border_radius=radius)


def ball(surface, pos, radius=12):
    x, y = pos
    pygame.draw.circle(surface, WHITE, (int(x), int(y)), radius)
    pygame.draw.circle(surface, INK, (int(x), int(y)), radius, 2)
    points = [(x + math.cos(i * math.tau / 5 - 1.57) * radius * 0.43,
               y + math.sin(i * math.tau / 5 - 1.57) * radius * 0.43) for i in range(5)]
    pygame.draw.polygon(surface, INK, points)
    for px, py in points:
        line(surface, INK, (px, py), (x + (px-x)*2.2, y + (py-y)*2.2), 1)


def item_sprite(kind, angle=0):
    image = pygame.Surface((48, 48), pygame.SRCALPHA)
    if kind == 0:
        pygame.draw.polygon(image, INK, [(9, 16), (20, 7), (34, 11), (40, 26), (30, 39), (13, 34)])
        pygame.draw.polygon(image, WHITE, [(12, 17), (21, 10), (32, 14), (37, 26), (29, 36), (15, 32)])
        pygame.draw.lines(image, (164, 175, 184), False, [(20, 12), (25, 23), (14, 30)], 2)
        pygame.draw.lines(image, (164, 175, 184), False, [(25, 23), (33, 27), (28, 35)], 2)
    elif kind == 1:
        pygame.draw.polygon(image, INK, [(9, 9), (39, 9), (33, 39), (15, 39)])
        pygame.draw.polygon(image, (247, 225, 201), [(12, 12), (36, 12), (30, 36), (18, 36)])
        pygame.draw.polygon(image, CORAL, [(14, 20), (34, 20), (32, 29), (16, 29)])
        pygame.draw.ellipse(image, INK, (9, 6, 30, 9))
        pygame.draw.ellipse(image, (173, 213, 230), (12, 8, 24, 5))
    else:
        round_rect(image, INK, (7, 12, 36, 27), 7)
        round_rect(image, (240, 198, 77), (9, 14, 32, 23), 5)
        round_rect(image, (116, 177, 147), (9, 29, 32, 8), 3)
        for x, y in [(15, 20), (29, 18), (34, 24), (23, 25)]:
            pygame.draw.circle(image, (200, 157, 51), (x, y), 2)
    return pygame.transform.rotate(image, angle)


class Sound:
    def __init__(self):
        self.enabled = True
        self.available = False
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            for name, frequency, duration in [("throw", 650, 0.12), ("hit", 170, 0.18)]:
                samples = array("h")
                count = int(22050 * duration)
                for i in range(count):
                    t = i / count
                    phase = math.tau * frequency * duration * (t - 0.35*t*t)
                    samples.append(int(6500 * math.sin(phase) * (1-t) ** 2 * min(t*30, 1)))
                self.sounds[name] = pygame.mixer.Sound(buffer=samples)
            self.available = True
        except pygame.error:
            self.enabled = False

    def play(self, name):
        if self.enabled and self.available:
            self.sounds[name].play()

    def toggle(self):
        if self.available:
            self.enabled = not self.enabled


class Game:
    def __init__(self, seed=None):
        pygame.display.init()
        pygame.font.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Дерби у стадиона")
        icon = pygame.Surface((32, 32))
        icon.fill(MINT)
        ball(icon, (16, 16), 13)
        pygame.display.set_icon(icon)
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.text = Text()
        self.state = GameState(seed)
        self.sound = Sound()
        self.running = True
        self.team_menu = False
        self.background = self.make_background()

    def make_background(self):
        surface = pygame.Surface((WIDTH, HEIGHT))
        surface.fill(PAPER)
        rng = random.Random(87)
        # A warm paper canvas, with a sunlit stadium and tiled plaza.
        round_rect(surface, (229, 237, 231), (32, 160, 1136, 482), 26)
        pygame.draw.circle(surface, (244, 220, 149), (1038, 238), 39)
        for x, y in [(110, 231), (1010, 323), (204, 194)]:
            round_rect(surface, (249, 249, 235), (x, y, 88, 13), 8)
            round_rect(surface, (249, 249, 235), (x+17, y-8, 48, 17), 8)
        for x in (91, 1090):
            line(surface, (135, 155, 148), (x, 232), (x, 406), 5)
            round_rect(surface, INK, (x-25, 223, 50, 13), 4)
            for dx in (-17, -5, 7, 19):
                pygame.draw.circle(surface, (245, 226, 161), (x+dx, 229), 3)
        # Rounded roof, layered facade, and entrance tunnels.
        pygame.draw.ellipse(surface, (161, 181, 181), (165, 189, 870, 201))
        pygame.draw.ellipse(surface, (250, 249, 235), (168, 184, 864, 197))
        pygame.draw.ellipse(surface, (206, 220, 213), (193, 202, 814, 152))
        pygame.draw.rect(surface, (211, 219, 213), (181, 275, 837, 157))
        pygame.draw.rect(surface, (181, 199, 193), (188, 295, 824, 17))
        pygame.draw.rect(surface, (243, 242, 226), (170, 317, 860, 11))
        for x in range(193, 1000, 40):
            line(surface, (242, 240, 224), (x, 282), (x, 408), 4)
        round_rect(surface, INK, (431, 220, 338, 44), 10)
        self.text.draw(surface, "ESPAÑA  /  DÍA DE PARTIDO", (600, 242), 18, WHITE, True, True)
        for x in (254, 463, 674, 875):
            round_rect(surface, (96, 119, 120), (x, 347, 73, 87), 29)
            pygame.draw.rect(surface, (96, 119, 120), (x, 386, 73, 48))
            for i in range(5):
                line(surface, (149, 170, 161), (x+7+i*14, 375), (x+7+i*14, 434), 2)
        # Fans at the gates give depth to the scene.
        for i in range(57):
            x = 195 + i*14
            y = rng.randrange(401, 420)
            color = rng.choice([(156, 176, 167), (147, 161, 159), (218, 220, 203)])
            pygame.draw.circle(surface, color, (x, y-15), 5)
            round_rect(surface, color, (x-6, y-10, 12, 22), 4)
        pygame.draw.rect(surface, (218, 218, 198), (50, 432, 1100, 189))
        round_rect(surface, (218, 218, 198), (32, 587, 1136, 55), 26)
        pygame.draw.rect(surface, (218, 218, 198), (32, 435, 1136, 177))
        surface.set_clip(pygame.Rect(40, 435, 1120, 197))
        for y in (455, 490, 535, 589, 632):
            line(surface, (203, 207, 188), (40, y), (1160, y))
        for x in range(-300, 1500, 170):
            line(surface, (203, 207, 188), (600+(x-600)*0.52, 432), (x, 642))
        for _ in range(160):
            x, y = rng.randrange(52, 1147), rng.randrange(447, 630)
            pygame.draw.circle(surface, (210, 212, 193), (x, y), 1)
        surface.set_clip(None)
        # Corner shrubs and two match-day flags.
        for x in (110, 1090):
            round_rect(surface, (152, 168, 141), (x-29, 476, 58, 20), 5)
            for dx, dy, r in [(-20, -3, 19), (0, -12, 24), (19, -1, 18)]:
                pygame.draw.circle(surface, (125, 159, 137), (x+dx, 469+dy), r)
            line(surface, INK, (x, 358), (x, 460), 3)
            pygame.draw.polygon(surface, WHITE, [(x, 359), (x+47, 369), (x, 392)])
            line(surface, (175, 162, 213), (x+4, 368), (x+33, 374), 5)
        return surface

    def character(self, x, y, index=None):
        hero = index is None
        state = self.state
        phase = 0 if hero else index
        bob = math.sin(state.time*2.8 + phase) * 1.7
        sprite = pygame.Surface((120, 164), pygame.SRCALPHA)
        skin = [(227, 167, 123), (183, 119, 85), (240, 190, 149)][0 if hero else index % 3]
        hair = [(63, 48, 42), (46, 40, 39), (109, 73, 42)][0 if hero else index % 3]
        throwing = not hero and state.poses[index] > 0
        reacting = hero and state.reaction > 0
        # Legs and trainers.
        for lx in (45, 70):
            line(sprite, INK, (lx, 108), (lx + (-3 if lx < 60 else 3), 143), 13)
            round_rect(sprite, WHITE, (lx-11, 139, 23, 9), 4)
            line(sprite, INK, (lx-11, 148), (lx+12, 148), 2)
        # Arms bend into an overhead throwing pose.
        direction = 1 if x < 600 else -1
        for side in (-1, 1):
            shoulder = (60+side*22, 72)
            if throwing and side == direction:
                elbow, hand = (60+side*38, 47), (60+side*29, 28)
            elif reacting:
                elbow, hand = (60+side*41, 82), (60+side*44, 57)
            else:
                elbow, hand = (60+side*32, 89), (60+side*31, 103)
            pygame.draw.lines(sprite, INK, False, [shoulder, elbow, hand], 11)
            pygame.draw.lines(sprite, skin, False, [shoulder, elbow, hand], 7)
            pygame.draw.circle(sprite, skin, hand, 6)
        round_rect(sprite, INK, (34, 62, 52, 55), 12)
        club = CLUBS[state.target if hero else state.throwers]
        round_rect(sprite, club.primary, (37, 65, 46, 48), 9)
        for sx in (44, 64):
            pygame.draw.rect(sprite, club.secondary, (sx, 66, 9, 44))
        round_rect(sprite, INK, (43, 78, 35, 19), 4)
        self.text.draw(sprite, club.badge, (60, 87), 10, WHITE, True, True)
        pygame.draw.circle(sprite, INK, (60, 40), 25)
        pygame.draw.circle(sprite, skin, (60, 40), 22)
        pygame.draw.circle(sprite, skin, (36, 43), 5)
        pygame.draw.circle(sprite, skin, (84, 43), 5)
        pygame.draw.arc(sprite, hair, (37, 17, 46, 31), 0, math.pi, 10)
        pygame.draw.polygon(sprite, hair, [(39, 29), (43, 15), (73, 15), (82, 30), (60, 23)])
        if reacting:
            for ex in (51, 69):
                pygame.draw.lines(sprite, INK, False, [(ex-3, 38), (ex+2, 41), (ex-3, 44)], 2)
            pygame.draw.ellipse(sprite, INK, (55, 50, 10, 9))
        else:
            for ex in (51, 69):
                pygame.draw.circle(sprite, INK, (ex, 41), 2)
            pygame.draw.arc(sprite, INK, (52, 44, 17, 12), math.pi, math.tau, 2)
        if hero:
            # Scarf follows the selected club colors.
            round_rect(sprite, club.primary, (35, 60, 50, 9), 4)
            pygame.draw.rect(sprite, club.secondary, (37, 62, 46, 5))
            pygame.draw.rect(sprite, club.primary, (75, 65, 10, 30))
            for sy in range(67, 94, 8):
                pygame.draw.rect(sprite, club.secondary, (75, sy, 10, 4))
        else:
            # Caps in white and purple, different on each fan.
            if index % 2 == 0:
                pygame.draw.arc(sprite, club.primary, (35, 9, 50, 33), 0, math.pi, 12)
                line(sprite, club.secondary, (32, 28), (80, 28), 5)
        shadow_width = 69 if hero else 60
        pygame.draw.ellipse(self.canvas, (182, 187, 165), (x-shadow_width/2, y-5, shadow_width, 13))
        angle = math.sin(state.time*44) * state.reaction * 16 if reacting else 0
        if throwing:
            angle = -direction * math.sin(state.poses[index]/0.5*math.pi) * 9
        sprite = pygame.transform.rotate(sprite, angle)
        rect = sprite.get_rect(midbottom=(x, y+16+bob))
        self.canvas.blit(sprite, rect)

    def speech(self, text, anchor, color=WHITE, below=False):
        font = self.text.font(16, True)
        width = min(400, font.size(text)[0]+28)
        x = max(45, min(WIDTH-width-45, anchor[0]-width/2))
        y = anchor[1]
        rect = pygame.Rect(x, y, width, 40)
        round_rect(self.canvas, (184, 189, 170), rect.move(0, 3), 12)
        round_rect(self.canvas, color, rect, 12)
        pointer_x = max(x+15, min(x+width-15, anchor[0]))
        if below:
            points = [(pointer_x-7, y+2), (pointer_x+7, y+2), (pointer_x, y-8)]
        else:
            points = [(pointer_x-7, y+38), (pointer_x+7, y+38), (pointer_x, y+49)]
        pygame.draw.polygon(self.canvas, color, points)
        self.text.draw(self.canvas, text, rect.center, 16, INK, True, True)

    def draw(self):
        state = self.state
        self.canvas.blit(self.background, (0, 0))
        ball(self.canvas, (53, 40), 12)
        self.text.draw(self.canvas, "ДВОРОВОЕ КЛАСИКО", (75, 27), 16, INK, True)
        self.text.draw(self.canvas, "ДЕРБИ У СТАДИОНА", (37, 60), 43, INK, True)
        round_rect(self.canvas, (229, 237, 231), TEAM_BUTTON, 10)
        matchup = f"Кидают: {CLUBS[state.throwers].name}  /  В центре: {CLUBS[state.target].name}"
        self.text.draw(self.canvas, matchup, (52, 122), 13, INK, True)
        self.text.draw(self.canvas, "Команды [T]", (716, 121), 13, BLUE, True)
        for x, value, caption in [(936, f"{state.throws:02}", "БРОСКИ"), (1080, f"{state.hits:02}", "ПОПАДАНИЯ")]:
            round_rect(self.canvas, (234, 234, 224), (x-69, 28, 137, 105), 18)
            self.text.draw(self.canvas, value, (x, 65), 33, INK, True, True)
            self.text.draw(self.canvas, caption, (x, 106), 11, MUTED, True, True)
        # Draw characters from the far end of the plaza to the foreground.
        actors = [(x, y, i) for i, (x, y) in enumerate(FANS)] + [(600, 575, None)]
        for x, y, i in sorted(actors, key=lambda a: a[1]):
            self.character(x, y, i)
        # An orbit shows who the next throw comes from.
        if state.cooldown <= 0:
            nx, ny = FANS[state.throws % len(FANS)]
            pygame.draw.ellipse(self.canvas, (103, 141, 119), (nx-38, ny-8, 76, 18), 2)
        for projectile in state.projectiles:
            x, y = projectile.position
            for trail in (0.04, 0.09):
                t = max(0, projectile.progress-trail)
                px = projectile.start[0] + (projectile.end[0]-projectile.start[0])*t
                py = projectile.start[1] + (projectile.end[1]-projectile.start[1])*t - 580*t*(1-t)
                pygame.draw.circle(self.canvas, (183, 191, 174), (int(px), int(py)), 3)
            image = item_sprite(projectile.kind, projectile.progress * 540)
            self.canvas.blit(image, image.get_rect(center=(x, y)))
        for particle in state.particles:
            pygame.draw.circle(self.canvas, particle.color, (int(particle.x), int(particle.y)), max(1, int(particle.life*7)))
        if state.bubble_time > 0:
            fx, fy = FANS[state.speaker]
            self.speech(state.bubble, (fx, fy-207))
        if state.reaction > 0:
            effect = ("ПУФ!", "ПЛЮХ!", "ШЛЁП!")[state.last_kind]
            self.text.draw(self.canvas, effect, (603, 419), 31, CORAL, True, True)
            for side in (-1, 1):
                line(self.canvas, CORAL, (600+side*67, 459), (600+side*84, 446), 3)
                line(self.canvas, CORAL, (600+side*71, 478), (600+side*91, 476), 3)
        if state.reply_time > 0:
            self.speech(state.reply, (600, 593), (248, 224, 165), below=True)
        elif state.throws == 0:
            self.speech("Я просто пришёл на футбол…", (600, 378), (248, 224, 165))
        self.text.draw(self.canvas, "01 / ВЫБЕРИ ПРЕДМЕТ", (40, 662), 12, MUTED, True)
        self.text.draw(self.canvas, "02 / УСТРОЙ ПЕРЕПОЛОХ", (824, 662), 12, MUTED, True)
        for i, rect in enumerate(ITEM_RECTS):
            active = state.selected == i
            round_rect(self.canvas, INK if active else (234, 234, 224), rect, 13)
            icon = item_sprite(i)
            self.canvas.blit(icon, (rect.x+8, rect.y+8))
            self.text.draw(self.canvas, f"{i+1}", (rect.right-20, rect.y+6), 11, MINT if active else MUTED, True)
            self.text.draw(self.canvas, ITEMS[i], (rect.x+56, rect.y+23), 13, WHITE if active else INK, True)
        # Small progress indicator during the key debounce interval.
        self.text.draw(self.canvas, "ВСЁ ПО КРУГУ", (721, 708), 10, MUTED, True, True)
        for i in range(len(FANS)):
            pygame.draw.circle(self.canvas, CORAL if i == state.throws % len(FANS) else (211, 216, 204), (681+i*16, 735), 4)
        round_rect(self.canvas, (211, 104, 76), BUTTON.move(0, 4), 14)
        round_rect(self.canvas, CORAL if state.cooldown <= 0 else (231, 154, 130), BUTTON, 14)
        self.text.draw(self.canvas, "ПРОБЕЛ", (855, 713), 17, WHITE, True)
        self.text.draw(self.canvas, "Бросить", (981, 713), 17, INK, True)
        line(self.canvas, INK, (1110, 725), (1132, 725), 2)
        pygame.draw.lines(self.canvas, INK, False, [(1125, 719), (1132, 725), (1125, 731)], 2)
        self.text.draw(self.canvas, "1–3  предмет     R  заново     Esc  выход", (40, 772), 12, MUTED)
        sound_label = "нет аудиоустройства" if not self.sound.available else ("вкл" if self.sound.enabled else "выкл")
        self.text.draw(self.canvas, f"M  звук: {sound_label}", (825, 772), 12, MUTED)
        if self.team_menu:
            self.draw_team_menu()
        self.present()

    def draw_team_menu(self):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((20, 30, 40, 180))
        self.canvas.blit(shade, (0, 0))
        round_rect(self.canvas, PAPER, (120, 44, 960, 720), 24)
        self.text.draw(self.canvas, "ВЫБЕРИ КОМАНДЫ", (600, 80), 30, INK, True, True)
        self.text.draw(self.canvas, "КТО КИДАЕТ", (370, 137), 18, INK, True, True)
        self.text.draw(self.canvas, "ФАНАТ В ЦЕНТРЕ", (830, 137), 18, INK, True, True)
        for role, index, rect in TEAM_CHOICES:
            club = CLUBS[index]
            selected = getattr(self.state, role) == index
            round_rect(self.canvas, INK if selected else (234, 234, 224), rect, 9)
            round_rect(self.canvas, club.primary, (rect.x+12, rect.y+10, 24, 24), 5)
            pygame.draw.rect(self.canvas, club.secondary, (rect.x+22, rect.y+10, 7, 24))
            self.text.draw(self.canvas, club.name, (rect.x+48, rect.y+10), 17, WHITE if selected else INK, selected)
            if selected:
                pygame.draw.lines(self.canvas, MINT, False, [(rect.right-29, rect.y+22), (rect.right-24, rect.y+27), (rect.right-15, rect.y+16)], 3)
        self.text.draw(self.canvas, "Один клуб на обеих сторонах? Команды поменяются местами.", (600, 677), 14, MUTED, center=True)
        round_rect(self.canvas, CORAL, TEAM_DONE, 12)
        self.text.draw(self.canvas, "ИГРАТЬ  /  Enter", TEAM_DONE.center, 18, INK, True, True)

    def viewport(self):
        width, height = self.window.get_size()
        scale = min(width/WIDTH, height/HEIGHT)
        size = (max(1, int(WIDTH*scale)), max(1, int(HEIGHT*scale)))
        offset = ((width-size[0])//2, (height-size[1])//2)
        return size, offset

    def present(self):
        size, offset = self.viewport()
        self.window.fill(INK)
        if size == (WIDTH, HEIGHT):
            self.window.blit(self.canvas, offset)
        else:
            self.window.blit(pygame.transform.smoothscale(self.canvas, size), offset)
        pygame.display.flip()

    def logical_mouse(self, position):
        size, offset = self.viewport()
        return ((position[0]-offset[0])*WIDTH/size[0], (position[1]-offset[1])*HEIGHT/size[1])

    def throw(self):
        if self.state.throw():
            self.sound.play("throw")

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                self.team_menu = not self.team_menu
                return
            if self.team_menu:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.team_menu = False
                return
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_SPACE:
                self.throw()
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.state.select(event.key-pygame.K_1)
            elif event.key == pygame.K_r:
                self.state.reset()
            elif event.key == pygame.K_m:
                self.sound.toggle()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.logical_mouse(event.pos)
            if self.team_menu:
                if TEAM_DONE.collidepoint(pos):
                    self.team_menu = False
                else:
                    for role, index, rect in TEAM_CHOICES:
                        if rect.collidepoint(pos):
                            self.state.choose_club(role, index)
                return
            if TEAM_BUTTON.collidepoint(pos):
                self.team_menu = True
                return
            if BUTTON.collidepoint(pos):
                self.throw()
            for i, rect in enumerate(ITEM_RECTS):
                if rect.collidepoint(pos):
                    self.state.select(i)
        elif event.type == pygame.VIDEORESIZE:
            self.window = pygame.display.set_mode((max(480, event.w), max(320, event.h)), pygame.RESIZABLE)

    def step(self, dt):
        for event in pygame.event.get():
            self.handle_event(event)
        if not self.team_menu and self.state.update(dt):
            self.sound.play("hit")
        self.draw()

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.step(min(clock.tick(60)/1000, 0.05))

    def smoke_test(self, screenshot=None):
        """Exercise real keyboard events, rendering, impacts, reset and shutdown."""
        def press(key):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
            self.step(1/60)

        for kind in range(3):
            press(pygame.K_1+kind)
            press(pygame.K_SPACE)
            if not self.state.projectiles or self.state.projectiles[-1].kind != kind:
                raise RuntimeError("Keyboard did not create the selected projectile")
            for _ in range(52):
                self.step(1/60)
        if self.state.hits != 3 or self.state.throws != 3:
            raise RuntimeError("Expected one impact for each of the three item types")
        press(pygame.K_SPACE)
        for _ in range(20):
            self.step(1/60)
        if screenshot:
            destination = Path(screenshot)
            destination.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(self.canvas, str(destination))
        # Resize and verify that the visible button still receives clicks.
        self.handle_event(pygame.event.Event(pygame.VIDEORESIZE, w=900, h=680))
        size, offset = self.viewport()
        mapped = (offset[0]+BUTTON.centerx*size[0]/WIDTH, offset[1]+BUTTON.centery*size[1]/HEIGHT)
        self.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=mapped))
        if self.state.throws != 5:
            raise RuntimeError("Throw button failed after resizing the window")
        before = self.sound.enabled
        press(pygame.K_m)
        if self.sound.available and before == self.sound.enabled:
            raise RuntimeError("Mute key failed")
        press(pygame.K_r)
        if self.state.hits or self.state.throws or self.state.projectiles or self.state.particles:
            raise RuntimeError("Reset did not clear the scene")
        press(pygame.K_ESCAPE)
        if self.running:
            raise RuntimeError("Escape did not close the game")
        print("Smoke test passed: 3 item types, keyboard, impacts, rendering, resized mouse input, mute, reset, exit.")


def main():
    parser = argparse.ArgumentParser(description="Дерби у стадиона — мультяшная игра на Python")
    parser.add_argument("--smoke-test", action="store_true", help="проверка без экрана и аудиоустройства")
    parser.add_argument("--screenshot", help="путь к PNG-кадру при --smoke-test")
    args = parser.parse_args()
    if args.screenshot and not args.smoke_test:
        parser.error("--screenshot используется вместе с --smoke-test")
    if args.smoke_test:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    elif sys.platform.startswith("linux") and not any(os.environ.get(k) for k in ("DISPLAY", "WAYLAND_DISPLAY", "SDL_VIDEODRIVER")):
        print("Для игры нужен рабочий стол с графическим экраном. Для облачной проверки: python game.py --smoke-test", file=sys.stderr)
        return 1
    try:
        game = Game(seed=42 if args.smoke_test else None)
        if args.smoke_test:
            game.smoke_test(args.screenshot)
        else:
            game.run()
    except pygame.error as error:
        print(f"Не удалось запустить графику: {error}", file=sys.stderr)
        return 1
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
