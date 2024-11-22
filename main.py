import pygame
import os
import random
import asyncio
import websockets
import json
import threading

# Pygame setup
pygame.init()

# Global Constants
SHOW_SPRITES_CONTOURNS = False
SCREEN_HEIGHT = 600
SCREEN_WIDTH = 1100
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

RUNNING = [pygame.image.load(os.path.join("Assets/Dino", "DinoRun1.png")),
           pygame.image.load(os.path.join("Assets/Dino", "DinoRun2.png"))]
JUMPING = pygame.image.load(os.path.join("Assets/Dino", "DinoJump.png"))
DUCKING = [pygame.image.load(os.path.join("Assets/Dino", "DinoDuck1.png")),
           pygame.image.load(os.path.join("Assets/Dino", "DinoDuck2.png"))]

SMALL_CACTUS = [pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus1.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus2.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus3.png"))]
LARGE_CACTUS = [pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus1.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus2.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus3.png"))]

BIRD = [pygame.image.load(os.path.join("Assets/Bird", "Bird1.png")),
        pygame.image.load(os.path.join("Assets/Bird", "Bird2.png"))]

CLOUD = pygame.image.load(os.path.join("Assets/Other", "Cloud.png"))

BG = pygame.image.load(os.path.join("Assets/Other", "Track.png"))

USER_MOVEMENT = 'stand'

# WebSocket communication
async def consume_websocket():
    uri = "ws://localhost:8765"  # Connect to your WebSocket server
    async with websockets.connect(uri) as websocket:
        while True:
            # Wait for a message from the WebSocket server
            message = await websocket.recv()

            # Parse the received JSON message
            data = json.loads(message)

            # Process the data
            print("Received data:", data)

            # Example: Accessing movement and position
            current_position = data.get('current_position')
            movement = data.get('movement')
            update_game_state(current_position, movement)

def set_user_movement(current_position, movement):
    if movement and movement.lower() == 'jumping':
        return 'jump'
    if current_position and current_position.lower() == 'squatting':
        return 'squat'
    return 'stand'

# Update the game state based on WebSocket data
def update_game_state(current_position, movement):
    # Use this data to adjust game behavior like moving the dinosaur
    # print(f"Position: {current_position}, Movement: {movement}")
    global USER_MOVEMENT
    USER_MOVEMENT = set_user_movement(current_position, movement)

# Thread to run the WebSocket client in the background
def websocket_thread():
    asyncio.run(consume_websocket())

# Start the WebSocket thread
thread = threading.Thread(target=websocket_thread)
thread.daemon = True  # Ensure it closes when the program exits
thread.start()

class Dinosaur:
    X_POS = 80
    Y_POS = 310
    Y_POS_DUCK = 340
    JUMP_VEL = 8.5
    INFLATION = -30

    def __init__(self):
        self.duck_img = DUCKING
        self.run_img = RUNNING
        self.jump_img = JUMPING

        self.dino_duck = False
        self.dino_run = True
        self.dino_jump = False

        self.step_index = 0
        self.jump_vel = self.JUMP_VEL
        self.image = self.run_img[0]
        self.dino_rect = self.image.get_rect().inflate(self.INFLATION, self.INFLATION)
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS

    def update(self, userInput):
        if self.dino_duck:
            self.duck()
        if self.dino_run:
            self.run()
        if self.dino_jump:
            self.jump()

        if self.step_index >= 10:
            self.step_index = 0

        print(f'movement: {USER_MOVEMENT}')
        if USER_MOVEMENT == 'jump' and not self.dino_jump:
            self.dino_duck = False
            self.dino_run = False
            self.dino_jump = True
        elif USER_MOVEMENT == 'squat' and not self.dino_jump:
            self.dino_duck = True
            self.dino_run = False
            self.dino_jump = False
        elif not (self.dino_jump or USER_MOVEMENT == 'squat'):
            self.dino_duck = False
            self.dino_run = True
            self.dino_jump = False

    def duck(self):
        self.image = self.duck_img[self.step_index // 5]
        self.dino_rect = self.image.get_rect().inflate(self.INFLATION, self.INFLATION)
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS_DUCK
        self.step_index += 1

    def run(self):
        self.image = self.run_img[self.step_index // 5]
        self.dino_rect = self.image.get_rect().inflate(self.INFLATION, self.INFLATION)
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS
        self.step_index += 1

    def jump(self):
        self.image = self.jump_img
        if self.dino_jump:
            self.dino_rect.y -= self.jump_vel * 4
            self.jump_vel -= 0.8
        if self.jump_vel < - self.JUMP_VEL:
            self.dino_jump = False
            self.jump_vel = self.JUMP_VEL

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.dino_rect.x, self.dino_rect.y))
        if SHOW_SPRITES_CONTOURNS:
            pygame.draw.rect(SCREEN, (255, 255, 0), self.dino_rect, 2)

class Cloud:
    def __init__(self):
        self.image = CLOUD
        self.x = SCREEN_WIDTH
        self.y = random.randint(50, 150)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.x -= game_speed
        if self.x < -self.width:
            self.x = SCREEN_WIDTH
            self.y = random.randint(50, 150)

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.x, self.y))

class Obstacle:
    def __init__(self, type):
        self.type = type
        self.image = self.type[0]  # Pick the first image from the type
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH
        self.rect.y = 300  # Position on the ground

    def update(self):
        self.rect.x -= game_speed
        if self.rect.x < -self.rect.width:
            obstacles.remove(self)

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.rect.x, self.rect.y))

# Add Cactus and Bird obstacles
class SmallCactus(Obstacle):
    def __init__(self):
        super().__init__(SMALL_CACTUS)

class LargeCactus(Obstacle):
    def __init__(self):
        super().__init__(LARGE_CACTUS)

class Bird(Obstacle):
    def __init__(self):
        super().__init__(BIRD)
        self.rect.y = 250

# Main game loop remains the same...
def main():
    global game_speed, x_pos_bg, y_pos_bg, points, obstacles
    run = True
    clock = pygame.time.Clock()
    player = Dinosaur()
    cloud = Cloud()
    game_speed = 20
    x_pos_bg = 0
    y_pos_bg = 380
    points = 0
    font = pygame.font.Font('freesansbold.ttf', 20)
    obstacles = []
    death_count = 0
    obstacle_options = [SmallCactus, LargeCactus, Bird]

    def score():
        global points, game_speed
        points += 1
        if points % 100 == 0:
            game_speed += 1

        text = font.render("Points: " + str(points), True, (0, 0, 0))
        textRect = text.get_rect()
        textRect.center = (1000, 40)
        SCREEN.blit(text, textRect)

    def background():
        global x_pos_bg, y_pos_bg
        image_width = BG.get_width()
        SCREEN.blit(BG, (x_pos_bg, y_pos_bg))
        SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
        if x_pos_bg <= -image_width:
            SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
            x_pos_bg = 0
        x_pos_bg -= game_speed

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        SCREEN.fill((255, 255, 255))
        userInput = pygame.key.get_pressed()
        player.update(userInput)
        player.draw(SCREEN)

        # Cloud and obstacles
        cloud.update()
        cloud.draw(SCREEN)
        if len(obstacles) == 0 and random.choices([0, 0, 0, 0, 1]):
            obstacle = random.choice(obstacle_options)()
            obstacles.append(obstacle)

        for obstacle in obstacles:
            obstacle.draw(SCREEN)
            obstacle.update()
            if player.dino_rect.colliderect(obstacle.rect):
                pygame.time.delay(2000)
                death_count += 1
                pygame.quit()

        # Update score
        score()

        # Game update
        background()
        pygame.display.update()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
