import pygame
import sys
import math

# ----------------------------
# CONFIGURACIÓN BÁSICA
# ----------------------------
WIDTH, HEIGHT = 960, 540
FPS = 60
TITLE = "PLATAFORMERO RECTANGULAR"

# Colores
BLACK = (15, 15, 20)
WHITE = (240, 240, 255)
GRAY = (80, 80, 100)
RED = (230, 60, 60)
GREEN = (60, 200, 120)
BLUE = (60, 120, 230)
YELLOW = (250, 210, 70)
CYAN = (60, 220, 220)
ORANGE = (255, 150, 60)

# ----------------------------
# UTILIDADES
# ----------------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def format_time(ms):
    total_sec = ms // 1000
    m = total_sec // 60
    s = total_sec % 60
    return f"{m:02d}:{s:02d}"

# ----------------------------
# CLASES
# ----------------------------
class Platform:
    def __init__(self, x, y, w, h, color=GRAY, vx=0, vy=0, min_x=None, max_x=None, min_y=None, max_y=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.vx = vx
        self.vy = vy
        self.min_x = x if min_x is None else min_x
        self.max_x = x if max_x is None else max_x
        self.min_y = y if min_y is None else min_y
        self.max_y = y if max_y is None else max_y

    def update(self, dt):
        if self.vx != 0:
            self.rect.x += int(self.vx * dt)
            if self.rect.x < self.min_x or self.rect.right > self.max_x:
                self.rect.x = clamp(self.rect.x, self.min_x, self.max_x - self.rect.width)
                self.vx *= -1
        if self.vy != 0:
            self.rect.y += int(self.vy * dt)
            if self.rect.y < self.min_y or self.rect.bottom > self.max_y:
                self.rect.y = clamp(self.rect.y, self.min_y, self.max_y - self.rect.height)
                self.vy *= -1

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect)

class Enemy:
    def __init__(self, x, y, w, h, color=RED, vx=120, min_x=None, max_x=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.vx = vx
        self.min_x = x if min_x is None else min_x
        self.max_x = (x + 1) if max_x is None else max_x

    def update(self, dt):
        self.rect.x += int(self.vx * dt)
        if self.rect.left < self.min_x or self.rect.right > self.max_x:
            self.rect.x = clamp(self.rect.x, self.min_x, self.max_x - self.rect.width)
            self.vx *= -1

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect)
        # franja central
        mid = self.rect.copy()
        mid.height = max(4, self.rect.height // 5)
        mid.centery = self.rect.centery
        pygame.draw.rect(surf, WHITE, mid)

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 36, 48)
        self.color = BLUE
        self.vx = 0
        self.vy = 0
        self.speed = 260
        self.jump_force = -460
        self.gravity = 1100
        self.max_fall = 900
        self.on_ground = False
        self.coyote_timer = 0.0
        self.jump_buffer = 0.0
        self.carry_dx = 0

    def handle_input(self, left, right, up, down, dt):
        ax = 0
        if left: ax -= 1
        if right: ax += 1

        target_vx = ax * self.speed
        lerp = clamp(12 * dt, 0, 1)
        self.vx = (1 - lerp) * self.vx + lerp * target_vx

        if up:
            self.jump_buffer = 0.15
        else:
            self.jump_buffer = max(0, self.jump_buffer - dt)

        if self.coyote_timer > 0 and self.jump_buffer > 0:
            self.vy = self.jump_force
            self.on_ground = False
            self.coyote_timer = 0
            self.jump_buffer = 0

        if down and self.vy > 0:
            self.vy = min(self.vy + 800 * dt, self.max_fall)

    def physics_step(self, platforms, dt):
        self.carry_dx = 0
        self.vy = min(self.vy + self.gravity * dt, self.max_fall)

        # Eje X
        self.rect.x += int(self.vx * dt)
        hits = [p for p in platforms if self.rect.colliderect(p.rect)]
        for p in hits:
            if self.vx > 0:
                self.rect.right = p.rect.left
            elif self.vx < 0:
                self.rect.left = p.rect.right

        # Eje Y
        self.rect.y += int(self.vy * dt)
        hits = [p for p in platforms if self.rect.colliderect(p.rect)]
        grounded_this_frame = False
        for p in hits:
            if self.vy > 0:
                self.rect.bottom = p.rect.top
                self.vy = 0
                grounded_this_frame = True
                self.carry_dx += p.vx * dt
            elif self.vy < 0:
                self.rect.top = p.rect.bottom
                self.vy = 0

        if grounded_this_frame:
            self.rect.x += int(self.carry_dx)

        if grounded_this_frame:
            self.on_ground = True
            self.coyote_timer = 0.1
        else:
            if self.on_ground:
                self.on_ground = False
                self.coyote_timer = 0.1
            else:
                self.coyote_timer = max(0, self.coyote_timer - dt)

        self.rect.x = clamp(self.rect.x, 0, WIDTH - self.rect.width)

    def draw(self, surf, t):
        pygame.draw.rect(surf, self.color, self.rect)
        pulse = 3 + int(2 * (1 + math.sin(t * 6)))
        outline = self.rect.inflate(pulse * 2, pulse * 2)
        pygame.draw.rect(surf, (100, 180, 255), outline, width=2)

