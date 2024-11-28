import pygame
from pygame.surface import Surface
from pygame.typing import Point
from typing import Optional
import numpy as np
import random
import math

def clamp(a, b, c):
    return max(a, min(b, c))

class Balloon(pygame.sprite.Sprite):
    target: Optional[pygame.Rect] = None
    target_index: int = 0

    def __init__(self, image: pygame.Surface, center: Point, *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.image = image
        self.rect = image.get_rect(midbottom=center)
        self.health = 100

    def update(self, map: np.ndarray, paths=[]):
        assert self.rect is not None
        if self.rect.x >= 1280+self.rect.width:
            self.kill()
        if self.target is None:
            self.rect.move_ip(2, 0)
            return

        balloon_pos = pygame.Vector2(self.rect.midbottom)
        target_pos = pygame.Vector2(self.target.center)

        if balloon_pos.distance_to(target_pos) > 0:
            balloon_pos.move_towards_ip(target_pos, 2)
            self.rect.midbottom = (int(balloon_pos.x), int(balloon_pos.y))
        else:
            self.target_index += 1
            if 0 <= self.target_index < len(paths):
                self.target = paths[self.target_index]
            else:
                self.target_index = -1
                self.target = None


class Tower(pygame.sprite.Sprite):
    def __init__(self, image: pygame.Surface, center: Point, *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.image = image
        self.rect = image.get_rect(center=center)
        self.shot = 0
        self.target = None

def tile(ground: Surface, tile: int) -> pygame.Surface:
    r = pygame.Rect((64*(tile % 8), 64*(tile // 8)), (64, 64))
    return ground.subsurface(r)

def generate_map(map_height, map_width):
    paths = []
    map = np.full((map_height, map_width), 10, dtype=np.int8)
    start_y = map_height // 2
    yy = start_y
    start_x = 0
    prev = 0
    while start_x < map_width:
        match prev:
            case 0:
                ud = random.choices([0, 1, 2], [.8,.1,.1])[0]
            case 1:
                ud = random.choices([0, 1], [.8,.1])[0]
            case 2:
                ud = random.choices([0, 2], [.8,.1])[0]
        tile_id = None
        match ud:
            case 0:
                if prev == 0:
                    tile_id = 2
                if prev == 1:
                    tile_id = 1
                if prev == 2:
                    tile_id = 17
            case 1:
                if prev == ud:
                    tile_id = 9
                else:
                    tile_id = 19
            case 2:
                if prev == ud:
                    tile_id = 9
                else:
                    tile_id = 3
        assert tile_id is not None
        match ud:
            case 0:
                map[yy, start_x] = tile_id
                paths.append(pygame.Rect(start_x*64+32,yy*64+32, 8,8))
                start_x += 1
            case 1:
                map[yy, start_x] = tile_id
                paths.append(pygame.Rect(start_x*64+32,yy*64+32, 8,8))
                yy = max(0, yy-1)
            case 2:
                map[yy, start_x] = tile_id
                paths.append(pygame.Rect(start_x*64+32,yy*64+32, 8,8))
                yy = min(map_height-1, yy+1)
        prev = ud
    return start_y*64, map, paths

def main():
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    running = True

    ground = pygame.image.load("tiles/ground.png")

    map_width = 1280 // 64
    map_height = 720 // 64

    start_y, map, paths = generate_map(map_height, map_width)

    towers = pygame.sprite.Group()

    radius = 250
    radar = pygame.Surface((radius*2,radius*2))
    radar.set_colorkey((0,0,0))
    radar.set_alpha(23)
    pygame.draw.circle(radar, pygame.Color(0, 0, 255), (radius,radius), radius)

    balloons = pygame.sprite.Group()

    frames = 0
    next = random.uniform(0.9,1.5)

    mode = "towers"

    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    start_y, map, paths = generate_map(map_height, map_width)
                if event.key == pygame.K_m:
                    mode = "towers" if mode == "paths" else "paths"
                if event.key == pygame.K_n:
                    paths = []
            if event.type == pygame.MOUSEBUTTONUP:
                if mode == "towers":
                    if event.button & 1:
                        t = pygame.Rect(0, 0, 64, 64)
                        t.center = pygame.mouse.get_pos()
                        if t.collidelist(towers.sprites()) < 0:
                            Tower(pygame.image.load("tiles/tower1.png"), pygame.mouse.get_pos(), towers)
                    if event.button & 2:
                        t = pygame.Rect(0, 0, 64, 64)
                        t.center = pygame.mouse.get_pos()
                        sprites = towers.sprites()
                        remove = t.collidelist(towers.sprites())
                        if remove >= 0:
                            towers.remove(sprites[remove])
                elif mode == "paths":
                    if event.button & 1:
                        t = pygame.Rect(0, 0, 8, 8)
                        t.center = pygame.mouse.get_pos()
                        paths.append(t)

        (down, _, _) = pygame.mouse.get_pressed()

        balloons.update(map=map, paths=paths)

        # for balloon in balloons:
        #     if balloon.target_index >= 0:
        #         continue
        #     balloon_pos = pygame.Vector2(balloon.rect.center)
        #     node_distance = 10000
        #     node_index = -1
        #     for (i, node) in enumerate(paths):
        #         target_pos = pygame.Vector2(node.center)
        #         if (d := balloon_pos.distance_to(target_pos)) < node_distance:
        #             node_index = i
        #             node_distance = d
        #     if node_index >= 0:
        #         balloon.target = paths[node_index]
        #         balloon.target_index = node_index
        for balloon in balloons:
            if balloon.target_index >= 0 and balloon.target is None and balloon.target_index < len(paths):
                balloon.target = paths[balloon.target_index]

        # for balloon in balloons:
        #     if balloon.target is None:
        #         continue
        #     balloon_pos = pygame.Vector2(balloon.rect.midbottom)
        #     target_pos = pygame.Vector2(balloon.target.center)
        #     if balloon_pos.distance_to(target_pos) > 0:
        #         balloon_pos.move_towards_ip(target_pos, 2)
        #         balloon.rect.midbottom = (int(balloon_pos.x), int(balloon_pos.y))
        #     else:
        #         balloon.target_index += 1
        #         if 0 <= balloon.target_index < len(paths):
        #             balloon.target = paths[balloon.target_index]
        #         else:
        #             balloon.target_index = -1
        #             balloon.target = None

        # Spawn new balloons
        if frames % int(next * 60) == 0:
            next = random.uniform(0.9,1.5)
            Balloon(pygame.image.load("tiles/balloon.png"), (-64, start_y), balloons)

        # fill the screen with a color to wipe away anything from last frame
        screen.fill("black")

        my = 0
        mx = 0
        for line in map:
            for tile_id in line:
                surf = tile(ground, int(tile_id))
                screen.blit(surf, (mx*64, my*64))
                mx += 1
            my += 1
            mx = 0

        towers.draw(screen)
        balloons.draw(screen)

        # for balloon in balloons:
        #     if balloon.target is not None:
        #         pygame.draw.line(screen, (0,200,200), balloon.rect.center, balloon.target.center, width=2)

        prev=None
        for node in paths:
            pygame.draw.rect(screen, (255,255,255), node)
            if prev:
                pygame.draw.line(screen, (200,200,200), prev.center, node.center, width=2)
            prev = node

        for tower in towers.sprites():
            dist = 100000
            closest = None
            for balloon in balloons.sprites():
                a = pygame.math.Vector2(tower.rect.center)
                b = pygame.math.Vector2(balloon.rect.center)
                ab_dist = a.distance_to(b)
                if ab_dist < radius and ab_dist < dist:
                    closest = balloon
            if closest is not None:
                if frames >= tower.shot + 30:
                    tower.target = closest
                    tower.shot = frames
            if tower.target is not None:
                if frames < tower.shot + 10:
                    pygame.draw.line(screen, (255,0,0), tower.rect.center, tower.target.rect.center, width=7)
                if frames >= tower.shot + 10:
                    tower.target.health -= 10
                    tower.target = None

        for balloon in balloons.sprites():
            if balloon.health <= 0:
                balloon.kill()

        # color = (255, 255, 255)
        # for sprite in balloons.sprites():
        #     rect = sprite.rect.copy()
        #     pygame.draw.rect(screen, color, rect, width=2)

        if mode == "towers" and down:
            t = pygame.Rect(0, 0, 64, 64)
            t.center = pygame.mouse.get_pos()
            color = (255,255,255) if t.collidelist(towers.sprites()) < 0 else (255,0,0)
            pygame.draw.rect(screen, color, t, width=2)
            pygame.draw.circle(screen, color, t.center, radius, width=2)
        elif mode == "paths" and down:
            t = pygame.Rect(0, 0, 8, 8)
            t.center = pygame.mouse.get_pos()
            color = (255,255,255) if t.collidelist(towers.sprites()) < 0 else (255,0,0)
            pygame.draw.rect(screen, color, t)

        # for tower in towers.sprites():
            # screen.blit(radar, tower.rect.move(-radius,-radius).center)
            #pygame.draw.circle(screen, pygame.Color(0,255,0,a=128), tower.rect.center, radius)

        # flip() the display to put your work on screen
        pygame.display.flip()

        frames += 1
        clock.tick(60)  # limits FPS to 60

    pygame.quit()

if __name__ == "__main__":
    main()
