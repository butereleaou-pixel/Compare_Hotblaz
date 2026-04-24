import threading
import time
import sys, os, msvcrt
import markdown
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import queue
import random
import cv2
import numpy as np
import pygame
import math
import atexit

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
lock = threading.Lock()

from Compare_Main import compare_chat, cycle_input, get_input_with_timeout
from Compare_Main import UN_THINKING_SERIE
from worker_messages import WORKER_MESSAGES, get_random_message

app = Flask(__name__)
CORS(app)

# Global variables
web_session_input_queue = {}
web_session_stream_buffer = {}
web_session_waiting = {}
web_session_active = {}
web_last_un_thinking_value = {}
web_parallel_mode_active = {}
web_message_index = {}
web_parallel_notification_sent = {}
web_parallel_message_timer = {}

# Pygame animation frame stream
frame_buffer = None
frame_lock = threading.Lock()
animation_running = False
pygame_screen = None
animation_thread = None

# Color definitions
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (120, 120, 120)
DARK_GRAY = (80, 80, 80)
LIGHT_GRAY = (200, 200, 200)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)
GREEN = (34, 139, 34)
DARK_GREEN = (20, 100, 20)
ORANGE = (255, 165, 0)
RED = (255, 50, 50)
BLUE = (50, 100, 255)
SKY_BLUE = (135, 206, 235)
YELLOW = (255, 255, 100)
PURPLE = (147, 112, 219)
PINK = (255, 182, 193)

PIXEL = 20

