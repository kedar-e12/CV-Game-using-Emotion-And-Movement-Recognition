import mediapipe
import numpy as np
import cv2
import pygame
import sys
import math
import random
import time
from pygame import Vector2
from pygame import sprite
from pygame import mixer
from pygame.draw import rect
import mouse 


import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Variables Initilization
global dt
screenSIZE = (1920, 1080)
isMenu = True
#ypos = y*48 +960
#xpos = x*27 -540

facemouse_x = 0
facemouse_y = 0

EYEBROW_RAISE = 0
MOUTH_LENGTH = 0
MOUTH_APERTURE =0
BLINKRATIO = 0
BLINKCOUNT = 0
DIRECTION = ""

TIMEOFLAST = 0 

webcam = cv2.VideoCapture(0)
FACEMESHOBJECT = mediapipe.solutions.face_mesh
FACEMESH = FACEMESHOBJECT.FaceMesh()
MPDRAWING = mediapipe.solutions.drawing_utils
DRAWINGSPECS = MPDRAWING.DrawingSpec(color = (0,0,255), thickness=1, circle_radius=1)


# -------------------------------------------------------------------------------

# pygame window initilization
pygame.init()
screen = pygame.display.set_mode((screenSIZE), pygame.FULLSCREEN)
pygame.display.set_caption("Penguin Shooter")
favicon = pygame.image.load("data/images/Logo.png")
pygame.display.set_icon(favicon)


class Explosion():
    global dt

    def __init__(self, position):
        self.position = Vector2()
        self.position.x = position.x
        self.position.y = position.y
        self.width = 20

    def draw(self, screen):
        pygame.draw.circle(screen, (220, 0, 0), self.position, self.width)
        pygame.draw.circle(screen, (255, 153, 51), self.position, self.width - (self.width / 2))

    def scale_down(self):
        if (self.width > 0):
            self.width -= dt*100


class Gun():
    def __init__(self):
        self.gun_sprite = None
        self.position = Vector2()
        self.is_flipped = False
        self.bullet_count = 30
        pygame.font.init()
        self.font = pygame.font.Font("data/fonts/oswald.ttf", 300)
        self.position = pygame.Vector2()
        self.refresh_sprite()
        self.explosions = []

    def render_current_ammo(self, screen):
        text = self.font.render(str(self.bullet_count), False, (200, 200, 200))
        screen.blit(text, (800, 200))

    def shoot(self):
        global facemouse_y
        global facemouse_x
        if (self.bullet_count > 0):
            sound = mixer.Sound("data/audio/Gunshot.wav")
            sound.set_volume(0.02)
            sound.play()
            exp_pos = Vector2()
            exp_pos.x = self.position.x
            exp_pos.y = self.position.y
            #mouse_x, mouse_y = pygame.mouse.get_pos()
            mouse_x, mouse_y = facemouse_x, facemouse_y
            
            rel_x, rel_y = mouse_x - self.position.x, mouse_y - self.position.y
            mag = Vector2(rel_x, rel_y).magnitude()
            exp_pos.x += (rel_x / mag) * 100
            exp_pos.y += (rel_y / mag) * 100
            explosion = Explosion(exp_pos)
            self.explosions.append(explosion)
            self.bullet_count -= 1
        else:
            sound = mixer.Sound("data/audio/CantShoot.wav")
            sound.set_volume(0.08)
            sound.play()

    def explode(self, screen):
        for i in range(len(self.explosions)):
            if (self.explosions[i].width <= 1):
                self.explosions.remove(self.explosions[i])
                break
            self.explosions[i].scale_down()
            self.explosions[i].draw(screen)

    def refresh_sprite(self):
        self.gun_sprite = pygame.image.load('data/images/Gun.png').convert_alpha()
        self.gun_sprite = pygame.transform.scale(self.gun_sprite, (200, 200))

    def draw(self, screen):
        screen.blit(self.gun_sprite, self.blit_position())
        self.explode(screen)

    def set_position(self, position):
        self.position = position

    def set_rotation(self, degrees):
        self.refresh_sprite()
        self.gun_sprite = pygame.transform.rotate(self.gun_sprite, degrees)

    def blit_position(self):
        return self.position.x - (self.gun_sprite.get_width() / 2), self.position.y - (self.gun_sprite.get_height() / 2)


