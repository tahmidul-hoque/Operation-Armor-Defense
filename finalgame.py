from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random


GRID_LENGTH = 1500
camera_mode = 0  

# Base and Armor
player_armor = 100
base_integrity = 400
enemies_destroyed = 0
REQ_ELIMINATIONS = 50
game_over = False
victory = False

# Tank and Turret
player_pos = [0.0, -300.0, 0.0]
player_angle = 0.0
turret_angle = 0.0

# Weapons
bullets = []
explosions = []
current_weapon = 'primary'
secondary_ammo = 15
shield_active = False
shield_health = 50
fire_cooldown = 0

# Railgun
railgun_timer = 0
railgun_cooldown = 0

# Enemies
enemies = []
NUM_ENEMIES = 8

# Obstacles
obstacles = [
    {'x': 300, 'y': 300, 'size': 80},
    {'x': -300, 'y': 300, 'size': 80},
    {'x': 300, 'y': -300, 'size': 80},
    {'x': -300, 'y': -300, 'size': 80},
    {'x': 600, 'y': 0, 'size': 100},
    {'x': -600, 'y': 0, 'size': 100}
]

def spawn_enemy():
    angle = random.uniform(0, 2 * math.pi)
    distance = random.uniform(GRID_LENGTH - 400, GRID_LENGTH - 150)
    x = distance * math.cos(angle)
    y = distance * math.sin(angle)
    target = random.choice(['base', 'player'])
    
    return {
        'x': x, 
        'y': y, 
        'speed': random.uniform(0.2, 0.6), 
        'target': target,
        'fire_cooldown': random.randint(1200, 2000),
        'health': 20
    }

def reset_enemy(enemy):
    new_e = spawn_enemy()
    enemy['x'] = new_e['x']
    enemy['y'] = new_e['y']
    enemy['target'] = new_e['target']
    enemy['speed'] = new_e['speed']
    enemy['fire_cooldown'] = new_e['fire_cooldown']
    enemy['health'] = new_e['health']

def init_enemies():
    global enemies
    enemies = [spawn_enemy() for _ in range(NUM_ENEMIES)]

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def get_turret_aim():
    total_angle = player_angle + turret_angle
    dir_x = -math.sin(math.radians(total_angle))
    dir_y = math.cos(math.radians(total_angle))
    muzzle_x = player_pos[0] + (dir_x * 40)
    muzzle_y = player_pos[1] + (dir_y * 40)
    return dir_x, dir_y, muzzle_x, muzzle_y, total_angle

def keyboardListener(key, x, y):
    global player_pos, player_angle, shield_active, game_over, camera_mode
    global current_weapon, fire_cooldown, secondary_ammo
    global railgun_timer, railgun_cooldown, enemies_destroyed
    
    if key == b't' or key == b'T':
        camera_mode = 1 - camera_mode
        
    if key == b'q' or key == b'Q':
        if current_weapon == 'primary':
            current_weapon = 'secondary' 
        else:
            current_weapon = 'primary'
        
    if key == b' ':  
        if not game_over and fire_cooldown == 0:
            dir_x, dir_y, mx, my, total_angle = get_turret_aim()
            if current_weapon == 'primary':
                bullets.append({'x': mx, 'y': my, 'angle': total_angle, 'type': 'primary', 'dmg': 10, 'size': 3, 'speed': 8})
                fire_cooldown = 10
            elif current_weapon == 'secondary' and secondary_ammo > 0:
                bullets.append({'x': mx, 'y': my, 'angle': total_angle, 'type': 'secondary', 'dmg': 50, 'size': 10, 'speed': 5})
                secondary_ammo -= 1
                fire_cooldown = 30

    if key == b'c' or key == b'C': 
        if not game_over and railgun_cooldown == 0:
            dir_x, dir_y, mx, my, total_angle = get_turret_aim()
            railgun_timer = 20        
            railgun_cooldown = 1000    
             
            for enemy in enemies:
                vx = enemy['x'] - mx
                vy = enemy['y'] - my         
                proj = vx * dir_x + vy * dir_y
                if proj > 0:
                    closest_x = mx + proj * dir_x
                    closest_y = my + proj * dir_y
                    
                    dist = math.sqrt((enemy['x'] - closest_x)**2 + (enemy['y'] - closest_y)**2)
                    if dist < 45: 
                        enemy['health'] = 0
                        explosions.append({'x': enemy['x'], 'y': enemy['y'], 'timer': 15})
                        enemies_destroyed += 1
                        reset_enemy(enemy)
            
    if game_over:
        if key == b'r' or key == b'R':
            reset_game()
        return

    speed = 10
    rotation_speed = 4
    
    if key == b'w' or key == b'W':
        new_x = player_pos[0] - math.sin(math.radians(player_angle)) * speed
        new_y = player_pos[1] + math.cos(math.radians(player_angle)) * speed
        if -GRID_LENGTH + 60 < new_x < GRID_LENGTH - 60: player_pos[0] = new_x
        if -GRID_LENGTH + 60 < new_y < GRID_LENGTH - 60: player_pos[1] = new_y
    if key == b's' or key == b'S':
        new_x = player_pos[0] + math.sin(math.radians(player_angle)) * speed
        new_y = player_pos[1] - math.cos(math.radians(player_angle)) * speed
        if -GRID_LENGTH + 60 < new_x < GRID_LENGTH - 60: player_pos[0] = new_x
        if -GRID_LENGTH + 60 < new_y < GRID_LENGTH - 60: player_pos[1] = new_y
    if key == b'a' or key == b'A':
        player_angle += rotation_speed
    if key == b'd' or key == b'D':
        player_angle -= rotation_speed

    if key == b'e' or key == b'E':
        if shield_health > 0:
            shield_active = not shield_active