class PixelMan:
    """Side‑view pixel character"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.frame = 0
        
    def draw(self, screen, offsets):
        x, y = self.x, self.y
        
        head_offset = offsets.get('head', 0)
        for dx in range(4):
            for dy in range(3):
                pygame.draw.rect(screen, BLACK,
                    (x + dx * PIXEL, y + dy * PIXEL + head_offset, PIXEL - 2, PIXEL - 2))
        
        pygame.draw.rect(screen, WHITE, (x + PIXEL, y + PIXEL + head_offset, PIXEL - 4, PIXEL - 4))
        pygame.draw.rect(screen, BLACK, (x + PIXEL + 4, y + PIXEL + 2 + head_offset, 3, 3))
        
        mouth = offsets.get('mouth', 0)
        if mouth > 0:
            pygame.draw.rect(screen, BLACK, (x + PIXEL * 2, y + PIXEL * 2 + head_offset, PIXEL - 4, 3))
        
        body_offset = offsets.get('body', 0)
        body_y = y + 3 * PIXEL + body_offset
        sit = offsets.get('sit', False)
        body_h = 3 if not sit else 2
        for dx in range(3):
            for dy in range(body_h):
                pygame.draw.rect(screen, BLACK,
                    (x + dx * PIXEL, body_y + dy * PIXEL, PIXEL - 2, PIXEL - 2))
        
        arm_y = body_y + PIXEL
        arm_l_offset = offsets.get('arm_l', 0)
        arm_r_offset = offsets.get('arm_r', 0)
        arm_l_h = offsets.get('arm_l_h', PIXEL * 2)
        arm_r_h = offsets.get('arm_r_h', PIXEL * 2)
        
        pygame.draw.rect(screen, BLACK, 
            (x - PIXEL + arm_l_offset, arm_y, PIXEL - 2, arm_l_h))
        pygame.draw.rect(screen, BLACK, 
            (x + 3 * PIXEL + arm_r_offset, arm_y, PIXEL - 2, arm_r_h))
        
        leg_y = body_y + body_h * PIXEL
        leg_l_offset = offsets.get('leg_l', 0)
        leg_r_offset = offsets.get('leg_r', 0)
        leg_h = 3 if not sit else 1
        
        pygame.draw.rect(screen, BLACK, 
            (x + 0 * PIXEL + leg_l_offset, leg_y, PIXEL - 2, PIXEL * leg_h - 2))
        pygame.draw.rect(screen, BLACK, 
            (x + 2 * PIXEL + leg_r_offset, leg_y, PIXEL - 2, PIXEL * leg_h - 2))

class Scene:
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.scene_width = 400
        self.scene_height = 300
        
    def draw_background(self, screen, scene_type, offset_x=0, offset_y=0):
        x = self.center_x - self.scene_width // 2 + offset_x
        y = self.center_y - self.scene_height // 2 + offset_y
        w, h = self.scene_width, self.scene_height
        
        ground_y = y + 180
        pygame.draw.rect(screen, DARK_GREEN, (x, ground_y, w, h - 180))
        pygame.draw.rect(screen, GREEN, (x, ground_y - 5, w, 10))
        
        if scene_type == "office":
            pygame.draw.rect(screen, LIGHT_GRAY, (x + 20, y + 50, 80, 100))
            pygame.draw.rect(screen, GRAY, (x + 25, y + 55, 70, 90))
            pygame.draw.rect(screen, SKY_BLUE, (x + 250, y + 40, 60, 80))
            pygame.draw.rect(screen, BROWN, (x + 278, y + 40, 4, 80))
            pygame.draw.rect(screen, BROWN, (x + 250, y + 78, 60, 4))
            pygame.draw.circle(screen, WHITE, (x + 330, y + 30), 15)
            pygame.draw.line(screen, BLACK, (x + 330, y + 30), (x + 330, y + 22), 2)
            pygame.draw.line(screen, BLACK, (x + 330, y + 30), (x + 336, y + 30), 2)
        elif scene_type == "street":
            pygame.draw.rect(screen, GRAY, (x, y + 150, w, 30))
            for i in range(0, w, 40):
                pygame.draw.rect(screen, WHITE, (x + i + 20, y + 165, 20, 4))
            pygame.draw.rect(screen, DARK_GRAY, (x + 50, y + 100, 6, 80))
            pygame.draw.circle(screen, YELLOW, (x + 53, y + 95), 10)
            pygame.draw.rect(screen, BROWN, (x + 320, y + 120, 8, 60))
            pygame.draw.circle(screen, DARK_GREEN, (x + 324, y + 105), 20)
        elif scene_type == "park":
            pygame.draw.rect(screen, DARK_GREEN, (x, y + 150, w, h - 150))
            pygame.draw.rect(screen, RED, (x + 280, y + 165, 60, 40))
            for tx in [50, 200, 340]:
                pygame.draw.rect(screen, BROWN, (x + tx, y + 130, 8, 50))
                pygame.draw.circle(screen, DARK_GREEN, (x + tx + 4, y + 115), 18)
            for fx in [100, 150, 250]:
                pygame.draw.circle(screen, PINK, (x + fx, y + 170), 4)
                pygame.draw.circle(screen, YELLOW, (x + fx, y + 170), 2)
        elif scene_type == "gym":
            pygame.draw.rect(screen, (200, 150, 100), (x, y + 150, w, h - 150))
            pygame.draw.rect(screen, RED, (x + 150, y + 150, 100, 5))
            pygame.draw.rect(screen, RED, (x + 150, y + 195, 100, 5))
            pygame.draw.rect(screen, DARK_GRAY, (x + 320, y + 60, 8, 120))
            pygame.draw.rect(screen, RED, (x + 328, y + 60, 50, 8))
            pygame.draw.circle(screen, RED, (x + 378, y + 64), 12, 3)
        elif scene_type == "beach":
            pygame.draw.rect(screen, (255, 220, 150), (x, y + 160, w, h - 160))
            pygame.draw.rect(screen, SKY_BLUE, (x, y, w, 100))
            pygame.draw.circle(screen, YELLOW, (x + 350, y + 30), 25)
            for i in range(0, w, 30):
                pygame.draw.arc(screen, BLUE, (x + i, y + 155, 20, 15), 0, math.pi, 2)

def draw_office_items(screen, x, y, frame):
    pygame.draw.rect(screen, BROWN, (x + 60, y + 80, 100, 8))
    pygame.draw.rect(screen, BROWN, (x + 70, y + 88, 6, 50))
    pygame.draw.rect(screen, BROWN, (x + 150, y + 88, 6, 50))
    pygame.draw.rect(screen, DARK_GRAY, (x + 70, y + 30, 45, 35))
    pygame.draw.rect(screen, SKY_BLUE, (x + 75, y + 35, 35, 25))
    pygame.draw.rect(screen, DARK_GRAY, (x + 90, y + 65, 8, 15))
    if frame % 8 < 4:
        for i in range(3):
            pygame.draw.rect(screen, BLACK, (x + 80 + i * 8, y + 40, 4, 4))
    pygame.draw.rect(screen, WHITE, (x + 130, y + 72, 12, 12))
    pygame.draw.rect(screen, BROWN, (x + 133, y + 74, 6, 8))
    pygame.draw.rect(screen, DARK_GRAY, (x + 142, y + 76, 3, 6))

def draw_bicycle(screen, x, y, phase):
    spoke = phase * 0.2
    pygame.draw.circle(screen, BLACK, (x - 25, y + 100), 22, 3)
    for i in range(6):
        angle = spoke + i * math.pi / 3
        ex = x - 25 + math.cos(angle) * 18
        ey = y + 100 + math.sin(angle) * 18
        pygame.draw.line(screen, DARK_GRAY, (x - 25, y + 100), (ex, ey), 1)
    pygame.draw.circle(screen, BLACK, (x + 65, y + 100), 22, 3)
    for i in range(6):
        angle = spoke + i * math.pi / 3
        ex = x + 65 + math.cos(angle) * 18
        ey = y + 100 + math.sin(angle) * 18
        pygame.draw.line(screen, DARK_GRAY, (x + 65, y + 100), (ex, ey), 1)
    pygame.draw.line(screen, BLACK, (x - 25, y + 100), (x, y + 70), 4)
    pygame.draw.line(screen, BLACK, (x + 65, y + 100), (x + 35, y + 70), 4)
    pygame.draw.line(screen, BLACK, (x, y + 70), (x + 35, y + 70), 4)
    pygame.draw.line(screen, BLACK, (x, y + 70), (x + 15, y + 85), 4)
    pedal_x = x + 15 + math.sin(phase) * 12
    pedal_y = y + 85 + math.cos(phase) * 10
    pygame.draw.circle(screen, BLACK, (int(pedal_x), int(pedal_y)), 5)
    pygame.draw.line(screen, BLACK, (x + 35, y + 70), (x + 50, y + 60), 4)
    pygame.draw.line(screen, BLACK, (x + 50, y + 60), (x + 55, y + 65), 3)

def draw_basketball_action(screen, x, y, phase):
    pygame.draw.rect(screen, DARK_GRAY, (x + 100, y + 20, 8, 100))
    pygame.draw.rect(screen, RED, (x + 108, y + 20, 55, 8))
    pygame.draw.circle(screen, RED, (x + 163, y + 24), 14, 3)
    for i in range(4):
        pygame.draw.line(screen, DARK_GRAY, (x + 158 + i * 3, y + 38), 
                        (x + 156 + i * 5, y + 60), 2)
    if phase < 12:
        ball_phase = phase * 0.5
        ball_x = x + 50 + ball_phase * 8
        ball_y = y + 80 - abs(ball_phase - 6) * 8
        pygame.draw.circle(screen, ORANGE, (int(ball_x), int(ball_y)), 12)
        pygame.draw.line(screen, BLACK, (int(ball_x) - 8, int(ball_y)), 
                        (int(ball_x) + 8, int(ball_y)), 2)
        pygame.draw.line(screen, BLACK, (int(ball_x), int(ball_y) - 8), 
                        (int(ball_x), int(ball_y) + 8), 2)

def run_pygame_animation_background():
    """Run Pygame animation in background (no window) and capture frames"""
    global frame_buffer, animation_running, pygame_screen
    
    # Set env to prevent visible window
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    
    pygame.init()
    # Create hidden window
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    
    # Create offscreen surface for rendering
    W, H = 400, 250
    pygame_screen = pygame.Surface((W, H))
    
    man = PixelMan(175, 100)
    particles = []
    
    ACTION_DURATION = 90
    NUM_ACTIONS = 8
    CYCLE_FRAMES = ACTION_DURATION * NUM_ACTIONS
    frame_counter = 0
    
    animation_running = True
    
    def draw_particles(screen, x, y, particle_list):
        for p in particle_list:
            pygame.draw.circle(screen, p['color'], (p['x'], p['y']), p['size'])
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
        return [p for p in particle_list if p['life'] > 0]
    
    scale = 0.5
    
    while animation_running:
        frame_counter += 1
        pygame_screen.fill(SKY_BLUE)
        
        cycle_frame = frame_counter % CYCLE_FRAMES
        action_index = cycle_frame // ACTION_DURATION
        action_progress = cycle_frame % ACTION_DURATION
        
        x, y = 150, 100
        
        if action_index == 0:
            scene = Scene(x + 25, y + 40)
            scene.draw_background(pygame_screen, "office")
            draw_office_items(pygame_screen, x, y, frame_counter)
            key_press = math.sin(action_progress * 0.3) * 6
            man.draw(pygame_screen, {
                'head': 0, 'body': 2, 'arm_l': -6 + int(key_press),
                'arm_r': -4 - int(key_press * 0.5), 'leg_l': 4, 'leg_r': 6,
                'sit': True, 'mouth': 1 if action_progress % 20 < 10 else 0
            })
            if action_progress % 6 == 0:
                particles.append({'x': x + 43, 'y': y + 33, 'vx': random.randint(-2, 2), 
                                'vy': -2, 'size': 2, 'color': YELLOW, 'life': 10})
        elif action_index == 1:
            scene = Scene(x + 25, y + 40)
            scene.draw_background(pygame_screen, "street")
            swing = math.sin(action_progress * 0.3) * 15
            man.draw(pygame_screen, {
                'head': -2, 'body': 0, 'arm_l': int(swing * 0.5), 'arm_r': int(swing),
                'leg_l': -3 if swing > 0 else 0, 'leg_r': 0 if swing > 0 else -3, 'mouth': 1
            })
            mx = x + 4 * PIXEL + int(swing)
            my = y + 6 * PIXEL
            pygame.draw.rect(pygame_screen, BROWN, (mx, my, 6, 50))
            pygame.draw.rect(pygame_screen, DARK_GRAY, (mx - 6, my + 45, 18, 8))
            if action_progress % 4 == 0:
                particles.append({'x': mx + 5, 'y': my + 50, 'vx': random.randint(-3, 3),
                                'vy': random.randint(-5, -1), 'size': 3, 'color': DARK_GRAY, 'life': 20})
        elif action_index == 2:
            scene = Scene(x + 25, y + 40)
            scene.draw_background(pygame_screen, "park")
            pedal_phase = action_progress * 0.2
            leg_offset = int(math.sin(pedal_phase) * 10)
            arm_offset = int(math.sin(pedal_phase) * 8)
            man.draw(pygame_screen, {
                'head': -2, 'body': 2, 'arm_l': -3 + arm_offset, 'arm_r': -3 - arm_offset,
                'leg_l': leg_offset, 'leg_r': -leg_offset,
                'mouth': 1 if action_progress % 15 < 8 else 0
            })
            draw_bicycle(pygame_screen, x, y, pedal_phase)
            if action_progress % 3 == 0:
                particles.append({'x': x - 10, 'y': y + 100, 'vx': -5, 'vy': 0,
                                'size': 2, 'color': LIGHT_GRAY, 'life': 15})
        elif action_index == 3:
            scene = Scene(x + 25, y + 40)
            scene.draw_background(pygame_screen, "gym")
            phase = (action_progress // 6) % 10
            if phase < 4:
                jump = -phase * 3
                arm_up = phase * 4
            elif phase < 7:
                jump = -(8 - phase) * 3
                arm_up = (8 - phase) * 4
            else:
                jump = 0
                arm_up = 0
            man.draw(pygame_screen, {
                'head': jump, 'body': jump, 'arm_l': 0, 'arm_r': arm_up,
                'leg_l': 4 if phase > 2 else 0, 'leg_r': 0 if phase > 2 else 4,
                'mouth': 1 if phase > 4 else 0
            })
            draw_basketball_action(pygame_screen, x, y, phase)
            if phase > 2 and action_progress % 5 == 0:
                particles.append({'x': x - 10, 'y': y + 50, 'vx': random.randint(-2, 2),
                                'vy': random.randint(1, 3), 'size': 2, 'color': SKY_BLUE, 'life': 15})
        elif action_index == 4:
            scene = Scene(x + 25, y + 40)
            scene.draw_background(pygame_screen, "beach")
            run_phase = action_progress * 0.4
            leg_offset = int(math.sin(run_phase) * 12)
            arm_offset = int(math.sin(run_phase) * 10)
            man.draw(pygame_screen, {
                'head': -1, 'body': 1, 'arm_l': -2 + arm_offset, 'arm_r': -2 - arm_offset,
                'leg_l': leg_offset, 'leg_r': -leg_offset, 'mouth': 1
            })
            for i in range(0, 400, 40):
                offset = (action_progress * 2 + i) % 80
                pygame.draw.rect(pygame_screen, WHITE, (x - 50 + offset, y + 170, 20, 5))
            pygame.draw.circle(pygame_screen, RED, (x + 180, y + 40), 15)
            pygame.draw.line(pygame_screen, WHITE, (x + 175, y + 40), (x + 178, y + 35), 2)
            pygame.draw.line(pygame_screen, WHITE, (x + 178, y + 35), (x + 182, y + 48), 2)
            pygame.draw.line(pygame_screen, WHITE, (x + 182, y + 48), (x + 185, y + 40), 2)
            if action_progress % 4 == 0:
                particles.append({'x': x + 20, 'y': y + 170, 'vx': random.randint(-2, 2),
                                'vy': -2, 'size': 2, 'color': BROWN, 'life': 10})
        elif action_index == 5:
            scene = Scene(x + 25, y + 40)
            scene.draw_background(pygame_screen, "beach")
            swim_phase = action_progress * 0.3
            arm_l_offset = int(math.sin(swim_phase) * 15)
            arm_r_offset = int(math.sin(swim_phase + math.pi) * 15)
            man.draw(pygame_screen, {
                'head': -2, 'body': 0, 'arm_l': -10 + arm_l_offset, 'arm_r': -10 + arm_r_offset,
                'leg_l': 5, 'leg_r': -5, 'mouth': 0
            })
            for i in range(0, 400, 20):
                wave_y = math.sin(swim_phase * 0.3 + i * 0.1) * 3
                pygame.draw.line(pygame_screen, BLUE, (x - 50 + i, y + 120), 
                                (x - 50 + i + 15, y + 120 + wave_y), 2)
            for i in range(0, 400, 50):
                pygame.draw.circle(pygame_screen, RED, (x - 30 + i, y + 130), 3)
            for i in range(3):
                sx = x - 20 + (action_progress * 10 + i * 20) % 60
                sy = y + 110 + math.sin(action_progress * 5 + i) * 5
                pygame.draw.circle(pygame_screen, WHITE, (int(sx), int(sy)), 3)
            if action_progress % 3 == 0:
                particles.append({'x': x + 30, 'y': y + 120, 'vx': random.randint(-3, 3),
                                'vy': random.randint(-4, -1), 'size': 3, 'color': WHITE, 'life': 12})
        elif action_index == 6:
            scene = Scene(x + 25, y + 40)
            scene.draw_background(pygame_screen, "gym")
            lift_phase = action_progress * 0.2
            bar_height = int(abs(math.sin(lift_phase)) * 40)
            man.draw(pygame_screen, {
                'head': -bar_height // 3, 'body': 0, 'arm_l': -2, 'arm_r': -2,
                'leg_l': 2, 'leg_r': 2, 'mouth': 1 if bar_height > 20 else 0
            })
            bar_offset = abs(math.sin(lift_phase)) * 30
            pygame.draw.rect(pygame_screen, DARK_GRAY, (x + 20, y + 30 - bar_offset, 100, 8))
            pygame.draw.rect(pygame_screen, BLACK, (x + 18, y + 26 - bar_offset, 8, 16))
            pygame.draw.rect(pygame_screen, BLACK, (x + 114, y + 26 - bar_offset, 8, 16))
            for i in range(3):
                pygame.draw.rect(pygame_screen, GRAY, (x + 10 + i * 4, y + 28 - bar_offset, 4, 12))
                pygame.draw.rect(pygame_screen, GRAY, (x + 126 - i * 4, y + 28 - bar_offset, 4, 12))
            if bar_height > 30 and action_progress % 5 == 0:
                particles.append({'x': x - 5, 'y': y + 40, 'vx': random.randint(-2, 2),
                                'vy': random.randint(1, 4), 'size': 2, 'color': SKY_BLUE, 'life': 15})
        else:
            scene = Scene(x + 25, y + 40)
            scene.draw_background(pygame_screen, "park")
            yoga_phase = action_progress * 0.1
            body_offset = int(math.sin(yoga_phase) * 5)
            man.draw(pygame_screen, {
                'head': body_offset, 'body': body_offset, 'arm_l': 5 + body_offset,
                'arm_r': 5 - body_offset, 'leg_l': 3, 'leg_r': 3,
                'mouth': 1 if action_progress % 30 < 15 else 0
            })
            pygame.draw.rect(pygame_screen, PURPLE, (x - 20, y + 140, 180, 40), 3)
            pygame.draw.rect(pygame_screen, BROWN, (x + 130, y + 135, 6, 15))
            pygame.draw.circle(pygame_screen, YELLOW, (x + 133, y + 132), 3)
            for i in range(3):
                alpha = yoga_phase * 0.5 + i
                radius = 15 + math.sin(alpha) * 5
                pygame.draw.circle(pygame_screen, (200, 200, 100), (x + 60, y + 100), int(radius), 1)
            if action_progress % 10 == 0:
                particles.append({'x': x + 60, 'y': y + 100, 'vx': random.randint(-1, 1),
                                'vy': -1, 'size': 2, 'color': YELLOW, 'life': 30})
        
        particles = draw_particles(pygame_screen, x, y, particles)
        
        action_names = ["WORKING", "CLEANING", "CYCLING", "BASKETBALL", 
                        "JOGGING", "SWIMMING", "WEIGHT LIFTING", "YOGA"]
        
        font = pygame.font.Font(None, 18)
        font_small = pygame.font.Font(None, 14)
        
        action_text = font.render(f"{action_names[action_index]}", True, DARK_GRAY)
        pygame_screen.blit(action_text, (x + 30, y - 20))
        
        progress = action_progress / ACTION_DURATION
        pygame.draw.rect(pygame_screen, LIGHT_GRAY, (x + 20, y - 15, 120, 6))
        pygame.draw.rect(pygame_screen, BLUE, (x + 20, y - 15, int(120 * progress), 6))
        
        cycle_count = frame_counter // CYCLE_FRAMES + 1
        time_seconds = frame_counter // 30
        minutes = time_seconds // 60
        seconds = time_seconds % 60
        
        info_text = font_small.render(f"Cycle: {cycle_count} | {minutes:02d}:{seconds:02d}", True, DARK_GRAY)
        pygame_screen.blit(info_text, (5, 5))
        
        action_num = font_small.render(f"{action_index + 1}/{NUM_ACTIONS}", True, DARK_GRAY)
        pygame_screen.blit(action_num, (5, 20))
        
        with frame_lock:
            frame_array = pygame.surfarray.array3d(pygame_screen)
            frame_array = np.transpose(frame_array, (1, 0, 2))
            frame_buffer = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
        
        time.sleep(0.033)
    
    pygame.quit()

def generate_frames():
    """Generate MJPEG frame stream"""
    global frame_buffer, frame_lock
    while True:
        if frame_buffer is not None:
            with frame_lock:
                ret, buffer = cv2.imencode('.jpg', frame_buffer)
                frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            time.sleep(0.1)

def get_next_message(sid):
    """Get next message (rotating)"""
    if sid not in web_message_index:
        web_message_index[sid] = 0
    msg = WORKER_MESSAGES[web_message_index[sid] % len(WORKER_MESSAGES)]
    web_message_index[sid] += 1
    return msg

def extract_answer_from_full_text(full_text):
    separator = "-" * 80
    answer_marker = "【HERE IS THE ANSWER】:"
    
    if answer_marker in full_text:
        parts = full_text.split(answer_marker)
        if len(parts) >= 2:
            answer_part = parts[1]
            if separator in answer_part:
                answer_part = answer_part.split(separator)[0]
            return answer_part.strip()
    
    if separator in full_text:
        separator_count = full_text.count(separator)
        if separator_count >= 2:
            parts = full_text.split(separator)
            if len(parts) >= 3:
                return parts[1].strip()
    
    return None

def web_get_input_with_timeout(sid, timeout=30):
    web_session_waiting[sid] = True
    
    try:
        user_input = web_session_input_queue[sid].get(timeout=timeout)
        return user_input, False
    except queue.Empty:
        return "agree", True
    finally:
        web_session_waiting[sid] = False

def stream_answer_to_web(sid, answer_text):
    if web_parallel_mode_active.get(sid, False):
        web_session_stream_buffer[sid].append("__PARALLEL_MODE_END__")
        web_parallel_mode_active[sid] = False
    
    for char in answer_text:
        web_session_stream_buffer[sid].append(char)
        time.sleep(0.02)
    web_session_stream_buffer[sid].append(None)

def web_cycle_input(sid, user_input, is_auto_agree=False):
    captured_output = []
    original_print = print
    
    def captured_print(*args, **kwargs):
        text = ' '.join(str(arg) for arg in args)
        captured_output.append(text)
        original_print(*args, **kwargs)
    
    import builtins
    builtins.print = captured_print
    
    try:
        result = cycle_input(user_input, is_auto_agree=is_auto_agree)
    finally:
        builtins.print = original_print
    
    full_output = '\n'.join(captured_output)
    answer_text = extract_answer_from_full_text(full_output)
    
    if answer_text:
        stream_answer_to_web(sid, answer_text)
    else:
        if web_parallel_mode_active.get(sid, False):
            web_session_stream_buffer[sid].append("__PARALLEL_MODE_END__")
            web_parallel_mode_active[sid] = False
        error_msg = "Processing completed, but no answer generated"
        stream_answer_to_web(sid, error_msg)
    
    return result

def send_worker_message(sid):
    """Send status message every 10 seconds"""
    if web_parallel_mode_active.get(sid, False) and sid in web_session_stream_buffer:
        message = get_next_message(sid)
        web_session_stream_buffer[sid].append(f"__WORKER_MSG__{message}")
        if web_parallel_mode_active.get(sid, False):
            timer = threading.Timer(10.0, send_worker_message, args=[sid])
            timer.daemon = True
            timer.start()
            web_parallel_message_timer[sid] = timer

def start_background_animation():
    """Start background animation thread"""
    global animation_thread
    if animation_thread is None or not animation_thread.is_alive():
        animation_thread = threading.Thread(target=run_pygame_animation_background, daemon=True)
        animation_thread.start()
        print("🎬 Background Pygame animation started (hidden window)")

def monitor_un_thinking_status():
    while True:
        try:
            from Compare_Main import UN_THINKING_SERIE
            current_value = UN_THINKING_SERIE
            
            for sid in list(web_session_active.keys()):
                if web_session_active.get(sid, False):
                    if sid not in web_parallel_notification_sent:
                        web_parallel_notification_sent[sid] = False                    
                    if current_value == 0 and not web_parallel_notification_sent.get(sid, False):
                        print(f"[DEBUG] UN_THINKING_SERIE = 0, enable parallel mode {sid}")
                        web_session_stream_buffer[sid] = []
                        web_session_stream_buffer[sid].append("__PARALLEL_MODE_START__")
                        web_session_stream_buffer[sid].append(f"__WORKER_MSG__{get_next_message(sid)}")
                        web_parallel_mode_active[sid] = True
                        web_parallel_notification_sent[sid] = True
                        
                        if sid in web_parallel_message_timer:
                            web_parallel_message_timer[sid].cancel()
                        timer = threading.Timer(10.0, send_worker_message, args=[sid])
                        timer.daemon = True
                        timer.start()
                        web_parallel_message_timer[sid] = timer
                    
                    elif current_value != 0:
                        if web_parallel_notification_sent.get(sid, False):
                            print(f"[DEBUG] UN_THINKING_SERIE restored to {current_value}, reset status {sid}")
                            web_parallel_notification_sent[sid] = False
                            if web_parallel_mode_active.get(sid, False):
                                web_session_stream_buffer[sid].append("__PARALLEL_MODE_END__")
                                web_parallel_mode_active[sid] = False
                            if sid in web_parallel_message_timer:
                                web_parallel_message_timer[sid].cancel()
                                del web_parallel_message_timer[sid]
                    
                    web_last_un_thinking_value[sid] = current_value
        except Exception as e:
            print(f"Monitor thread error: {e}")
        
        time.sleep(0.3)

def main_loop_for_session(sid):
    web_session_active[sid] = True
    web_parallel_mode_active[sid] = False
    web_parallel_notification_sent[sid] = False
    
    try:
        while web_session_active[sid]:
            web_parallel_notification_sent[sid] = False
            
            user_content, is_auto = web_get_input_with_timeout(sid, timeout=30)
            if user_content.lower() in ["exit"]:
                break
            web_cycle_input(sid, user_content, is_auto_agree=is_auto)
    except Exception as e:
        print(f"Session {sid} error: {e}")
    finally:
        web_session_active[sid] = False
        web_parallel_mode_active[sid] = False
        web_parallel_notification_sent[sid] = False
        if sid in web_parallel_message_timer:
            web_parallel_message_timer[sid].cancel()
            del web_parallel_message_timer[sid]

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AI Chat - Pixel Workshop</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:#1a1a2e;font-family:Microsoft Yahei, 'Courier New', monospace;padding-bottom:120px}
        .chat{max-width:900px;margin:0 auto;padding:20px}
        .msg{margin:15px 0;}
        .msg-loading{margin:15px 0;}

        .user{text-align:right}
        .bot{text-align:left}

        .bot .bubble{
            display:inline-block;
            padding:14px 36px;
            border-radius:18px;
            max-width:85%;
            line-height:1.8;
            background:#16213e;
            color:#e0e0e0;
            border:1px solid #0f3460;
        }
        .bot .bubble p { margin-bottom: 1em !important; }
        .bot .bubble strong { color: #00d4ff; }
        .bot .bubble em { color: #ff6b6b; }

        .user .bubble{
            display:inline-block;
            padding:14px 36px;
            border-radius:18px;
            max-width:85%;
            line-height:1.8;
            background:#00d4ff;
            color:#1a1a2e;
        }

        .pixel-workshop {
            background: #0f0f1a;
            border: 2px solid #00d4ff;
            border-radius: 12px;
            padding: 15px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            box-shadow: 0 0 20px rgba(0,212,255,0.2);
            animation: glowPulse 2s ease-in-out infinite;
        }
        
        @keyframes glowPulse {
            0%, 100% { box-shadow: 0 0 20px rgba(0,212,255,0.2); border-color: #00d4ff; }
            50% { box-shadow: 0 0 40px rgba(0,212,255,0.5); border-color: #00ffaa; }
        }
        
        .pixel-worker {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        
        .pygame-embed {
            background: #000000;
            border-radius: 10px;
            overflow: hidden;
            border: 2px solid #00d4ff;
            box-shadow: 0 0 20px rgba(0,212,255,0.3);
            width: 400px;
            height: 250px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .pygame-embed img {
            display: block;
            width: 100%;
            height: 100%;
            object-fit: contain;
            object-position: center;
        }
        
        .animation-container {
            background: #0a0a1a;
            border-radius: 10px;
            padding: 10px;
            text-align: center;
        }
        
        .animation-status {
            margin-top: 8px;
            font-size: 11px;
            color: #00d4ff;
            font-family: monospace;
        }
        
        .worker-message {
            flex: 1;
            font-size: 14px;
            color: #00d4ff;
            background: rgba(0,212,255,0.1);
            padding: 10px 15px;
            border-radius: 8px;
            font-family: monospace;
            border-left: 3px solid #00d4ff;
            transition: all 0.3s ease;
        }
        
        .worker-message.update {
            animation: messageFlash 0.3s ease;
        }
        
        @keyframes messageFlash {
            0% { opacity: 0.5; border-left-color: #00ffaa; background: rgba(0,255,170,0.2); }
            100% { opacity: 1; border-left-color: #00d4ff; background: rgba(0,212,255,0.1); }
        }
        
        .pixel-progress {
            margin-top: 10px;
            height: 4px;
            background: #2a2a3e;
            border-radius: 2px;
            overflow: hidden;
        }
        
        .pixel-progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #00ffaa);
            width: 0%;
            animation: progress 3s ease-in-out infinite;
            border-radius: 2px;
        }
        
        @keyframes progress {
            0% { width: 0%; opacity: 0.5; }
            50% { width: 70%; opacity: 1; }
            100% { width: 100%; opacity: 0.5; }
        }
        
        .pixel-stats {
            display: flex;
            gap: 20px;
            margin-top: 12px;
            font-size: 10px;
            color: #888;
            font-family: monospace;
            flex-wrap: wrap;
        }
        
        .pixel-stat {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .pixel-stat span {
            animation: statPulse 1s ease-in-out infinite;
        }
        
        @keyframes statPulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
        }
        
        pre {
            background: #0d1117;
            border-radius: 8px;
            padding: 16px;
            overflow-x: auto;
            margin: 12px 0;
            border: 1px solid #30363d;
        }
        
        code {
            font-family: 'Courier New', 'Fira Code', monospace;
            font-size: 13px;
        }
        
        pre code {
            color: #e6edf3;
            line-height: 1.5;
            display: block;
        }
        
        .inline-code {
            background: #2d2d3d;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
            color: #00d4ff;
        }
        
        .loading {
            display:flex;
            align-items:center;
            gap:8px;
            font-size:14px;
            color:#666;
        }
        .spin {
            width:16px;
            height:16px;
            border:2px solid #eee;
            border-top:#3574F0;
            border-radius:50%;
            animation:spin 1s linear infinite
        }
        @keyframes spin{to{transform:rotate(360deg)}}

        .input-bar{
            position:fixed;
            bottom:0;
            left:0;
            right:0;
            background:#0f0f1a;
            padding:20px;
            border-top:1px solid #00d4ff;
        }
        .input-inner{
            max-width:900px;
            margin:0 auto;
            display:flex;
            gap:12px;
        }
        #input{
            flex:1;
            padding:12px 18px;
            background:#1a1a2e;
            color:#00d4ff;
            border:1px solid #00d4ff;
            border-radius:24px;
            outline:0;
            font-size:14px;
            font-family:monospace;
        }
        #input:focus{border-color:#00ffaa; box-shadow:0 0 10px rgba(0,212,255,0.3);}
        #send{
            padding:12px 24px;
            background:#00d4ff;
            color:#1a1a2e;
            border:0;
            border-radius:24px;
            cursor:pointer;
            font-size:14px;
            font-weight:bold;
        }
        #send:hover{background:#00ffaa;}
        
        .streaming-cursor {
            display: inline-block;
            width: 2px;
            height: 1.2em;
            background-color: #00d4ff;
            margin-left: 2px;
            animation: blink 1s infinite;
            vertical-align: middle;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
    </style>
</head>
<body>
    <div class="chat" id="chat"></div>
    <div class="input-bar">
        <div class="input-inner">
            <input id="input" placeholder="Type your message...">
            <button id="send">Send</button>
        </div>
    </div>

    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('input');
        const send = document.getElementById('send');
        
        let sessionId = Date.now();
        let eventSource = null;
        let currentAnswerDiv = null;
        let currentBubble = null;
        let currentParallelDiv = null;
        let answerBuffer = '';
        let isStreaming = false;
        let parallelModeActive = false;
        
        function showParallelModeStart(initialMessage) {
            if (currentParallelDiv) return;
            
            let container = document.createElement('div');
            container.className = 'pixel-workshop';
            container.innerHTML = `
                <div class="pixel-worker">
                    <div class="animation-container">
                        <div class="pygame-embed">
                            <img src="/video_feed" alt="Pixel Animation" id="animationFrame">
                        </div>
                        <div class="animation-status">
                            🎮 System working - animation active
                        </div>
                    </div>
                    <div class="worker-message" id="workerMessage">${escapeHtml(initialMessage) || '🔄 Entering parallel comparison mode...'}</div>
                </div>
                <div class="pixel-progress">
                    <div class="pixel-progress-bar"></div>
                </div>
                <div class="pixel-stats">
                    <div class="pixel-stat"><span>⚡</span> Dual Model Parallel Inference</div>
                    <div class="pixel-stat"><span>📊</span> Real-time Comparison</div>
                    <div class="pixel-stat"><span>🎯</span> Quality Evaluation</div>
                    <div class="pixel-stat"><span>🔄</span> Auto Message Every 10s</div>
                    <div class="pixel-stat"><span>🎮</span> Embedded Pygame Animation</div>
                </div>
            `;
            chat.appendChild(container);
            currentParallelDiv = container;
            parallelModeActive = true;
            
            window.scrollTo(0, document.body.scrollHeight);
        }
        
        function escapeHtml(text) {
            let div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function updateWorkerMessage(message) {
            if (currentParallelDiv) {
                const msgDiv = currentParallelDiv.querySelector('.worker-message');
                if (msgDiv) {
                    msgDiv.classList.add('update');
                    msgDiv.innerHTML = escapeHtml(message);
                    setTimeout(() => {
                        if (msgDiv) msgDiv.classList.remove('update');
                    }, 300);
                }
            }
        }
        
        function hideParallelMode() {
            if (currentParallelDiv) {
                currentParallelDiv.style.transition = 'opacity 0.3s';
                currentParallelDiv.style.opacity = '0';
                setTimeout(() => {
                    if (currentParallelDiv && currentParallelDiv.parentNode) {
                        currentParallelDiv.remove();
                        currentParallelDiv = null;
                    }
                }, 300);
            }
            parallelModeActive = false;
        }
        
        function renderMarkdownLive(text) {
            if (!text) return '';
            
            let html = text;
            let codeBlocks = [];
            
            html = html.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, function(match, lang, code) {
                let idx = codeBlocks.length;
                codeBlocks.push({ lang: lang || 'text', code: code.trim() });
                return `__CODEBLOCK_${idx}__`;
            });
            
            html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
            
            html = html.replace(/[&<>]/g, function(m) {
                if (m === '&') return '&amp;';
                if (m === '<') return '&lt;';
                if (m === '>') return '&gt;';
                return m;
            });
            
            html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
            html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
            html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
            
            html = html.replace(/\\*\\*(.+?)\\*\\*/gs, '<strong>$1</strong>');
            
            html = html.replace(/\\*(?!\\*)(.+?)(?<!\\*)\\*/gs, '<em>$1</em>');
            
            html = html.replace(/\\n/g, '<br>');
            
            html = html.replace(/__CODEBLOCK_(\\d+)__/g, function(match, idx) {
                let block = codeBlocks[parseInt(idx)];
                let escapedCode = escapeHtml(block.code);
                return `<pre><code class="language-${block.lang}">${escapedCode}</code></pre>`;
            });
            
            return html;
        }
        
        function appendStreamContent(char, isComplete = false) {
            if (!currentBubble) return;
            
            if (!isComplete) {
                answerBuffer += char;
                let renderedHtml = renderMarkdownLive(answerBuffer);
                currentBubble.innerHTML = renderedHtml;
                
                if (!currentBubble.querySelector('.streaming-cursor')) {
                    let cursor = document.createElement('span');
                    cursor.className = 'streaming-cursor';
                    currentBubble.appendChild(cursor);
                }
                window.scrollTo(0, document.body.scrollHeight);
            } else {
                let renderedHtml = renderMarkdownLive(answerBuffer);
                currentBubble.innerHTML = renderedHtml;
                let cursor = currentBubble.querySelector('.streaming-cursor');
                if (cursor) cursor.remove();
                currentAnswerDiv = null;
                currentBubble = null;
                isStreaming = false;
            }
        }
        
        function resetForNewMessage() {
            answerBuffer = '';
            hideParallelMode();
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
            isStreaming = true;
            parallelModeActive = false;
        }
        
        function sendMsg(){
            let t = input.value.trim();
            if(!t) return;
            
            resetForNewMessage();
            
            let u = document.createElement('div');
            u.className='msg user';
            u.innerHTML=`<div class="bubble">${escapeHtml(t)}</div>`;
            chat.appendChild(u);
            
            let b = document.createElement('div');
            b.className='msg bot msg-loading';
            b.innerHTML=`<div class="bubble bubble-loading"><div class="loading"><div class="spin"></div><span>AI Thinking - may take 1-10 minutes...</span></div></div>`;
            chat.appendChild(b);
            currentAnswerDiv = b;
            currentBubble = b.querySelector('.bubble');
            input.value='';
            
            connect();
            
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_id: sessionId, msg: t})
            }).catch(err => console.error('Send failed:', err));
        }
        
        function connect() {
            if (eventSource) {
                eventSource.close();
            }
            
            eventSource = new EventSource('/stream/' + sessionId);
            
            eventSource.onmessage = function(e) {
                try {
                    let data = JSON.parse(e.data);
                    
                    if (data.type === 'stream') {
                        if (data.content === null) {
                            if (currentAnswerDiv && isStreaming) {
                                currentAnswerDiv.classList.remove('msg-loading');
                                currentBubble.classList.remove('bubble-loading');
                                appendStreamContent('', true);
                            }
                            hideParallelMode();
                        } else if (data.content === '__PARALLEL_MODE_START__') {
                            console.log('Parallel mode started');
                        } else if (data.content === '__PARALLEL_MODE_END__') {
                            console.log('Parallel mode stopped');
                            hideParallelMode();
                        } else if (data.content && data.content.startsWith('__WORKER_MSG__')) {
                            const msg = data.content.substring('__WORKER_MSG__'.length);
                            if (!parallelModeActive) {
                                showParallelModeStart(msg);
                            } else {
                                updateWorkerMessage(msg);
                            }
                        } else {
                            if (currentAnswerDiv && isStreaming) {
                                currentAnswerDiv.classList.remove('msg-loading');
                                currentBubble.classList.remove('bubble-loading');
                                appendStreamContent(data.content, false);
                            }
                        }
                    }
                } catch(err) {
                    console.error('Parse error:', err);
                }
            };
            
            eventSource.onerror = function(err) {
                console.error('SSE error:', err);
            };
        }
        
        send.onclick = sendMsg;
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendMsg();
        });
        
        connect();
        
        setTimeout(() => {
            let welcome = document.createElement('div');
            welcome.className='msg bot';
            welcome.innerHTML=`<div class="bubble">👋 Hello! I'm your AI assistant. How can I help you today?</div>`;
            chat.appendChild(welcome);
        }, 500);
    </script>
</body>
</html>
'''

@app.route('/video_feed')
def video_feed():
    """Video stream route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    msg = data.get('msg', '')
    sid = str(data.get('session_id'))
    
    if sid not in web_session_input_queue:
        web_session_input_queue[sid] = queue.Queue()
        web_session_stream_buffer[sid] = []
        web_session_waiting[sid] = False
        web_session_active[sid] = False
        web_parallel_notification_sent[sid] = False
        
        def run():
            main_loop_for_session(sid)
        
        threading.Thread(target=run, daemon=True).start()
    
    web_parallel_notification_sent[sid] = False
    web_session_stream_buffer[sid] = []
    web_session_input_queue[sid].put(msg)
    
    return jsonify({"ok": 1})

@app.route('/stream/<sid>')
def stream(sid):
    def gen():
        import json
        last_char_count = 0
        
        while True:
            if sid in web_session_stream_buffer:
                chars = web_session_stream_buffer[sid]
                
                while last_char_count < len(chars):
                    char = chars[last_char_count]
                    yield f"data: {json.dumps({'type': 'stream', 'content': char})}\n\n"
                    last_char_count += 1
                    
                    if char is None:
                        break
            
            time.sleep(0.02)
    
    return Response(gen(), mimetype="text/event-stream")

monitor_thread = threading.Thread(target=monitor_un_thinking_status, daemon=True)
monitor_thread.start()

# Start background animation (silent, no visible window)
start_background_animation()

if __name__ == '__main__':
    print("✅ System Started: Pixel Workshop")
    print("📌 Access http://127.0.0.1:5123")
    print("🎮 Pygame animation running in background (no visible window)")
    print("   Animation will appear in web page when parallel mode is activated")
    
    app.run(
        host="127.0.0.1",
        port=5123,
        debug=False,
        threaded=True,
        use_reloader=False
    )