class Player():
    global dt

    def __init__(self):
        self.is_dead = False
        self.score = 0
        self.position = pygame.Vector2()
        w, h = pygame.display.get_surface().get_size()
        self.position.xy = w / 2, h / 5
        self.velocity = pygame.Vector2()
        self.rotation = pygame.Vector2()
        self.offset = pygame.Vector2()
        self.gun = Gun()
        self.drag = 100
        self.gravity_scale = 150
        self.player_sprite = pygame.image.load('data/images/Player.png').convert_alpha()
        self.player_sprite = pygame.transform.scale(self.player_sprite, (50, 60))
        self.gun.set_position(self.position)

    def move(self):
        self.gravity()
        self.air_resistance()
        self.wall_detection()
        self.position.x -= self.velocity.x * dt
        self.position.y -= self.velocity.y * dt

    def handle_gun(self):
        self.gun.set_position(self.position)
        #mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_x, mouse_y = facemouse_x, facemouse_y
        rel_x, rel_y = mouse_x - self.position.x, mouse_y - self.position.y
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x)
        self.gun.set_rotation(angle)

        if (self.offset.x > 0):
            self.offset.x = rel_x if rel_x < 4 else 4
        else:
            self.offset.x = rel_x if rel_x > -4 else -4
        if (self.offset.y > 0):
            self.offset.y = rel_y if rel_y < 4 else 4
        else:
            self.offset.y = rel_y if rel_y > -4 else -4

    def wall_detection(self):
        if (self.position.x < 0):
            self.position.x = 1900
        if (self.position.x > 1900):
            self.position.x = 0

    def get_score(self):
        return self.score

    def gravity(self):
        self.velocity.y -= self.gravity_scale * dt

    def air_resistance(self):
        if (self.velocity.y > 0):
            self.velocity.y -= self.drag * dt
        if (self.velocity.x > 0):
            self.velocity.x -= (self.drag - 50) * dt
        else:
            self.velocity.x += (self.drag - 50) * dt

    def check_state(self):
        global isMenu
        if (self.is_dead):
            old_highscore_value = open("data/serialisation/highscore.csv", "r").readline()
            try:
                if (self.score > int(old_highscore_value)):
                    highscore_value = open("data/serialisation/highscore.csv", "w")
                    highscore_value.write(str(self.score))
                    highscore_value.close()
            except:
                pass
            isMenu = True

    def collision_detection(self, level_builder):
        for i in range(len(level_builder.refills)):
            other = level_builder.refills[i]
            if (self.get_left() < other.get_right() and self.get_right() > other.get_left() and self.get_top() < other.get_bottom() and self.get_bottom() > other.get_top()):
                self.gun.bullet_count += 30
                level_builder.populate_refill()
                self.score += 30

        for i in range(len(level_builder.enemies)):
            other = level_builder.enemies[i]
            if (self.get_left() < other.get_right() and self.get_right() > other.get_left() and self.get_top() < other.get_bottom() and self.get_bottom() > other.get_top()):
                self.is_dead = True
        if (self.position.y > 1080):
            self.is_dead = True

    def get_right(self):
        return self.position.x + (self.player_sprite.get_width() / 2)

    def get_left(self):
        return self.position.x - (self.player_sprite.get_width() / 2)

    def get_top(self):
        return self.position.y - (self.player_sprite.get_height() / 2)

    def get_bottom(self):
        return self.position.y + (self.player_sprite.get_height() / 2)

    def draw(self, screen):
        self.gun.draw(screen)
        screen.blit(self.player_sprite, self.blit_position())
        pygame.draw.circle(screen, (0,0,0), (self.position.x - 14 + self.offset.x, self.position.y - 10 + self.offset.y), 4)
        pygame.draw.circle(screen, (0,0,0), (self.position.x + 4 + self.offset.x , self.position.y - 10 + self.offset.y ), 4)

    def blit_position(self):
        return (self.position.x - (self.player_sprite.get_width() / 2), self.position.y - (self.player_sprite.get_height() / 2))

    def shoot(self):
        if (self.gun.bullet_count <= 0):
            return
        #mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_x, mouse_y = facemouse_x, facemouse_y
        rel_x, rel_y = mouse_x - self.position.x, mouse_y - self.position.y
        vector = Vector2()
        vector.xy = rel_x, rel_y
        mag = vector.magnitude()
        vector.xy /= mag
        self.velocity.y = 0
        self.velocity.x = 0
        self.add_force(vector, 400)

    def add_force(self, vector, magnitude):
        self.velocity.x += vector.x * magnitude
        self.velocity.y += vector.y * magnitude