def specialKeyListener(key, x, y):
    global turret_angle
    turret_speed = 3
    if game_over: return
    if key == GLUT_KEY_LEFT:
        turret_angle += turret_speed
    if key == GLUT_KEY_RIGHT:
        turret_angle -= turret_speed


def reset_game():
    global player_armor, base_integrity, enemies_destroyed, game_over, victory
    global player_pos, player_angle, turret_angle, bullets, secondary_ammo
    global shield_active, shield_health, fire_cooldown, explosions
    global railgun_timer, railgun_cooldown, current_weapon
    player_armor = 100
    base_integrity = 400
    enemies_destroyed = 0
    game_over = False
    victory = False
    player_pos = [0.0, -300.0, 0.0]
    player_angle = 0.0
    turret_angle = 0.0
    bullets = []
    explosions = []
    current_weapon = 'primary'
    secondary_ammo = 15
    shield_active = False
    shield_health = 50
    fire_cooldown = 0
    railgun_timer = 0
    railgun_cooldown = 0
    init_enemies()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(90, 1.25, 0.1, 5000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    dir_x, dir_y, mx, my, total_angle = get_turret_aim()

    if camera_mode == 0:
        cam_x = player_pos[0] + math.sin(math.radians(player_angle)) * 200
        cam_y = player_pos[1] - math.cos(math.radians(player_angle)) * 200
        gluLookAt(cam_x, cam_y, 120, player_pos[0], player_pos[1], 0, 0, 0, 1)
    else:
        cam_x = player_pos[0] + (dir_x * 5)
        cam_y = player_pos[1] + (dir_y * 5)
        cam_z = 55
        gluLookAt(cam_x, cam_y, cam_z, cam_x + (dir_x * 100), cam_y + (dir_y * 100), cam_z, 0, 0, 1)

def idle():
    global fire_cooldown, player_armor, base_integrity, game_over, victory
    global enemies_destroyed, turret_angle, shield_active, shield_health, explosions
    global railgun_timer, railgun_cooldown

    if game_over: return

    if fire_cooldown > 0:
        fire_cooldown -= 1
        
    if railgun_cooldown > 0:
        railgun_cooldown -= 1
        
    if railgun_timer > 0:
        railgun_timer -= 1
        
    active_explosions = []
    for exp in explosions:
        exp['timer'] -= 1
        if exp['timer'] > 0:
            active_explosions.append(exp)
    explosions[:] = active_explosions

    alive_bullets = []
    for b in bullets:
        b['x'] -= math.sin(math.radians(b['angle'])) * b['speed']
        b['y'] += math.cos(math.radians(b['angle'])) * b['speed']
        
        hit = False
        explode = False 
        
        # Bullet vs Concrete Obstacles
        for obs in obstacles:
            dist = math.sqrt((b['x'] - obs['x'])**2 + (b['y'] - obs['y'])**2)
            if dist < obs['size'] / 2:
                hit = True
                if b['type'] == 'secondary': explode = True
                break
                
        # Bullet vs Command Base
        dist_b = math.sqrt((b['x'] - 0)**2 + (b['y'] - 0)**2)
        if dist_b < 65:
            hit = True
            if b['type'] == 'secondary': 
                explode = True
            if b['type'] == 'enemy': 
                base_integrity -= b['dmg']

        # Enemy Bullet vs Player
        if b['type'] == 'enemy' and not hit:
            dist_p = math.sqrt((b['x'] - player_pos[0])**2 + (b['y'] - player_pos[1])**2)
            if dist_p < 30:
                hit = True
                if shield_active:
                    shield_health -= b['dmg']
                    if shield_health <= 0: shield_active = False
                else:
                    player_armor -= b['dmg']
        
        # Player Bullet vs Enemies
        elif b['type'] in ['primary', 'secondary'] and not hit:
            for enemy in enemies:
                dist = math.sqrt((b['x'] - enemy['x'])**2 + (b['y'] - enemy['y'])**2)
                if dist < 25:
                    hit = True
                    if b['type'] == 'secondary':
                        explode = True
                    else:
                        enemy['health'] -= b['dmg']
                        if enemy['health'] <= 0:
                            enemies_destroyed += 1
                            reset_enemy(enemy)
                    break

        # Area of Effect (AoE) logic for Heavy Shells
        if explode:
            explosions.append({'x': b['x'], 'y': b['y'], 'timer': 15})
            blast_radius = 80
            for enemy in enemies:
                dist = math.sqrt((b['x'] - enemy['x'])**2 + (b['y'] - enemy['y'])**2)
                if dist < blast_radius:
                    enemy['health'] -= b['dmg'] 
                    if enemy['health'] <= 0:
                        enemies_destroyed += 1
                        reset_enemy(enemy)
        
        if not hit and abs(b['x']) < GRID_LENGTH and abs(b['y']) < GRID_LENGTH:
            alive_bullets.append(b)
            
    bullets[:] = alive_bullets

    for enemy in enemies:
        if enemy['target'] == 'base':
            target_x, target_y = 0.0, 0.0
        else:
            target_x, target_y = player_pos[0], player_pos[1]

        dx = target_x - enemy['x']
        dy = target_y - enemy['y']
        distance_to_target = math.sqrt(dx**2 + dy**2)
        if distance_to_target > 350:
            enemy['x'] += (dx / distance_to_target) * enemy['speed']
            enemy['y'] += (dy / distance_to_target) * enemy['speed']
            
        # Enemy vs Obstacle collision
        for obs in obstacles:
            dist = math.sqrt((enemy['x'] - obs['x'])**2 + (enemy['y'] - obs['y'])**2)
            min_dist = 25 + obs['size'] / 2 
            if dist < min_dist:
                overlap = min_dist - dist
                if dist > 0:
                    enemy['x'] += ((enemy['x'] - obs['x']) / dist) * overlap
                    enemy['y'] += ((enemy['y'] - obs['y']) / dist) * overlap
                    enemy['health'] -= 0.5  
                    if enemy['health'] <= 0:
                        enemies_destroyed += 1
                        reset_enemy(enemy)
                        break
        # Enemy vs Command Base Collision
        dist_base = math.sqrt((enemy['x'] - 0)**2 + (enemy['y'] - 0)**2)
        min_dist = 125
        if dist_base < min_dist:
            overlap = min_dist - dist_base
            if dist_base > 0:
                enemy['x'] += ((enemy['x'] - 0) / dist_base) * overlap
                enemy['y'] += ((enemy['y'] - 0) / dist_base) * overlap
                enemy['health'] -= 0.5  
                if enemy['health'] <= 0:
                    enemies_destroyed += 1
                    reset_enemy(enemy)
                    break
        
        # Enemy vs Player Collision
        dist_p = math.sqrt((enemy['x'] - player_pos[0])**2 + (enemy['y'] - player_pos[1])**2)
        min_dist_p = 45 
        if dist_p < min_dist_p:
            overlap = min_dist_p - dist_p
            if dist_p > 0:
                enemy['x'] += ((enemy['x'] - player_pos[0]) / dist_p) * overlap
                enemy['y'] += ((enemy['y'] - player_pos[1]) / dist_p) * overlap
            
            enemy['health'] -= 1.5
            if shield_active:
                shield_health -= 1.5
                if shield_health <= 0: shield_active = False
            else:
                player_armor -= 1.5
                
            if enemy['health'] <= 0:
                enemies_destroyed += 1
                reset_enemy(enemy)
                continue

        # Enemy Firing Logic
        if distance_to_target <= 350:
            if enemy['fire_cooldown'] > 0:
                enemy['fire_cooldown'] -= 1
            else:
                aim_angle = math.degrees(math.atan2(-dx, dy))
                bullets.append({
                    'x': enemy['x'], 'y': enemy['y'], 
                    'angle': aim_angle, 'type': 'enemy', 
                    'dmg': 5, 'size': 4, 'speed': 4
                })
                enemy['fire_cooldown'] = random.randint(1200, 2000)

    # Player vs Command Base collision
    dist_base = math.sqrt((player_pos[0] - 0)**2 + (player_pos[1] - 0)**2)
    min_dist_base = 125 
    if dist_base < min_dist_base:
        overlap = min_dist_base - dist_base
        if dist_base > 0:
            player_pos[0] += ((player_pos[0] - 0) / dist_base) * overlap
            player_pos[1] += ((player_pos[1] - 0) / dist_base) * overlap
            if not shield_active:
                player_armor -= 1

    # Player vs Obstacle collision 
    for obs in obstacles:
        dist = math.sqrt((player_pos[0] - obs['x'])**2 + (player_pos[1] - obs['y'])**2)
        min_dist = 25 + obs['size']/2
        if dist < min_dist:
            overlap = min_dist - dist
            if dist > 0:
                player_pos[0] += ((player_pos[0] - obs['x']) / dist) * overlap
                player_pos[1] += ((player_pos[1] - obs['y']) / dist) * overlap
                if not shield_active:
                    player_armor -= 1 

    if base_integrity <= 0 or player_armor <= 0:
        game_over = True
    if enemies_destroyed >= REQ_ELIMINATIONS:
        game_over = True
        victory = True

    glutPostRedisplay()

def draw_environment():
    glBegin(GL_QUADS)
    tile_size = 300
    for i in range(-GRID_LENGTH, GRID_LENGTH, tile_size):
        for j in range(-GRID_LENGTH, GRID_LENGTH, tile_size):
            if ((i // tile_size) + (j // tile_size)) % 2 == 0:
                glColor3f(0.85, 0.75, 0.55)
            else:
                glColor3f(0.80, 0.70, 0.50)
            glVertex3f(i, j, 0)
            glVertex3f(i + tile_size, j, 0)
            glVertex3f(i + tile_size, j + tile_size, 0)
            glVertex3f(i, j + tile_size, 0)
    glEnd()

    wall_height = 250
    glBegin(GL_QUADS)
    glColor3f(0.6, 0.5, 0.4) 
    
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, wall_height)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, wall_height)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, wall_height)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, wall_height)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, wall_height)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, wall_height)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, wall_height)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, wall_height)
    glEnd()

    sky_height = 1200
    glBegin(GL_QUADS)
    glColor3f(0.4, 0.6, 1.0) 
    FAR = GRID_LENGTH + 500
    glVertex3f(-FAR, -FAR, wall_height)
    glVertex3f(FAR, -FAR, wall_height)
    glVertex3f(FAR, FAR, wall_height)
    glVertex3f(-FAR, FAR, wall_height)
    glVertex3f(-FAR, -FAR, sky_height)
    glVertex3f(FAR, -FAR, sky_height)
    glVertex3f(FAR, FAR, sky_height)
    glVertex3f(-FAR, FAR, sky_height)
    glEnd()

    #Sun
    glPushMatrix()
    glTranslatef(1000, 1000, 600)
    glColor3f(1.0, 1.0, 0.8)
    gluSphere(gluNewQuadric(), 80, 20, 20)
    glPopMatrix()

    for obs in obstacles:
        glPushMatrix()
        glTranslatef(obs['x'], obs['y'], 0)
        glColor3f(0.5, 0.5, 0.5)
        glTranslatef(0, 0, obs['size']/4)
        glScalef(1.0, 1.0, 0.5)
        glutSolidCube(obs['size'])
        glColor3f(0.4, 0.4, 0.4)
        glTranslatef(0, 0, obs['size'])
        glScalef(0.7, 0.7, 1.0)
        glutSolidCube(obs['size'])
        glPopMatrix()

    #Command Base
    glPushMatrix()
    glTranslatef(0, 0, 0)
    # Wide Foundation
    glColor3f(0.25, 0.25, 0.25)
    glTranslatef(0, 0, 20)
    glPushMatrix()
    glScalef(2.0, 2.0, 0.4)
    glutSolidCube(100)
    glPopMatrix()
    # Main Bunker
    glColor3f(0.35, 0.35, 0.35)
    glTranslatef(0, 0, 30)
    glPushMatrix()
    glScalef(1.2, 1.2, 0.6)
    glutSolidCube(100)
    glPopMatrix()
    # Dome on top
    glTranslatef(0, 0, 35)
    glColor3f(0.7, 0.8, 0.9)
    gluSphere(gluNewQuadric(), 35, 20, 20)
    # Antenna
    glColor3f(0.1, 0.1, 0.1)
    glTranslatef(0, 0, 25)
    gluCylinder(gluNewQuadric(), 2, 0.5, 90, 10, 10)
    # Flag
    glColor3f(0.1, 0.8, 0.1) 
    glTranslatef(0, 0, 65) 
    glBegin(GL_QUADS)
    glVertex3f(0, 0, 0)
    glVertex3f(45, 0, 0)
    glVertex3f(45, 0, 25)
    glVertex3f(0, 0, 25)
    glEnd()
    glPopMatrix()