# ----------------------------
# NIVEL
# ----------------------------
def build_level():
    platforms = []
    enemies = []

    # Piso
    platforms.append(Platform(0, HEIGHT - 40, WIDTH, 40, color=(50, 60, 80)))

    # Plataformas estáticas
    platforms.append(Platform(60, HEIGHT - 140, 160, 20, color=GREEN))
    platforms.append(Platform(360, HEIGHT - 220, 150, 20, color=GREEN))
    platforms.append(Platform(650, HEIGHT - 300, 180, 20, color=GREEN))

    # Plataformas móviles horizontales
    platforms.append(Platform(120, HEIGHT - 300, 140, 18, color=ORANGE,
                              vx=140, min_x=80, max_x=320))
    platforms.append(Platform(520, HEIGHT - 160, 120, 18, color=ORANGE,
                              vx=-160, min_x=420, max_x=720))

    # Plataforma móvil vertical
    platforms.append(Platform(820, HEIGHT - 200, 100, 18, color=YELLOW,
                              vy=-140, min_y=HEIGHT - 280, max_y=HEIGHT - 120))

    # Enemigos
    enemies.append(Enemy(80, HEIGHT - 70, 36, 30, vx=130, min_x=40, max_x=320))
    enemies.append(Enemy(370, HEIGHT - 250, 36, 30, vx=110, min_x=360, max_x=510))
    enemies.append(Enemy(660, HEIGHT - 330, 36, 30, vx=150, min_x=650, max_x=830))

    spawn = (40, HEIGHT - 120)
    return platforms, enemies, spawn