# Refill class


class Refill:
    def __init__(self, position):
        self.position = Vector2()
        self.position.x = position.x
        self.position.y = position.y
        self.gun_sprite = pygame.image.load('data/images/Bullet.png').convert_alpha()
        self.gun_sprite = pygame.transform.scale(self.gun_sprite, (30, 40))

    def draw(self, screen):
        screen.blit(self.gun_sprite, self.position)

    def get_right(self):
        return self.position.x + 30

    def get_left(self):
        return self.position.x

    def get_top(self):
        return self.position.y

    def get_bottom(self):
        return self.position.y + 40

# Enemies Class


class Enemy:
    global dt

    def __init__(self, position):
        self.position = Vector2()
        self.position.x = position.x
        self.position.y = position.y
        self.gravity_scale = random.randint(20, 100)

        self.xOffset = 0
        self.yOffset = 0

        rand = random.randint(0, 2)
        self.enemy_sprite = None

        if (rand == 0):
            self.enemy_sprite = pygame.image.load('data/images/Shell.png').convert_alpha()
            self.enemy_sprite = pygame.transform.scale(self.enemy_sprite, (40, 40))
            self.xOffset = 40
            self.yOffset = 40
        elif (rand == 1):
            self.enemy_sprite = pygame.image.load('data/images/Fish.png').convert_alpha()
            self.enemy_sprite = pygame.transform.scale(self.enemy_sprite, (30, 50))
            self.xOffset = 30
            self.yOffset = 50
        else:
            self.enemy_sprite = pygame.image.load('data/images/Bone.png').convert_alpha()
            self.enemy_sprite = pygame.transform.scale(self.enemy_sprite, (30, 50))
            self.xOffset = 30
            self.yOffset = 50

    def draw(self, screen):
        screen.blit(self.enemy_sprite, self.position)
        self.gravity()

    def gravity(self):
        self.position.y += self.gravity_scale * dt

    def get_right(self):
        return self.position.x + self.xOffset

    def get_left(self):
        return self.position.x - self.xOffset

    def get_top(self):
        return self.position.y - self.yOffset

    def get_bottom(self):
        return self.position.y + self.yOffset

# Level Building Class


