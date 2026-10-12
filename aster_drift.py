#!/usr/bin/env python3
"""Aster Drift — neon asteroid blast arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv

if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/ASTER_DRIFT_ElbowOS.mp4")
TITLE, HANDLE = "ASTER DRIFT", "x.com/ElbowOS"

# Distinct neon palette: deep void, electric cyan, magenta, gold, lime
VOID = (4, 2, 18)
CYAN = (0, 255, 220)
MAGENTA = (255, 40, 180)
GOLD = (255, 210, 40)
LIME = (160, 255, 60)
WHITE = (240, 250, 255)
PINK = (255, 100, 200)
BLUE = (40, 80, 255)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("monospace", 72, bold=True)
        self.font_med = pygame.font.SysFont("monospace", 48, bold=True)
        self.font_sm = pygame.font.SysFont("monospace", 36)
        self.reset()

    def reset(self):
        self.ship_x = W // 2
        self.ship_y = H - 220
        self.ship_w = 80
        self.bullets = []
        self.asteroids = []
        self.score = 0
        self.lives = 3
        self.spawn_timer = 0
        self.game_over = False
        self.frame = 0
        self.particles = []
        # Pre-spawn some for motion
        for _ in range(6):
            self.spawn_asteroid()

    def spawn_asteroid(self):
        size = random.choice([40, 60, 80, 100])
        self.asteroids.append({
            "x": random.randint(80, W-80),
            "y": random.randint(-200, 100),
            "vx": random.uniform(-1.5, 1.5),
            "vy": random.uniform(2.5, 5.5),
            "size": size,
            "rot": random.uniform(0, 360),
            "spin": random.uniform(-3, 3),
            "hue": random.choice([CYAN, MAGENTA, GOLD, LIME, PINK])
        })

    def update(self, keys=None, auto=False):
        if self.game_over:
            return
        self.frame += 1
        # Ship control
        if auto:
            # Simple AI: move toward nearest asteroid below, fire often
            target = None
            for a in self.asteroids:
                if a["y"] > 200 and a["y"] < H - 400:
                    if target is None or abs(a["x"] - self.ship_x) < abs(target["x"] - self.ship_x):
                        target = a
            if target:
                if target["x"] < self.ship_x - 20:
                    self.ship_x -= 8
                elif target["x"] > self.ship_x + 20:
                    self.ship_x += 8
            if self.frame % 8 == 0 and len(self.bullets) < 6:
                self.bullets.append({"x": self.ship_x, "y": self.ship_y - 30, "vy": -14})
        else:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.ship_x -= 10
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.ship_x += 10
            if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.frame % 6 == 0:
                self.bullets.append({"x": self.ship_x, "y": self.ship_y - 30, "vy": -16})
        self.ship_x = max(60, min(W-60, self.ship_x))

        # Bullets
        for b in self.bullets[:]:
            b["y"] += b["vy"]
            if b["y"] < -20:
                self.bullets.remove(b)

        # Asteroids
        self.spawn_timer += 1
        if self.spawn_timer > 18 and len(self.asteroids) < 12:
            self.spawn_asteroid()
            self.spawn_timer = 0

        for a in self.asteroids[:]:
            a["x"] += a["vx"]
            a["y"] += a["vy"]
            a["rot"] += a["spin"]
            if a["x"] < a["size"] or a["x"] > W - a["size"]:
                a["vx"] *= -1
            if a["y"] > H + 100:
                self.asteroids.remove(a)
                self.score = max(0, self.score - 5)

        # Collisions bullets vs asteroids
        for b in self.bullets[:]:
            for a in self.asteroids[:]:
                dist = math.hypot(b["x"] - a["x"], b["y"] - a["y"])
                if dist < a["size"] + 8:
                    self.score += int(120 / (a["size"]/40))
                    # Split or destroy
                    if a["size"] > 50:
                        for _ in range(2):
                            self.asteroids.append({
                                "x": a["x"] + random.randint(-20,20),
                                "y": a["y"],
                                "vx": random.uniform(-3,3),
                                "vy": a["vy"] * 0.7,
                                "size": a["size"] * 0.55,
                                "rot": a["rot"],
                                "spin": random.uniform(-5,5),
                                "hue": a["hue"]
                            })
                    # Particles
                    for _ in range(8):
                        self.particles.append({
                            "x": a["x"], "y": a["y"],
                            "vx": random.uniform(-4,4), "vy": random.uniform(-6,2),
                            "life": 20, "c": a["hue"]
                        })
                    if b in self.bullets:
                        self.bullets.remove(b)
                    if a in self.asteroids:
                        self.asteroids.remove(a)
                    break

        # Ship vs asteroids
        for a in self.asteroids[:]:
            dist = math.hypot(self.ship_x - a["x"], self.ship_y - a["y"])
            if dist < a["size"] + 30:
                self.lives -= 1
                self.asteroids.remove(a)
                if self.lives <= 0:
                    self.game_over = True
                break

        # Particles
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)

    def draw(self):
        self.screen.fill(VOID)
        # Starfield
        for i in range(80):
            sx = (i * 137 + self.frame * 2) % W
            sy = (i * 89 + self.frame * 3) % H
            pygame.draw.circle(self.screen, (80, 90, 140), (sx, sy), 1)

        # Asteroids
        for a in self.asteroids:
            # Simple polygon asteroid
            pts = []
            for k in range(7):
                ang = math.radians(a["rot"] + k * 51)
                r = a["size"] * (0.7 + 0.3 * math.sin(k))
                pts.append((a["x"] + math.cos(ang)*r, a["y"] + math.sin(ang)*r))
            if len(pts) >= 3:
                pygame.draw.polygon(self.screen, a["hue"], pts)
                pygame.draw.polygon(self.screen, WHITE, pts, 3)

        # Particles
        for p in self.particles:
            alpha = int(255 * p["life"] / 20)
            pygame.draw.circle(self.screen, p["c"], (int(p["x"]), int(p["y"])), 4)

        # Ship
        # Triangle ship
        pts = [
            (self.ship_x, self.ship_y - 40),
            (self.ship_x - 35, self.ship_y + 30),
            (self.ship_x + 35, self.ship_y + 30)
        ]
        pygame.draw.polygon(self.screen, CYAN, pts)
        pygame.draw.polygon(self.screen, WHITE, pts, 3)
        # Engine glow
        pygame.draw.circle(self.screen, MAGENTA, (int(self.ship_x), int(self.ship_y + 40)), 12)

        # Bullets
        for b in self.bullets:
            pygame.draw.rect(self.screen, GOLD, (b["x"]-4, b["y"]-12, 8, 24))

        # UI overlay
        title_surf = self.font_big.render(TITLE, True, CYAN)
        self.screen.blit(title_surf, (W//2 - title_surf.get_width()//2, 40))
        score_surf = self.font_med.render(f"SCORE {self.score}", True, GOLD)
        self.screen.blit(score_surf, (40, 140))
        lives_surf = self.font_med.render(f"LIVES {self.lives}", True, MAGENTA)
        self.screen.blit(lives_surf, (W - lives_surf.get_width() - 40, 140))
        handle_surf = self.font_sm.render(HANDLE, True, WHITE)
        self.screen.blit(handle_surf, (W//2 - handle_surf.get_width()//2, H - 80))

        if self.game_over:
            over = self.font_big.render("GAME OVER", True, MAGENTA)
            self.screen.blit(over, (W//2 - over.get_width()//2, H//2))

        pygame.display.flip()

    def play_interactive(self):
        running = True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                    self.reset()
            keys = pygame.key.get_pressed()
            self.update(keys=keys, auto=False)
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        # Headless record 15s at 30fps, pipe to ffmpeg
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        total_frames = FPS * SECS
        for i in range(total_frames):
            self.update(auto=True)
            self.draw()
            # Get RGB surface
            raw = pygame.image.tostring(self.screen, "RGB")
            try:
                proc.stdin.write(raw)
            except BrokenPipeError:
                break
            if i % 30 == 0:
                print(f"frame {i}/{total_frames}", flush=True)
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