# ----------------------------
# ENTRADA: TECLADO / JOYSTICK
# ----------------------------
class InputManager:
    def __init__(self):
        self.joy = None
        self.deadzone = 0.2
        self.CROSS_BUTTON = 1   # botón X suele ser 1 en DS4
        self.OPTIONS_BUTTON = 9 # suele ser Options

        try:
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.joy = pygame.joystick.Joystick(0)
                self.joy.init()
                print("Joystick conectado:", self.joy.get_name())
            else:
                print("No se detectó joystick. Usando teclado.")
        except pygame.error as e:
            print("Joystick deshabilitado:", e)
            self.joy = None

    def get_move(self):
        keys = pygame.key.get_pressed()
        left = keys[pygame.K_LEFT]
        right = keys[pygame.K_RIGHT]
        up = keys[pygame.K_UP]
        down = keys[pygame.K_DOWN]

        if self.joy:
            try:
                # D‑Pad (hat)
                if self.joy.get_numhats() > 0:
                    hx, hy = self.joy.get_hat(0)
                    left = left or (hx < 0)
                    right = right or (hx > 0)
                    up = up or (hy > 0)
                    down = down or (hy < 0)

                # Stick izquierdo (horizontal)
                if self.joy.get_numaxes() > 0:
                    ax0 = self.joy.get_axis(0)
                    if abs(ax0) > self.deadzone:
                        left = ax0 < 0
                        right = ax0 > 0

                # Botón X también salta
                if self.joy.get_numbuttons() >= self.CROSS_BUTTON + 1:
                    if self.joy.get_button(self.CROSS_BUTTON):
                        up = True
            except pygame.error:
                # Si algo falla con el joystick, sigue con teclado
                pass
        return left, right, up, down

    def start_pressed(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            return True
        if self.joy and event.type == pygame.JOYBUTTONDOWN:
            # Options o cualquier botón
            return True
        return False

# ----------------------------
# PANTALLAS (ESTADOS)
# ----------------------------
def draw_title_screen(surf, t, font_big, font_small):
    surf.fill(BLACK)
    bands = 12
    for i in range(bands):
        hue = (i * 23 + int(t * 60)) % 360
        color = (
            40 + (hue * 3) % 90,
            60 + (hue * 2) % 120,
            90 + (hue * 5) % 120,
        )
        h = int(HEIGHT / bands) + 2
        y = i * h
        pygame.draw.rect(surf, color, pygame.Rect(0, y, WIDTH, h))

    frame_w, frame_h = 700, 280
    frame = pygame.Rect(0, 0, frame_w, frame_h)
    frame.center = (WIDTH // 2, HEIGHT // 2)
    pygame.draw.rect(surf, (20, 20, 35), frame)
    pygame.draw.rect(surf, CYAN, frame.inflate(12, 12), width=6)

    title = "PLATAFORMERO RECTANGULAR"
    subtitle = "Solo rectángulos. Mucha acción."
    press = "Presiona [ENTER] o [Options] para comenzar"
    controls1 = "TECLADO: ← → moverse | ↑ saltar | ↓ caída rápida"
    controls2 = "PS4: D‑Pad ← → | D‑Pad ↑ o X para saltar"

    tw = font_big.size(title)[0]
    surf.blit(font_big.render(title, True, WHITE), (WIDTH//2 - tw//2, frame.top + 24))
    sw = font_small.size(subtitle)[0]
    surf.blit(font_small.render(subtitle, True, (200, 220, 255)), (WIDTH//2 - sw//2, frame.top + 90))

    puls = 0.5 + 0.5 * (1 + math.sin(t * 3))
    color_press = (int(200 + 55 * puls), int(200 + 55 * (1 - puls)), 255)
    pw = font_small.size(press)[0]
    surf.blit(font_small.render(press, True, color_press), (WIDTH//2 - pw//2, frame.top + 140))

    c1w = font_small.size(controls1)[0]
    c2w = font_small.size(controls2)[0]
    surf.blit(font_small.render(controls1, True, (230, 230, 230)), (WIDTH//2 - c1w//2, frame.top + 190))
    surf.blit(font_small.render(controls2, True, (230, 230, 230)), (WIDTH//2 - c2w//2, frame.top + 220))

def draw_game_over_screen(surf, t, font_big, font_small, time_str):
    surf.fill((10, 10, 18))
    layers = 10
    for i in range(layers):
        scale = 1.0 - i * 0.08
        w = int(WIDTH * scale)
        h = int(HEIGHT * scale * 0.7)
        r = pygame.Rect(0, 0, w, h)
        r.center = (WIDTH // 2, HEIGHT // 2)
        col = (40 + i * 18, 20 + i * 10, 80 + i * 12)
        pygame.draw.rect(surf, col, r, width=3)

    title = "¡GAME OVER!"
    tw = font_big.size(title)[0]
    surf.blit(font_big.render(title, True, (255, 80, 120)), (WIDTH//2 - tw//2, HEIGHT//2 - 110))

    msg = f"Tiempo sobrevivido: {time_str}"
    mw = font_small.size(msg)[0]
    surf.blit(font_small.render(msg, True, WHITE), (WIDTH//2 - mw//2, HEIGHT//2 - 50))

    press1 = "Presiona [R] para reiniciar"
    press2 = "Presiona [M] para volver al menú"
    p1w = font_small.size(press1)[0]
    p2w = font_small.size(press2)[0]
    surf.blit(font_small.render(press1, True, (230, 230, 230)), (WIDTH//2 - p1w//2, HEIGHT//2 + 10))
    surf.blit(font_small.render(press2, True, (230, 230, 230)), (WIDTH//2 - p2w//2, HEIGHT//2 + 40))

    pulse_w = int(300 + 140 * (0.5 + 0.5 * math.sin(t * 4)))
    line = pygame.Rect(WIDTH//2 - pulse_w//2, HEIGHT - 60, pulse_w, 12)
    pygame.draw.rect(surf, (255, 120, 160), line)

# ----------------------------
# BUCLE PRINCIPAL
# ----------------------------
def main():
    pygame.init()
    # Usamos SCALED para mejor compatibilidad y tamaño
    flags = pygame.SCALED | pygame.RESIZABLE
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Fuentes seguras (integradas)
    font_big = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 24)

    input_mgr = InputManager()
    state = "menu"  # "menu", "game", "game_over"

    platforms, enemies, spawn = build_level()
    player = Player(*spawn)

    start_ticks = 0
    elapsed_ms = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        t = pygame.time.get_ticks() / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == "menu":
                if input_mgr.start_pressed(event):
                    platforms, enemies, spawn = build_level()
                    player = Player(*spawn)
                    start_ticks = pygame.time.get_ticks()
                    state = "game"

            if state == "game_over":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        platforms, enemies, spawn = build_level()
                        player = Player(*spawn)
                        start_ticks = pygame.time.get_ticks()
                        state = "game"
                    elif event.key == pygame.K_m:
                        state = "menu"

        if not running:
            break

        # ----- ESTADOS -----
        if state == "menu":
            draw_title_screen(screen, t, font_big, font_small)
            pygame.display.flip()
            continue

        if state == "game":
            left, right, up, down = input_mgr.get_move()
            player.handle_input(left, right, up, down, dt)

            for p in platforms:
                p.update(dt)
            for e in enemies:
                e.update(dt)

            player.physics_step(platforms, dt)

            for e in enemies:
                if player.rect.colliderect(e.rect):
                    state = "game_over"
                    elapsed_ms = pygame.time.get_ticks() - start_ticks

            if player.rect.top > HEIGHT + 80:
                state = "game_over"
                elapsed_ms = pygame.time.get_ticks() - start_ticks

            screen.fill((18, 18, 26))
            grid_color = (30, 30, 50)
            cell = 40
            for x in range(0, WIDTH, cell):
                pygame.draw.rect(screen, grid_color, pygame.Rect(x, 0, 2, HEIGHT))
            for y in range(0, HEIGHT, cell):
                pygame.draw.rect(screen, grid_color, pygame.Rect(0, y, WIDTH, 2))

            for p in platforms:
                p.draw(screen)
            for e in enemies:
                e.draw(screen)
            player.draw(screen, t)

            current_ms = pygame.time.get_ticks() - start_ticks
            screen.blit(pygame.font.Font(None, 24).render(f"Tiempo: {format_time(current_ms)}", True, WHITE), (16, 12))

            pygame.display.flip()
            continue

        if state == "game_over":
            draw_game_over_screen(screen, t, font_big, font_small, format_time(elapsed_ms))
            pygame.display.flip()
            continue

    pygame.quit()
    sys.exit()

# ----------------------------
# EJECUCIÓN
# ----------------------------
if __name__ == "__main__":
    main()