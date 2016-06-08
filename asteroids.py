# -*- coding: utf-8 -*-

import math
import random
import simplegui

WIDTH = 800
HEIGHT = 600
MEDIA_HOST = 'http://commondatastorage.googleapis.com/codeskulptor-assets/'


class ImageInfo(object):
    def __init__(self, center, size, radius=0, lifespan=None, animated=False):
        self.center = center
        self.size = size
        self.radius = radius
        self.lifespan = lifespan if lifespan else float('inf')
        self.animated = animated

    def get_center(self):
        return self.center

    def get_size(self):
        return self.size

    def get_radius(self):
        return self.radius

    def get_lifespan(self):
        return self.lifespan

    def get_animated(self):
        return self.animated


def dist(p, q):
    return math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)


class Ship(object):

    def __init__(self, position, velocity, angle):
        self.position = [position[0], position[1]]
        self.velocity = [velocity[0], velocity[1]]
        self.angle = angle

        self.ship_image_info = ImageInfo([45, 45], [90, 90], 35) 
        self.missile_info = ImageInfo([5,5], [10, 10], 3, 50)
        self.missile_image = simplegui.load_image(
            MEDIA_HOST + 'lathrop/shot2.png')
        self.missile_sound = simplegui.load_sound(
            MEDIA_HOST + 'sounddogs/missile.mp3')
        self.missile_sound.set_volume(.5)
        self.image = simplegui.load_image(
            MEDIA_HOST + 'lathrop/double_ship.png')

        self.image_center = self.ship_image_info.get_center()
        self.image_size = self.ship_image_info.get_size()
        self.radius = self.ship_image_info.get_radius()
        self.animated = self.ship_image_info.get_animated()
        self.thrust = False
        self.angle_velocity = 0
        self.missile_group = set()

    def adjust_center_and_angle(self):
        angle = self.angle
        self.image_center[0] = self.image_size[0] / 2
        if self.thrust:
            self.image_center[0] += self.image_size[0]
        current_center = self.image_center
        return (current_center, angle)
        
        
    def draw(self, canvas):
        angle = 0
        current_center = self.image_center
        if not self.animated:
            current_center, angle = self.adjust_center_and_angle()
        canvas.draw_image(
            self.image, current_center, self.image_size,
            (self.position[0] % WIDTH, self.position[1] % HEIGHT), 
            self.image_size, angle
        )

    def angle_to_vector(self):
        return [math.cos(self.angle), math.sin(self.angle)]

    def accelerate(self):
        forward_velocity = 17.0
        forward = self.angle_to_vector()
        self.velocity[0] += forward[0] / forward_velocity
        self.velocity[1] += forward[1] / forward_velocity

    def update(self):
        slow_down_velocity = 0.991
        self.angle += self.angle_velocity
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.velocity[0] *= slow_down_velocity
        self.velocity[1] *= slow_down_velocity
        if self.thrust:
            self.accelerate()

    def get_new_missile(self):
        missile_forward_velocity = 2.5
        forward = self.angle_to_vector()
        start_position = (
            self.position[0] + (self.image_size[0] / 2) * forward[0],
            self.position[1] + (self.image_size[0] / 2) * forward[1]
        )
        return Sprite(
            start_position,
            [
                self.velocity[0] + missile_forward_velocity * forward[0],
                self.velocity[1] + missile_forward_velocity * forward[1]
            ],
            self.angle, 0, self.missile_image, self.missile_info,
            self.missile_sound
        )

    def shoot(self):
        new_missile = self.get_new_missile()
        self.missile_group.add(new_missile)
        
    def get_position(self):
        return self.position
    
    def get_radius(self):
        return self.radius


class Sprite:

    def __init__(
        self, position, velocity, angle, angle_velocity, image,
        image_info, sound=None
    ):
        self.position = [position[0], position[1]]
        self.velocity = [velocity[0], velocity[1]]
        self.angle = angle
        self.angle_velocity = angle_velocity
        self.image = image
        self.image_center = image_info.get_center()
        self.image_size = image_info.get_size()
        self.radius = image_info.get_radius()
        self.lifespan = image_info.get_lifespan()
        self.animated = image_info.get_animated()
        self.age = 0
        if sound:
            sound.rewind()
            sound.play()

    def adjust_center_and_angle(self):
        angle = 0
        current_center = [
            self.image_center[0] + self.age * self.image_size[0],
            self.image_center[1]
        ]
        return (current_center, angle)
   
    def draw(self, canvas):
        current_center = self.image_center
        angle = self.angle

        if self.animated:
            current_center, angle = self.adjust_center_and_angle()
        canvas.draw_image(
            self.image, current_center, self.image_size,
            (self.position[0] % WIDTH, self.position[1] % HEIGHT),
            self.image_size, self.angle
        )
    
    def update(self):
        self.angle += self.angle_velocity
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.age += 1
        if self.age >= self.lifespan:
            return True
        return False
    
    def get_position(self):
        return self.position
    
    def get_radius(self):
        return self.radius
        
    def collide(self, other_object):
        pos1 = (self.get_position()[0] % WIDTH, self.get_position()[1] % HEIGHT)
        pos2 = (
            other_object.get_position()[0] % WIDTH,
            other_object.get_position()[1] % HEIGHT
        )
        if dist(pos1, pos2) < (self.get_radius() + other_object.get_radius()):
            return True
        return False