def draw_tank():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], 15)
    
    if game_over and player_armor <= 0:
        glRotatef(180, 1, 0, 0)
        glTranslatef(0, 0, -30)
        
    if shield_active:
        glPushMatrix()
        glColor3f(0.0, 0.8, 1.0)
        gluSphere(gluNewQuadric(), 40, 15, 15) 
        glPopMatrix()
    
    glPushMatrix()
    glRotatef(player_angle, 0, 0, 1)
    #Left Tread
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(-15, 0, 0)
    glScalef(0.5, 2.8, 0.6)
    glutSolidCube(20)
    glPopMatrix()
    #Right Tread
    glPushMatrix()
    glTranslatef(15, 0, 0)
    glScalef(0.5, 2.8, 0.6)
    glutSolidCube(20)
    glPopMatrix()
    #Main Chassis
    glColor3f(0.2, 0.4, 0.2)
    glPushMatrix()
    glScalef(1.3, 2.0, 0.8)
    glutSolidCube(20)
    glPopMatrix()
    #Engine details on back
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glTranslatef(0, -18, 5)
    glScalef(0.8, 0.4, 0.3)
    glutSolidCube(20)
    glPopMatrix()
    glPopMatrix()
    #Detailed Turret
    glPushMatrix()
    glRotatef(player_angle + turret_angle, 0, 0, 1)
    glColor3f(0.15, 0.35, 0.15)
    glTranslatef(0, 0, 15)
    gluSphere(gluNewQuadric(), 12, 15, 15)
    #Hatch on top
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix(); glTranslatef(0, 0, 10)
    gluSphere(gluNewQuadric(), 5, 10, 10)
    glPopMatrix()
    
    # Railgun beam
    if railgun_timer > 0:
        glPushMatrix()
        glTranslatef(0, 40, 0) 
        
        intensity = railgun_timer / 20.0
        
        # Outer blue beam
        glColor3f(0.0, 0.5 * intensity, 1.0 * intensity)
        glBegin(GL_QUADS)
        glVertex3f(-12, 0, 0)
        glVertex3f(12, 0, 0)
        glVertex3f(12, 3000, 0)
        glVertex3f(-12, 3000, 0)
        glEnd()
        
        # Inner white beam
        glColor3f(intensity, intensity, intensity)
        glBegin(GL_QUADS)
        glVertex3f(-4, 0, 0)
        glVertex3f(4, 0, 0)
        glVertex3f(4, 3000, 0)
        glVertex3f(-4, 3000, 0)
        glEnd()
        glPopMatrix()

    # Barrel
    glColor3f(0.3, 0.3, 0.3)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 2.5, 2, 40, 10, 10)
    glPopMatrix()
    glPopMatrix()