class LevelBuilder:
    def __init__(self):
        self.refills = []
        self.enemies = []

    def populate_refill(self):
        self.refills = []
        sound = mixer.Sound("data/audio/Reload.wav")
        sound.set_volume(0.02)
        sound.play()
        for i in range(2):
            pos = Vector2()
            pos.x = random.randint(100, 1700)
            pos.y = random.randint(100, 600)
            refill = Refill(pos)
            self.refills.append(refill)

    def spawn_enemies(self):
        rand = random.randint(1, 4)
        sound = mixer.Sound("data/audio/Spawn.wav")
        sound.set_volume(0.05)
        sound.play()
        for i in range(rand):
            random_pos = random.randint(0, 1920)
            position = Vector2()
            position.x = random_pos
            position.y = -30
            enemy = Enemy(position)
            self.enemies.append(enemy)

    def draw(self, screen):
        for i in range(len(self.refills)):
            self.refills[i].draw(screen)
        
        j = len(self.enemies)
        for enmy in self.enemies:
            enmy.draw(screen)
            if enmy.position.y >700:
                self.enemies.remove(enmy)

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.size = None
        self.width = None
        self.height = None
        self.background_color = 245, 245, 245
        self.playercam = pygame.image.load("data/images/Logo.png")
        
        
        self.player = Player()
        self.level_builder = LevelBuilder()
        self.clock = pygame.time.Clock()
        #self.clock.tick(30)
        self.score = 0
        pygame.font.init()
        self.font = pygame.font.Font("data/fonts/oswald.ttf", 40)
        self.update()
        
    def compvisionrender(self, screen):
        global webcam        
        global FACEMESHOBJECT
        global FACEMESH
        global MPDRAWING
        global DRAWINGSPECS
        global facemouse_x
        global facemouse_y
        global EYEBROW_RAISE 
        global MOUTH_LENGTH 
        global MOUTH_APERTURE
        global BLINKRATIO
        global BLINKCOUNT
        global DIRECTION
        global TIMEOFLAST
        
        
        success, image = webcam.read()
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = FACEMESH.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        img_h, img_w, img_c = image.shape
        templist = []
        face_2d = []
        face_3d = []
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                for idx, lm in enumerate(face_landmarks.landmark):
                    x,y = int(lm.x*img_w), int(lm.y*img_h)
                    templist.append([idx,x,y])
                    if len(templist) == 468:
                        x1, y1 = templist[104][1:]
                        x2, y2 = templist[333][1:]
                        facewidth = math.hypot(x2-x1, y2-y1)

                        # Right Eyebrow
                        x1, y1 = templist[65][1:]
                        x2, y2 = templist[158][1:]
                        longitud1 = math.hypot(x2-x1, y2-y1)/facewidth

                        # Left Eyebrow
                        x1, y1 = templist[295][1:]
                        x2, y2 = templist[385][1:]
                        longitud2 = math.hypot(x2-x1, y2-y1)/facewidth
                        
                        # avg eyebrow raise
                        avg_eyebrow_raise = int((longitud1+longitud2) * 1000)
                        EYEBROW_RAISE = avg_eyebrow_raise
                        #cv2.putText(image, f"Eyebrow Raise : {avg_eyebrow_raise}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)

                        # Smile Length
                        x1, y1 = templist[78][1:]
                        x2, y2 = templist[308][1:]
                        longitud3 = int((math.hypot(x2-x1, y2-y1))*1000/facewidth)
                        MOUTH_LENGTH = longitud3
                        #cv2.putText(image, f"Mouth Length: {longitud3}", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)

                        # Mouth Open
                        x1, y1 = templist[13][1:]
                        x2, y2 = templist[14][1:]
                        longitud4 = int((math.hypot(x2-x1, y2-y1))*1000/facewidth)
                        MOUTH_APERTURE = longitud4
                        #cv2.putText(image, f"Mouth Aperture: {longitud4}", (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)

                        # right eye indices
                        # 33 and 133 for horizontal line
                        # 159 and 145 for vert line
                        
                        # left eye indices
                        # 362 and 263 for horizontal line
                        # 386 and 374 for vert line
                        # Eye Blink
                        x1, y1 = templist[33][1:]
                        x2, y2 = templist[133][1:]
                        x3, y3 = templist[159][1:]
                        x4, y4 = templist[145][1:]
                        Right_Eye_Horizontal = math.hypot(x2-x1, y2-y1)
                        Right_Eye_Vertical = math.hypot(x4-x3, y4-y3)
                        Right_Ratio = Right_Eye_Horizontal / Right_Eye_Vertical

                        x1, y1 = templist[362][1:]
                        x2, y2 = templist[263][1:]
                        x3, y3 = templist[386][1:]
                        x4, y4 = templist[374][1:]
                        Left_Eye_Horizontal = math.hypot(x2-x1, y2-y1)
                        Left_Eye_Vertical = math.hypot(x4-x3, y4-y3)
                        Left_Ratio = Left_Eye_Horizontal / Left_Eye_Vertical

                        Mix_ratio = (Left_Ratio + Right_Ratio)/2
                        Mix_ratio = round(Mix_ratio, 2)
                        BLINKRATIO = Mix_ratio
                        #cv2.putText(image, f"Blink Ratio: {Mix_ratio}", (20, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)
                        
                        oldblink = round(BLINKCOUNT)+1
                        
                        if (Mix_ratio > 4.2):
                            BLINKCOUNT+=0.1
                        
                        if (MOUTH_LENGTH > 500):
                            if (time.time_ns() // 1_000_000) - TIMEOFLAST > 50:
                                mouse.click('left')
                                TIMEOFLAST = time.time_ns() // 1_000_000
                            
                        #cv2.putText(image, f"Blink Count: {round(BLINKCOUNT)}", (20, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)

                    if idx == 33 or idx == 263 or idx == 1 or idx == 61 or idx == 291 or idx == 199:
                        if idx == 1:
                            nose_2d = (lm.x * img_w, lm.y * img_h)
                            nose_3d = (lm.x * img_w, lm.y * img_h, lm.z * 3000)
                        
                        face_2d.append([x, y])
                        face_3d.append([x, y, lm.z])

                face_2d = np.array(face_2d, dtype=np.float64)
                face_3d = np.array(face_3d, dtype=np.float64)
                focal_length = 1 * img_w

                # 3d matrix of the camera
                cam_matrix = np.array([[focal_length, 0, img_h / 2],
                                        [0, focal_length, img_w / 2],
                                        [0, 0, 1]])

                # face data will give us rotation and translational vector
                # rotation vector will give us rotation matrix
                # rotation matrix will give us rotation angles
                # multiply angles by 360 as they are normalized between 0 and 1

                dist_matrix = np.zeros((4, 1), dtype=np.float64)
                success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
                rmat, jac = cv2.Rodrigues(rot_vec)
                angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)
                x = angles[0] * 360
                y = angles[1] * 360
                z = angles[2] * 360
                
                if y < -10:
                    DIRECTION = "FACING LEFT"
                elif y > 10:
                    DIRECTION = "FACING RIGHT"
                elif x < -10:
                    DIRECTION = "FACING DOWN"
                elif x > 10:
                    DIRECTION = "FACING TOP"
                else:
                    DIRECTION = "FACING FORWARD"
                
                
                #ypos = y*48 +960
                #xpos = x*27 -540
                facemouse_x = y*192 + 960
                facemouse_y = 540 - x*81

                nose_3d_projection, jacobian = cv2.projectPoints(nose_3d, rot_vec, trans_vec, cam_matrix, dist_matrix)
                p1 = (int(nose_2d[0]), int(nose_2d[1]))
                p2 = (int(nose_2d[0] + y * 25), int(nose_2d[1] - x * 25))

                cv2.line(image, p1, p2, (0, 0, 255), 5)
                #cv2.putText(image, "x: " + str(np.round(x, 2)), (500, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                #cv2.putText(image, "y: " + str(np.round(y, 2)), (500, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                #cv2.putText(image, "z: " + str(np.round(z, 2)), (500, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
            MPDRAWING.draw_landmarks(image=image, landmark_list=face_landmarks, connections=FACEMESHOBJECT.FACEMESH_CONTOURS, landmark_drawing_spec=DRAWINGSPECS, connection_drawing_spec=DRAWINGSPECS)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.playercam = pygame.image.frombuffer(image.tobytes(), image.shape[1::-1], "RGB")
        
           
        
        

    def update(self):
        global isMenu
        self.level_builder.populate_refill()
        next_time = time.time()
        elapsed_time = time.time()
        min_time = 5
        max_time = 10
        enemiy_iteration = 0
        while not isMenu:
            
            self.handle_dt()
            self.clear_screen()
            self.compvisionrender(self.screen)
            
            

            self.player.gun.render_current_ammo(screen)

            self.level_builder.draw(screen)
            self.level_builder.draw(screen)
            self.player.move()
            self.player.handle_gun()
            self.player.collision_detection(self.level_builder)
            self.player.check_state()
            self.player.draw(self.screen)

            self.score = self.player.get_score()

            pygame.display.flip()
            self.handle_events()

            elapsed_time = time.time()
            if (elapsed_time > next_time):
                next_time = elapsed_time + random.randint(min_time, max_time)
                self.level_builder.spawn_enemies()
                enemiy_iteration += 1
                if (enemiy_iteration > 5 and min_time > 1):
                    min_time -= 1
                    max_time -= 1
                    enemiy_iteration = 0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.player.shoot()
                self.player.gun.shoot()

    def clear_screen(self):
        self.screen.fill(self.background_color)
        self.playercam = pygame.transform.scale(self.playercam, (420, 315))
        screen.blit(self.playercam, (0,765))
        
        
        text0 = self.font.render(DIRECTION, False, (200, 200, 200))
        text1 = self.font.render(str(f'BLINK COUNT   : {round(BLINKCOUNT)}'), False, (200, 200, 200))
        text2 = self.font.render(str(f'SMILE LENGTH  : {MOUTH_LENGTH}'), False, (200, 200, 200))
        text3 = self.font.render(str(f'MOUTH OPEN    : {MOUTH_APERTURE}'), False, (200, 200, 200))
        text4 = self.font.render(str(f'EYEBROW RAISE : {EYEBROW_RAISE}'), False, (200, 200, 200))
        screen.blit(text0, (430, 775))
        screen.blit(text1, (430, 835))
        screen.blit(text2, (430, 895))
        screen.blit(text3, (430, 955))
        screen.blit(text4, (430, 1015))
        
        

    def handle_dt(self):
        global dt
        dt = self.clock.tick() / 1000