class Asteroids(object):

    def __init__(self):
        self.my_ship = Ship([WIDTH / 2, HEIGHT / 2], [0, 0], 0)
        self.rock_group = set()
        self.explosion_group = set()

        self.lives = 3
        self.started = False
        self.score = 0
        self.time = 0.5
        self.max_rock_velocity = 10   
        self.points_to_velocity_map = {
            20: 13, 30: 17, 40: 21, 50: 25, 60: 29, 70: 33, 80: 37,
            90: 41, 100: 45
        }

        self.soundtrack = simplegui.load_sound(
            MEDIA_HOST + 'sounddogs/soundtrack.mp3')
        self.splash_info = ImageInfo([200, 150], [400, 300])
        self.splash_image = simplegui.load_image(
            MEDIA_HOST + 'lathrop/splash.png')
        self.asteroid_info = ImageInfo([45, 45], [90, 90], 40)
        self.asteroid_image = simplegui.load_image(
            MEDIA_HOST + 'lathrop/asteroid_blue.png')
        self.ship_explosion_image = simplegui.load_image(
            MEDIA_HOST + 'lathrop/explosion_alpha.png')
        self.asteroid_explosion_image = simplegui.load_image(
            MEDIA_HOST + 'lathrop/explosion_blue2.png')
        self.ship_thrust_sound = simplegui.load_sound(
            MEDIA_HOST + 'sounddogs/thrust.mp3')
        self.explosion_info = ImageInfo([64, 64], [128, 128], 17, 24, True)
        self.explosion_sound = simplegui.load_sound(
            MEDIA_HOST + 'sounddogs/explosion.mp3')
        self.debris_info = ImageInfo([320, 240], [640, 480])
        self.debris_image = simplegui.load_image(
            MEDIA_HOST + 'lathrop/debris3_brown.png')
        self.nebula_info = ImageInfo([400, 300], [800, 600])
        self.nebula_image = simplegui.load_image(
            MEDIA_HOST + 'lathrop/nebula_blue.s2014.png')


    def keydown(self, key):
        angle_velocity = 0.06
        if key == simplegui.KEY_MAP['left']:
            self.my_ship.angle_velocity = (-1) * angle_velocity
        elif key == simplegui.KEY_MAP['right']:
            self.my_ship.angle_velocity = angle_velocity
        elif key == simplegui.KEY_MAP['up']:
            self.my_ship.thrust = True
            self.ship_thrust_sound.rewind()
            self.ship_thrust_sound.play()
        elif key == simplegui.KEY_MAP['space']:
            self.my_ship.shoot()

        
    def keyup(self, key):
        if key == simplegui.KEY_MAP['left']:
            self.my_ship.angle_velocity = 0
        elif key == simplegui.KEY_MAP['right']:
            self.my_ship.angle_velocity = 0
        elif key == simplegui.KEY_MAP['up']:
            self.my_ship.thrust = False
            self.ship_thrust_sound.pause() 
            self.ship_thrust_sound.rewind()

    def splash_clicked(self, coords):
        center = [WIDTH / 2, HEIGHT / 2]
        size = self.splash_info.get_size()
        inwidth = (
            center[0] - size[0] / 2) < coords[0] < (center[0] + size[0] / 2)
        inheight = (
            center[1] - size[1] / 2) < coords[1] < (center[1] + size[1] / 2)
        return inwidth and inheight

    def reset_state(self):
        self.score = 0
        self.lives = 3
        self.my_ship.missile_group = set()
        self.rock_group = set()
        self.explosion_group = set()
        self.max_rock_velocity = 10

    def click(self, coords):
        if not self.started and self.splash_clicked(coords):
            self.reset_state()
            self.started = True
            self.soundtrack.play()

    def process_sprite_group(self, sprite_group, canvas):
        for sprite in sprite_group:
            sprite.draw(canvas)
            if sprite.update():
                sprite_group.remove(sprite)

    def explode(self, exploding_object, explosion_image):
        new_explosion = Sprite(
            exploding_object.get_position(), (0, 0), 0, 0, explosion_image,
            self.explosion_info, self.explosion_sound
        )
        self.explosion_group.add(new_explosion)        

    def group_collide_object(self, group, other_object):
        collide = False
        for sprite in group:
            if sprite.collide(other_object):
                collide = True
                sprite.animated = True
                self.explode(sprite, self.asteroid_explosion_image)
                group.remove(sprite)
        return collide

    def update_score_and_max_rock_velocity(self):
        self.score += 1
        if self.score in self.points_to_velocity_map:
            self.max_rock_velocity = self.points_to_velocity_map[self.score]

    def rocks_collide_missiles(self):
        for rock in self.rock_group:
            if self.group_collide_object(self.my_ship.missile_group, rock):
                self.rock_group.discard(rock)
                rock.animated = True
                self.update_score_and_max_rock_velocity()

    def get_random_velocity(self):
        direction = random.choice([-1, 1])
        return direction * random.randrange(1, self.max_rock_velocity) / 10.0

    def get_new_rock_data(self):
        position = [random.randrange(0, WIDTH), random.randrange(0, HEIGHT)]
        velocity = [self.get_random_velocity(), self.get_random_velocity()]
        angle_velocity = 0.1 * random.randrange(-2, 3)
        return (position, velocity, angle_velocity)

    def spawn_a_rock(self, position, velocity, angle_velocity):
        new_rock = Sprite(
            position, velocity, 0, angle_velocity, self.asteroid_image,
            self.asteroid_info
        )
        self.rock_group.add(new_rock)                

    def can_spawn(self, position):
        ship_position = self.my_ship.get_position()
        ship_radius = self.my_ship.get_radius()
        return dist(position, ship_position) > 6 * ship_radius
                        
    def rock_spawner(self):
        if self.started and len(self.rock_group) < 12:
            position, velocity, angle_velocity = self.get_new_rock_data()
            if self.can_spawn(position):
                self.spawn_a_rock(position, velocity, angle_velocity)

    def stats_draw(self, canvas):
        canvas.draw_text('Lives:', (50, 50), 24, 'White')  
        canvas.draw_text('Score:', (WIDTH - 150, 50), 24, 'White')
        canvas.draw_text(str(self.lives), (50, 80), 24, 'White')  
        canvas.draw_text(str(self.score), (WIDTH - 150, 80), 24, 'White')

    def background_draw(self, canvas):
        debris_flytime = (self.time / 4) % WIDTH
        debris_center = self.debris_info.get_center()
        debris_size = self.debris_info.get_size()
        canvas.draw_image(
            self.nebula_image, self.nebula_info.get_center(), 
            self.nebula_info.get_size(), (WIDTH / 2, HEIGHT / 2),
            (WIDTH, HEIGHT)
        )
        canvas.draw_image(
            self.debris_image, debris_center, debris_size,
            (debris_flytime - WIDTH / 2, HEIGHT / 2), (WIDTH, HEIGHT)
        )
        canvas.draw_image(
            self.debris_image, debris_center, debris_size,
            (debris_flytime + WIDTH / 2, HEIGHT / 2), (WIDTH, HEIGHT)
        )

        self.stats_draw(canvas)

    def ship_explode(self):
        self.lives -= 1
        self.my_ship.animated = True
        self.explode(self.my_ship, self.ship_explosion_image)
        self.my_ship.animated = False

    def splash_draw(self, canvas):
        canvas.draw_image(
            self.splash_image, self.splash_info.get_center(),
            self.splash_info.get_size(), (WIDTH / 2, HEIGHT / 2),
            self.splash_info.get_size()
        )

    def stop_and_display_splash(self):
        self.started = False
        self.soundtrack.pause()
        self.soundtrack.rewind()
        self.rock_group = set()

    def draw(self, canvas):
        self.time += 1
        self.background_draw(canvas)    

        self.my_ship.draw(canvas)
        self.my_ship.update()

        self.process_sprite_group(self.rock_group, canvas)
        self.process_sprite_group(self.my_ship.missile_group, canvas)
        self.process_sprite_group(self.explosion_group, canvas)
       
        if self.group_collide_object(self.rock_group, self.my_ship):
            self.ship_explode()

        self.rocks_collide_missiles()
            
        if self.lives == 0:
            self.stop_and_display_splash()
        
        if not self.started:
            self.splash_draw(canvas)

    def run_game(self):
        frame = simplegui.create_frame('Asteroids', WIDTH, HEIGHT)
        frame.set_draw_handler(self.draw)
        frame.set_keydown_handler(self.keydown)
        frame.set_keyup_handler(self.keyup)
        time_interval = 1000.0
        timer = simplegui.create_timer(time_interval, self.rock_spawner)
        frame.set_mouseclick_handler(self.click)

        timer.start()
        frame.start()


asteroids = Asteroids()
asteroids.run_game()

