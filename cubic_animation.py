import pygame
import math
import random

# 初始化
pygame.init()
W, H = 800, 500
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Side Pixel Man - Working & Sports")
clock = pygame.time.Clock()

# 颜色
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
    """侧面像素小人"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.frame = 0
        
    def draw(self, screen, offsets):
        x, y = self.x, self.y
        
        # 头部
        head_offset = offsets.get('head', 0)
        for dx in range(4):
            for dy in range(3):
                pygame.draw.rect(screen, BLACK,
                    (x + dx * PIXEL, y + dy * PIXEL + head_offset, PIXEL - 2, PIXEL - 2))
        
        # 眼睛
        eye_offset = offsets.get('eye', 0)
        pygame.draw.rect(screen, WHITE, (x + PIXEL, y + PIXEL + head_offset, PIXEL - 4, PIXEL - 4))
        pygame.draw.rect(screen, BLACK, (x + PIXEL + 4, y + PIXEL + 2 + head_offset, 3, 3))
        
        # 嘴巴
        mouth = offsets.get('mouth', 0)
        if mouth > 0:
            pygame.draw.rect(screen, BLACK, (x + PIXEL * 2, y + PIXEL * 2 + head_offset, PIXEL - 4, 3))
        
        # 身体
        body_offset = offsets.get('body', 0)
        body_y = y + 3 * PIXEL + body_offset
        sit = offsets.get('sit', False)
        body_h = 3 if not sit else 2
        for dx in range(3):
            for dy in range(body_h):
                pygame.draw.rect(screen, BLACK,
                    (x + dx * PIXEL, body_y + dy * PIXEL, PIXEL - 2, PIXEL - 2))
        
        # 手臂
        arm_y = body_y + PIXEL
        arm_l_offset = offsets.get('arm_l', 0)
        arm_r_offset = offsets.get('arm_r', 0)
        arm_l_h = offsets.get('arm_l_h', PIXEL * 2)
        arm_r_h = offsets.get('arm_r_h', PIXEL * 2)
        
        pygame.draw.rect(screen, BLACK, 
            (x - PIXEL + arm_l_offset, arm_y, PIXEL - 2, arm_l_h))
        pygame.draw.rect(screen, BLACK, 
            (x + 3 * PIXEL + arm_r_offset, arm_y, PIXEL - 2, arm_r_h))
        
        # 腿
        leg_y = body_y + body_h * PIXEL
        leg_l_offset = offsets.get('leg_l', 0)
        leg_r_offset = offsets.get('leg_r', 0)
        leg_h = 3 if not sit else 1
        
        pygame.draw.rect(screen, BLACK, 
            (x + 0 * PIXEL + leg_l_offset, leg_y, PIXEL - 2, PIXEL * leg_h - 2))
        pygame.draw.rect(screen, BLACK, 
            (x + 2 * PIXEL + leg_r_offset, leg_y, PIXEL - 2, PIXEL * leg_h - 2))

class Scene:
    """场景管理器 - 背景聚焦在小人周围"""
    
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.scene_width = 400
        self.scene_height = 300
        
    def draw_background(self, screen, scene_type, offset_x=0, offset_y=0):
        """绘制局部背景"""
        x = self.center_x - self.scene_width // 2 + offset_x
        y = self.center_y - self.scene_height // 2 + offset_y
        w, h = self.scene_width, self.scene_height
        
        # 地面
        ground_y = y + 180
        pygame.draw.rect(screen, DARK_GREEN, (x, ground_y, w, h - 180))
        pygame.draw.rect(screen, GREEN, (x, ground_y - 5, w, 10))
        
        # 根据场景类型添加装饰
        if scene_type == "office":
            # 办公室背景
            pygame.draw.rect(screen, LIGHT_GRAY, (x + 20, y + 50, 80, 100))
            pygame.draw.rect(screen, GRAY, (x + 25, y + 55, 70, 90))
            # 窗户
            pygame.draw.rect(screen, SKY_BLUE, (x + 250, y + 40, 60, 80))
            pygame.draw.rect(screen, BROWN, (x + 278, y + 40, 4, 80))
            pygame.draw.rect(screen, BROWN, (x + 250, y + 78, 60, 4))
            # 时钟
            pygame.draw.circle(screen, WHITE, (x + 330, y + 30), 15)
            pygame.draw.line(screen, BLACK, (x + 330, y + 30), (x + 330, y + 22), 2)
            pygame.draw.line(screen, BLACK, (x + 330, y + 30), (x + 336, y + 30), 2)
            
        elif scene_type == "street":
            # 街道背景
            pygame.draw.rect(screen, GRAY, (x, y + 150, w, 30))
            for i in range(0, w, 40):
                pygame.draw.rect(screen, WHITE, (x + i + 20, y + 165, 20, 4))
            # 路灯
            pygame.draw.rect(screen, DARK_GRAY, (x + 50, y + 100, 6, 80))
            pygame.draw.circle(screen, YELLOW, (x + 53, y + 95), 10)
            # 树木
            pygame.draw.rect(screen, BROWN, (x + 320, y + 120, 8, 60))
            pygame.draw.circle(screen, DARK_GREEN, (x + 324, y + 105), 20)
            
        elif scene_type == "park":
            # 公园背景
            pygame.draw.rect(screen, DARK_GREEN, (x, y + 150, w, h - 150))
            # 野餐垫
            pygame.draw.rect(screen, RED, (x + 280, y + 165, 60, 40))
            # 树木
            for tx in [50, 200, 340]:
                pygame.draw.rect(screen, BROWN, (x + tx, y + 130, 8, 50))
                pygame.draw.circle(screen, DARK_GREEN, (x + tx + 4, y + 115), 18)
            # 花朵
            for fx in [100, 150, 250]:
                pygame.draw.circle(screen, PINK, (x + fx, y + 170), 4)
                pygame.draw.circle(screen, YELLOW, (x + fx, y + 170), 2)
                
        elif scene_type == "gym":
            # 篮球场背景
            pygame.draw.rect(screen, (200, 150, 100), (x, y + 150, w, h - 150))
            pygame.draw.rect(screen, RED, (x + 150, y + 150, 100, 5))
            pygame.draw.rect(screen, RED, (x + 150, y + 195, 100, 5))
            # 篮球架
            pygame.draw.rect(screen, DARK_GRAY, (x + 320, y + 60, 8, 120))
            pygame.draw.rect(screen, RED, (x + 328, y + 60, 50, 8))
            pygame.draw.circle(screen, RED, (x + 378, y + 64), 12, 3)
            
        elif scene_type == "beach":
            # 海滩背景
            pygame.draw.rect(screen, (255, 220, 150), (x, y + 160, w, h - 160))
            pygame.draw.rect(screen, SKY_BLUE, (x, y, w, 100))
            # 太阳
            pygame.draw.circle(screen, YELLOW, (x + 350, y + 30), 25)
            # 海浪
            for i in range(0, w, 30):
                pygame.draw.arc(screen, BLUE, (x + i, y + 155, 20, 15), 0, math.pi, 2)
                
        elif scene_type == "snow":
            # 雪地背景
            pygame.draw.rect(screen, WHITE, (x, y + 160, w, h - 160))
            pygame.draw.rect(screen, LIGHT_GRAY, (x, y + 155, w, 10))
            # 雪人
            pygame.draw.circle(screen, WHITE, (x + 330, y + 165), 15)
            pygame.draw.circle(screen, WHITE, (x + 330, y + 145), 12)
            pygame.draw.circle(screen, WHITE, (x + 330, y + 130), 9)
            pygame.draw.circle(screen, BLACK, (x + 326, y + 127), 2)
            pygame.draw.circle(screen, BLACK, (x + 334, y + 127), 2)
            # 雪花
            for _ in range(20):
                sx = x + random.randint(0, w)
                sy = y + random.randint(0, h)
                pygame.draw.circle(screen, (200, 200, 255), (sx, sy), 2)

def draw_office_items(screen, x, y, frame):
    """办公室物品"""
    # 桌子
    pygame.draw.rect(screen, BROWN, (x + 60, y + 80, 100, 8))
    pygame.draw.rect(screen, BROWN, (x + 70, y + 88, 6, 50))
    pygame.draw.rect(screen, BROWN, (x + 150, y + 88, 6, 50))
    # 电脑
    pygame.draw.rect(screen, DARK_GRAY, (x + 70, y + 30, 45, 35))
    pygame.draw.rect(screen, SKY_BLUE, (x + 75, y + 35, 35, 25))
    pygame.draw.rect(screen, DARK_GRAY, (x + 90, y + 65, 8, 15))
    # 屏幕内容（闪烁）
    if frame % 8 < 4:
        for i in range(3):
            pygame.draw.rect(screen, BLACK, (x + 80 + i * 8, y + 40, 4, 4))
    # 咖啡杯
    pygame.draw.rect(screen, WHITE, (x + 130, y + 72, 12, 12))
    pygame.draw.rect(screen, BROWN, (x + 133, y + 74, 6, 8))
    pygame.draw.rect(screen, DARK_GRAY, (x + 142, y + 76, 3, 6))

def draw_bicycle(screen, x, y, phase):
    """自行车"""
    # 车轮辐条动画
    spoke = phase * 0.2
    # 后轮
    pygame.draw.circle(screen, BLACK, (x - 25, y + 100), 22, 3)
    for i in range(6):
        angle = spoke + i * math.pi / 3
        ex = x - 25 + math.cos(angle) * 18
        ey = y + 100 + math.sin(angle) * 18
        pygame.draw.line(screen, DARK_GRAY, (x - 25, y + 100), (ex, ey), 1)
    # 前轮
    pygame.draw.circle(screen, BLACK, (x + 65, y + 100), 22, 3)
    for i in range(6):
        angle = spoke + i * math.pi / 3
        ex = x + 65 + math.cos(angle) * 18
        ey = y + 100 + math.sin(angle) * 18
        pygame.draw.line(screen, DARK_GRAY, (x + 65, y + 100), (ex, ey), 1)
    # 车架
    pygame.draw.line(screen, BLACK, (x - 25, y + 100), (x, y + 70), 4)
    pygame.draw.line(screen, BLACK, (x + 65, y + 100), (x + 35, y + 70), 4)
    pygame.draw.line(screen, BLACK, (x, y + 70), (x + 35, y + 70), 4)
    pygame.draw.line(screen, BLACK, (x, y + 70), (x + 15, y + 85), 4)
    # 脚踏板
    pedal_x = x + 15 + math.sin(phase) * 12
    pedal_y = y + 85 + math.cos(phase) * 10
    pygame.draw.circle(screen, BLACK, (int(pedal_x), int(pedal_y)), 5)
    # 车把
    pygame.draw.line(screen, BLACK, (x + 35, y + 70), (x + 50, y + 60), 4)
    pygame.draw.line(screen, BLACK, (x + 50, y + 60), (x + 55, y + 65), 3)

def draw_basketball_action(screen, x, y, phase):
    """篮球动作"""
    # 篮球架
    pygame.draw.rect(screen, DARK_GRAY, (x + 100, y + 20, 8, 100))
    pygame.draw.rect(screen, RED, (x + 108, y + 20, 55, 8))
    pygame.draw.circle(screen, RED, (x + 163, y + 24), 14, 3)
    # 篮网
    for i in range(4):
        pygame.draw.line(screen, DARK_GRAY, (x + 158 + i * 3, y + 38), 
                        (x + 156 + i * 5, y + 60), 2)
    # 篮球轨迹
    if phase < 12:
        ball_phase = phase * 0.5
        ball_x = x + 50 + ball_phase * 8
        ball_y = y + 80 - abs(ball_phase - 6) * 8
        pygame.draw.circle(screen, ORANGE, (int(ball_x), int(ball_y)), 12)
        pygame.draw.line(screen, BLACK, (int(ball_x) - 8, int(ball_y)), 
                        (int(ball_x) + 8, int(ball_y)), 2)
        pygame.draw.line(screen, BLACK, (int(ball_x), int(ball_y) - 8), 
                        (int(ball_x), int(ball_y) + 8), 2)

def draw_jogging_scene(screen, x, y, phase):
    """慢跑场景"""
    # 跑道
    for i in range(0, 400, 40):
        offset = (phase * 2 + i) % 80
        pygame.draw.rect(screen, WHITE, (x - 50 + offset, y + 170, 20, 5))
    # 心率图标
    pygame.draw.circle(screen, RED, (x + 180, y + 40), 15)
    pygame.draw.line(screen, WHITE, (x + 175, y + 40), (x + 178, y + 35), 2)
    pygame.draw.line(screen, WHITE, (x + 178, y + 35), (x + 182, y + 48), 2)
    pygame.draw.line(screen, WHITE, (x + 182, y + 48), (x + 185, y + 40), 2)

def draw_swimming(screen, x, y, phase):
    """游泳动作"""
    # 水面
    for i in range(0, 400, 20):
        wave_y = math.sin(phase * 0.3 + i * 0.1) * 3
        pygame.draw.line(screen, BLUE, (x - 50 + i, y + 120), 
                        (x - 50 + i + 15, y + 120 + wave_y), 2)
    # 泳道线
    for i in range(0, 400, 50):
        pygame.draw.circle(screen, RED, (x - 30 + i, y + 130), 3)
    # 水花
    for i in range(3):
        sx = x - 20 + (phase * 10 + i * 20) % 60
        sy = y + 110 + math.sin(phase * 5 + i) * 5
        pygame.draw.circle(screen, WHITE, (int(sx), int(sy)), 3)

def draw_weight_lifting(screen, x, y, phase):
    """举重"""
    # 杠铃
    bar_offset = abs(math.sin(phase * 0.3)) * 30
    pygame.draw.rect(screen, DARK_GRAY, (x + 20, y + 30 - bar_offset, 100, 8))
    pygame.draw.rect(screen, BLACK, (x + 18, y + 26 - bar_offset, 8, 16))
    pygame.draw.rect(screen, BLACK, (x + 114, y + 26 - bar_offset, 8, 16))
    # 重量片
    for i in range(3):
        pygame.draw.rect(screen, GRAY, (x + 10 + i * 4, y + 28 - bar_offset, 4, 12))
        pygame.draw.rect(screen, GRAY, (x + 126 - i * 4, y + 28 - bar_offset, 4, 12))

def draw_yoga(screen, x, y, phase):
    """瑜伽"""
    # 瑜伽垫
    pygame.draw.rect(screen, PURPLE, (x - 20, y + 140, 180, 40), 3)
    # 香薰
    pygame.draw.rect(screen, BROWN, (x + 130, y + 135, 6, 15))
    pygame.draw.circle(screen, YELLOW, (x + 133, y + 132), 3)
    # 光环效果
    for i in range(3):
        alpha = phase * 0.5 + i
        radius = 15 + math.sin(alpha) * 5
        pygame.draw.circle(screen, (200, 200, 100), (x + 60, y + 100), int(radius), 1)

def draw_particles(screen, x, y, particle_list):
    """绘制粒子效果"""
    for p in particle_list:
        pygame.draw.circle(screen, p['color'], (p['x'], p['y']), p['size'])
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['life'] -= 1
    return [p for p in particle_list if p['life'] > 0]

running = True
frame = 0
man = PixelMan(350, 200)
particles = []

# 动作序列 - 8个动作，每个90帧 = 720帧 @30fps = 24秒一个循环
# 循环5次 = 120秒 = 2分钟，循环10次 = 4分钟
ACTION_DURATION = 90  # 每个动作90帧 (3秒)
NUM_ACTIONS = 8
CYCLE_FRAMES = ACTION_DURATION * NUM_ACTIONS  # 720帧 = 24秒

while running:
    clock.tick(30)
    frame += 1
    screen.fill(SKY_BLUE)
    
    # 循环帧 (支持2-5分钟，自动重复)
    cycle_frame = frame % CYCLE_FRAMES
    action_index = cycle_frame // ACTION_DURATION
    action_progress = cycle_frame % ACTION_DURATION
    
    x, y = 300, 200
    
    # 退出事件
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
    
    # 根据动作选择场景和动画
    # 动作0: 办公室工作
    if action_index == 0:
        scene = Scene(x + 50, y + 80)
        scene.draw_background(screen, "office")
        draw_office_items(screen, x, y, frame)
        
        key_press = math.sin(action_progress * 0.3) * 6
        man.draw(screen, {
            'head': 0,
            'body': 2,
            'arm_l': -6 + int(key_press),
            'arm_r': -4 - int(key_press * 0.5),
            'leg_l': 4,
            'leg_r': 6,
            'sit': True,
            'mouth': 1 if action_progress % 20 < 10 else 0
        })
        
        # 添加粒子效果（键盘按键火花）
        if action_progress % 6 == 0:
            particles.append({'x': x + 85, 'y': y + 65, 'vx': random.randint(-2, 2), 
                            'vy': -2, 'size': 2, 'color': YELLOW, 'life': 10})
    
    # 动作1: 打扫卫生
    elif action_index == 1:
        scene = Scene(x + 50, y + 80)
        scene.draw_background(screen, "street")
        
        swing = math.sin(action_progress * 0.3) * 15
        man.draw(screen, {
            'head': -2,
            'body': 0,
            'arm_l': int(swing * 0.5),
            'arm_r': int(swing),
            'leg_l': -3 if swing > 0 else 0,
            'leg_r': 0 if swing > 0 else -3,
            'mouth': 1
        })
        
        # 扫把
        mx = x + 4 * PIXEL + int(swing)
        my = y + 6 * PIXEL
        pygame.draw.rect(screen, BROWN, (mx, my, 6, 50))
        pygame.draw.rect(screen, DARK_GRAY, (mx - 6, my + 45, 18, 8))
        
        # 灰尘粒子
        if action_progress % 4 == 0:
            particles.append({'x': mx + 5, 'y': my + 50, 'vx': random.randint(-3, 3),
                            'vy': random.randint(-5, -1), 'size': 3, 'color': DARK_GRAY, 'life': 20})
    
    # 动作2: 骑自行车
    elif action_index == 2:
        scene = Scene(x + 50, y + 80)
        scene.draw_background(screen, "park")
        
        pedal_phase = action_progress * 0.2
        leg_offset = int(math.sin(pedal_phase) * 10)
        arm_offset = int(math.sin(pedal_phase) * 8)
        
        man.draw(screen, {
            'head': -2,
            'body': 2,
            'arm_l': -3 + arm_offset,
            'arm_r': -3 - arm_offset,
            'leg_l': leg_offset,
            'leg_r': -leg_offset,
            'mouth': 1 if action_progress % 15 < 8 else 0
        })
        
        draw_bicycle(screen, x, y, pedal_phase)
        
        # 速度线粒子
        if action_progress % 3 == 0:
            particles.append({'x': x - 10, 'y': y + 100, 'vx': -5, 'vy': 0,
                            'size': 2, 'color': LIGHT_GRAY, 'life': 15})
    
    # 动作3: 打篮球
    elif action_index == 3:
        scene = Scene(x + 50, y + 80)
        scene.draw_background(screen, "gym")
        
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
        
        man.draw(screen, {
            'head': jump,
            'body': jump,
            'arm_l': 0,
            'arm_r': arm_up,
            'leg_l': 4 if phase > 2 else 0,
            'leg_r': 0 if phase > 2 else 4,
            'mouth': 1 if phase > 4 else 0
        })
        
        draw_basketball_action(screen, x, y, phase)
        
        # 汗水粒子
        if phase > 2 and action_progress % 5 == 0:
            particles.append({'x': x - 10, 'y': y + 50, 'vx': random.randint(-2, 2),
                            'vy': random.randint(1, 3), 'size': 2, 'color': SKY_BLUE, 'life': 15})
    
    # 动作4: 慢跑
    elif action_index == 4:
        scene = Scene(x + 50, y + 80)
        scene.draw_background(screen, "beach")
        
        run_phase = action_progress * 0.4
        leg_offset = int(math.sin(run_phase) * 12)
        arm_offset = int(math.sin(run_phase) * 10)
        
        man.draw(screen, {
            'head': -1,
            'body': 1,
            'arm_l': -2 + arm_offset,
            'arm_r': -2 - arm_offset,
            'leg_l': leg_offset,
            'leg_r': -leg_offset,
            'mouth': 1
        })
        
        draw_jogging_scene(screen, x, y, action_progress)
        
        # 脚步粒子
        if action_progress % 4 == 0:
            particles.append({'x': x + 20, 'y': y + 170, 'vx': random.randint(-2, 2),
                            'vy': -2, 'size': 2, 'color': BROWN, 'life': 10})
    
    # 动作5: 游泳
    elif action_index == 5:
        scene = Scene(x + 50, y + 80)
        scene.draw_background(screen, "beach")
        
        swim_phase = action_progress * 0.3
        arm_l_offset = int(math.sin(swim_phase) * 15)
        arm_r_offset = int(math.sin(swim_phase + math.pi) * 15)
        
        man.draw(screen, {
            'head': -2,
            'body': 0,
            'arm_l': -10 + arm_l_offset,
            'arm_r': -10 + arm_r_offset,
            'leg_l': 5,
            'leg_r': -5,
            'mouth': 0
        })
        
        draw_swimming(screen, x, y, action_progress)
        
        # 水花粒子
        if action_progress % 3 == 0:
            particles.append({'x': x + 30, 'y': y + 120, 'vx': random.randint(-3, 3),
                            'vy': random.randint(-4, -1), 'size': 3, 'color': WHITE, 'life': 12})
    
    # 动作6: 举重
    elif action_index == 6:
        scene = Scene(x + 50, y + 80)
        scene.draw_background(screen, "gym")
        
        lift_phase = action_progress * 0.2
        bar_height = int(abs(math.sin(lift_phase)) * 40)
        
        man.draw(screen, {
            'head': -bar_height // 3,
            'body': 0,
            'arm_l': -2,
            'arm_r': -2,
            'leg_l': 2,
            'leg_r': 2,
            'mouth': 1 if bar_height > 20 else 0
        })
        
        draw_weight_lifting(screen, x, y, action_progress)
        
        # 汗水粒子
        if bar_height > 30 and action_progress % 5 == 0:
            particles.append({'x': x - 5, 'y': y + 40, 'vx': random.randint(-2, 2),
                            'vy': random.randint(1, 4), 'size': 2, 'color': SKY_BLUE, 'life': 15})
    
    # 动作7: 瑜伽
    else:
        scene = Scene(x + 50, y + 80)
        scene.draw_background(screen, "park")
        
        yoga_phase = action_progress * 0.1
        body_offset = int(math.sin(yoga_phase) * 5)
        
        man.draw(screen, {
            'head': body_offset,
            'body': body_offset,
            'arm_l': 5 + body_offset,
            'arm_r': 5 - body_offset,
            'leg_l': 3,
            'leg_r': 3,
            'mouth': 1 if action_progress % 30 < 15 else 0
        })
        
        draw_yoga(screen, x, y, action_progress)
        
        # 光环粒子
        if action_progress % 10 == 0:
            particles.append({'x': x + 60, 'y': y + 100, 'vx': random.randint(-1, 1),
                            'vy': -1, 'size': 2, 'color': YELLOW, 'life': 30})
    
    # 更新粒子系统
    particles = draw_particles(screen, x, y, particles)
    
    # 显示信息
    action_names = ["WORKING", "CLEANING", "CYCLING", "BASKETBALL", 
                    "JOGGING", "SWIMMING", "WEIGHT LIFTING", "YOGA"]
    
    font = pygame.font.Font(None, 24)
    font_small = pygame.font.Font(None, 18)
    
    # 动作名称
    action_text = font.render(f"{action_names[action_index]}", True, DARK_GRAY)
    screen.blit(action_text, (x + 60, y - 40))
    
    # 进度条
    progress = action_progress / ACTION_DURATION
    pygame.draw.rect(screen, LIGHT_GRAY, (x + 40, y - 25, 160, 8))
    pygame.draw.rect(screen, BLUE, (x + 40, y - 25, int(160 * progress), 8))
    
    # 循环计数器
    cycle_count = frame // CYCLE_FRAMES + 1
    time_seconds = frame // 30
    minutes = time_seconds // 60
    seconds = time_seconds % 60
    
    info_text = font_small.render(f"Cycle: {cycle_count} | Time: {minutes:02d}:{seconds:02d}", True, DARK_GRAY)
    screen.blit(info_text, (10, 10))
    
    # 动作进度
    action_num = font_small.render(f"Action: {action_index + 1}/{NUM_ACTIONS}", True, DARK_GRAY)
    screen.blit(action_num, (10, 30))
    
    pygame.display.flip()

pygame.quit()