class Menu():
    def __init__(self, screen):
        self.background_color = 40, 40, 40
        self.screen = screen
        self.update()

    def update(self):
        global isMenu
        global BLINKCOUNT
        BLINKCOUNT = 0
        
        pygame.font.init()

        sound = mixer.Sound("data/audio/Error.wav")
        sound.set_volume(0.05)
        sound.play()

        while isMenu:
            self.clear_screen()
            
            
            logo = pygame.image.load('data/images/Logo.png').convert_alpha()
            logo = pygame.transform.scale(logo, (100, 120))
            screen.blit(logo, (850, 150))

            self.font = pygame.font.Font("data/fonts/oswald.ttf", 70)
            text = self.font.render("Penguin Shooter", False, (255, 255, 255))
            screen.blit(text, (675, 300))

            self.font = pygame.font.Font("data/fonts/oswald.ttf", 50)
            text = self.font.render("Click To Play", False, (150, 150, 150))
            screen.blit(text, (765, 400 + (math.sin(time.time() * 10) * 5)))

            self.font = pygame.font.Font("data/fonts/oswald.ttf", 30)
            highscore_value = open("data/serialisation/highscore.csv", "r").readline()
            highscore = self.font.render("Highscore: " + str(highscore_value), False, (150, 150, 150))
            screen.blit(highscore, (825, 465 + (math.sin(time.time() * 10) * 5)))
            pygame.display.flip()
            self.handle_events()

    def clear_screen(self):
        self.screen.fill(self.background_color)

    def handle_events(self):
        global isMenu
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                webcam.release()
                cv2.destroyAllWindows()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                isMenu = False


instance = None

mixer.init()
mixer.music.load("data/audio/music.mp3")
mixer.music.set_volume(0.035)
mixer.music.play(-1)

while (True):
    if (isMenu):
        instance = Menu(screen)
    else:
        instance = Game(screen)