def draw_laser_sight():
    dir_x, dir_y, mx, my, _ = get_turret_aim()
    glColor3f(1.0, 0.0, 0.0)
    glPointSize(4)
    glBegin(GL_POINTS)
    for step in range(1, 20):
        reach = step * 30
        glVertex3f(mx + dir_x * reach, my + dir_y * reach, 15)
    glEnd()

def draw_entities():
    for b in bullets:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], 15)
        glRotatef(b['angle'], 0, 0, 1)
        
        if b['type'] == 'primary':
            glColor3f(1.0, 1.0, 0.0)
        elif b['type'] == 'secondary':
            glColor3f(1.0, 0.5, 0.0)
        elif b['type'] == 'enemy':
            glColor3f(1.0, 0.0, 1.0)
            
        glutSolidCube(b['size'])
        glPopMatrix()
        
    for exp in explosions:
        glPushMatrix()
        glTranslatef(exp['x'], exp['y'], 15)
        scale = exp['timer'] / 15.0
        glScalef(scale, scale, scale)
        glColor3f(1.0, 0.3, 0.0) 
        gluSphere(gluNewQuadric(), 80, 15, 15)
        glColor3f(1.0, 0.8, 0.0)
        gluSphere(gluNewQuadric(), 50, 15, 15)
        glColor3f(1.0, 1.0, 1.0)
        gluSphere(gluNewQuadric(), 20, 10, 10)
        glPopMatrix()

    for enemy in enemies:
        glPushMatrix()
        glTranslatef(enemy['x'], enemy['y'], 15)
        
        health_ratio = max(enemy['health'] / 20.0, 0.1)
        
        glColor3f(0.1, 0.1, 0.1)
        glPushMatrix()
        glTranslatef(-15, 0, 0)
        glScalef(0.5, 2.5, 0.6)
        glutSolidCube(20)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(15, 0, 0)
        glScalef(0.5, 2.5, 0.6)
        glutSolidCube(20);
        glPopMatrix()
        
        glColor3f(0.6 * health_ratio, 0.1, 0.1)
        glPushMatrix()
        glScalef(1.3, 2.0, 0.8)
        glutSolidCube(20)
        glPopMatrix()
        
        if enemy['target'] == 'base':
            tx, ty = 0, 0
        else:
            tx, ty = player_pos[0], player_pos[1]
            
        aim_angle = math.degrees(math.atan2(-(tx - enemy['x']), ty - enemy['y']))
        
        glRotatef(aim_angle, 0, 0, 1)
        glColor3f(0.3 * health_ratio, 0.0, 0.0)
        glTranslatef(0, 0, 12)
        gluSphere(gluNewQuadric(), 10, 10, 10)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 2, 2, 25, 10, 10)
        
        glPopMatrix()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()

    draw_environment()
    draw_entities()
    if not (game_over and player_armor <= 0):
        draw_laser_sight()
    draw_tank()

    draw_text(10, 770, f"Tank Armor: {int(player_armor)}%")
    draw_text(10, 740, f"Base Integrity: {int(base_integrity)}")
    draw_text(10, 710, f"Enemies Defeated: {enemies_destroyed} / {REQ_ELIMINATIONS}")
    
    weapon_text = "Primary (Machine Gun)" if current_weapon == 'primary' else "Secondary (HE Shell)"
    draw_text(10, 680, f"Equipped: {weapon_text} | HE Shells: {secondary_ammo}")
    draw_text(10, 650, "Space = Fire | Q = Switch Weapon | T = Camera")
    
    if shield_active:
        draw_text(10, 620, f"Shield Power: {int(shield_health)}")

    if railgun_cooldown == 0:
        draw_text(400, 750, "RAILGUN READY (Press C)")
    else:
        seconds_left = (railgun_cooldown // 120) + 1
        draw_text(400, 750, f"RAILGUN RECHARGING: {seconds_left} s")

    if game_over:
        if victory:
            draw_text(400, 450, "VICTORY! SIEGE BROKEN!")
        else:
            draw_text(400, 450, "CATASTROPHIC FAILURE!")
        draw_text(400, 400, "Press R to Restart")

    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"Operation: Armor Defense")

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutIdleFunc(idle)

    init_enemies()
    glutMainLoop()

if __name__ == "__main__":
    main()