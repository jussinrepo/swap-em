import pygame
import random
import copy
import os
import json
import math

# Game constants
SCREEN_WIDTH = 512
SCREEN_HEIGHT = 548  # Increased to make room for score display
GRID_WIDTH = 8
GRID_HEIGHT = 8
TILE_SIZE = 64
NUM_COLORS = 8
COLORS = ['red', 'blue', 'green', 'yellow', 'purple', 'aqua', 'hotpink', 'chocolate'][:NUM_COLORS]
ANIMATION_SPEED = 1 # 1 for fast, 2 for regular and 3 for slow/degub

class Tile:
    def __init__(self, color, special_type=None):
        self.color = color
        self.special_type = special_type

    def __eq__(self, other):
        if isinstance(other, Tile):
            return self.color == other.color
        return False

    def __str__(self):
        return f"{self.color} ({self.special_type or 'normal'})"

class MultiplierDisplay:
    def __init__(self):
        self.value = 1
        self.display_time = 0
        self.font = pygame.font.Font(None, 48)  # Base font size
        self.alpha = 255
        
    def update(self, new_value):
        self.value = new_value
        self.display_time = 60  # frames to display
        self.alpha = 255
        
    def draw(self, surface, pos):
        if self.display_time > 0 and self.value > 1:
            # Dynamic font size based on multiplier
            font_size = 36 + (self.value * 6)  # Increases font size with multiplier
            font = pygame.font.Font(None, font_size)
            
            text = font.render(f'{self.value}x', True, pygame.Color('yellow'))
            text.set_alpha(self.alpha)
            text_rect = text.get_rect(center=pos)
            surface.blit(text, text_rect)
            
            self.display_time -= 1
            self.alpha = int(255 * (self.display_time / 60))

class MatchThreeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Swap\'em! A Match Three Game')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        # Initialize grid
        self.grid = None  # Will be populated in reset_game()

        # JSON-based high score management
        self.high_score_file = 'swap_em_highscores.json'
        self.high_scores = self.load_high_scores()
        
        # Pre-initialize color_buttons to avoid AttributeError
        self.color_buttons = [
            (pygame.Rect(SCREEN_WIDTH//2 - 150 - 50, 300 - 25, 100, 50), '5'),
            (pygame.Rect(SCREEN_WIDTH//2 - 50 - 50, 300 - 25, 100, 50), '6'),
            (pygame.Rect(SCREEN_WIDTH//2 + 50 - 50, 300 - 25, 100, 50), '7'),
            (pygame.Rect(SCREEN_WIDTH//2 + 150 - 50, 300 - 25, 100, 50), '8')
        ]
        self.score = 0
        self.game_over_tip = None
        self.in_start_menu = True
        self.current_color_count = 8  # Default
        self.high_score = self.high_scores.get(str(self.current_color_count), 0)
        self.multiplier_display = MultiplierDisplay()
        self.score_popups = []
        self.removal_effects = []  # List of (rect, alpha) tuples

        # Load special tile images
        self.special_tile_images = {}
        try:
            self.special_tile_images['L'] = pygame.image.load('assets/horizontal.png')
            self.special_tile_images['D'] = pygame.image.load('assets/vertical.png')
            self.special_tile_images['X'] = pygame.image.load('assets/double.png')
            
            # Resize images to tile size
            for key in self.special_tile_images:
                self.special_tile_images[key] = pygame.transform.scale(
                    self.special_tile_images[key], (TILE_SIZE, TILE_SIZE)
                )
        except pygame.error:
            print("Could not load all special tile images. Falling back to letter representation.")
            self.special_tile_images = {}

    def reset_game(self):
        self.grid = self.create_grid_without_matches()
        self.selected_tile = None
        self.game_over = False
        self.score = 0
        self.chain_multiplier = 1

    def draw_gradient_button(self, surface, color, rect, hover=False):
        # Create a gradient button similar to tile gradient
        base_color = pygame.Color(color)
        
        # Create lighter and darker versions for hover effect
        if hover:
            lighter_color = base_color.lerp(pygame.Color('white'), 0.5)
        else:
            lighter_color = base_color.lerp(pygame.Color('white'), 0.3)
        
        # Create gradient surface
        gradient_surf = pygame.Surface(rect.size)
        for y in range(rect.height):
            inter_color = base_color.lerp(lighter_color, y / rect.height)
            pygame.draw.line(gradient_surf, inter_color, (0, y), (rect.width, y))
        
        surface.blit(gradient_surf, rect)
        
        # Draw border
        pygame.draw.rect(surface, pygame.Color('white'), rect, 2)

    def draw_start_menu(self):
        # Ensure screen is properly drawn every frame
        self.screen.fill(pygame.Color('black'))
        
        # Title
        title_font = pygame.font.Font(None, 74)
        title = title_font.render('Swap\'em!', True, pygame.Color('white'))
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Color selection buttons - now with gradients
        color_options = [
            (SCREEN_WIDTH//2 - 150, 300, '5', 'red'),
            (SCREEN_WIDTH//2 - 50, 300, '6', 'blue'),
            (SCREEN_WIDTH//2 + 50, 300, '7', 'green'),
            (SCREEN_WIDTH//2 + 150, 300, '8', 'purple')
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        
        for idx, (x, y, num_colors, color) in enumerate(color_options):
            button_rect = self.color_buttons[idx][0]
            
            # Check if mouse is hovering
            hover = button_rect.collidepoint(mouse_pos)
            
            # Draw gradient button
            self.draw_gradient_button(self.screen, color, button_rect, hover)
            
            # Button text
            button_font = pygame.font.Font(None, 36)
            button_text = button_font.render(f'{num_colors} Col', True, pygame.Color('white'))
            button_text_rect = button_text.get_rect(center=button_rect.center)
            self.screen.blit(button_text, button_text_rect)
            
            # High score for this color count
            # high_score_text = self.font.render(f'High: {self.high_scores[num_colors]}', 
            high_score_text = self.font.render(f'{self.high_scores[num_colors]}', 
                                                True, pygame.Color('yellow'))
            high_score_rect = high_score_text.get_rect(center=(x, y + 50))
            self.screen.blit(high_score_text, high_score_rect)
        
        # Quit instructions
        quit_font = pygame.font.Font(None, 24)
        quit_text = quit_font.render('Press ESC to Quit', True, pygame.Color('gray'))
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
        credits = quit_font.render("Made by Jussi & Claude 3.5 Haiku", True, pygame.Color('yellow'))
        credits_rect = credits.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))

        self.screen.blit(quit_text, quit_rect)        
        self.screen.blit(credits, credits_rect)
        
        pygame.display.flip()

    def load_high_scores(self):
        if not os.path.exists(self.high_score_file):
            return {
                "5": 0,
                "6": 0,
                "7": 0,
                "8": 0
            }
        
        try:
            with open(self.high_score_file, 'r') as f:
                return json.load(f)
        except (ValueError, IOError):
            return {
                "5": 0,
                "6": 0,
                "7": 0,
                "8": 0
            }

    def save_high_scores(self):
        try:
            with open(self.high_score_file, 'w') as f:
                json.dump(self.high_scores, f)
        except IOError:
            print("Could not save high scores")

    def create_random_tile(self):
        return Tile(random.choice(COLORS[:self.current_color_count]))

    def create_grid_without_matches(self):
        while True:
            grid = [[self.create_random_tile() for _ in range(GRID_WIDTH)] 
                    for _ in range(GRID_HEIGHT)]
            test_grid = copy.deepcopy(grid)
            if not self.check_matches(test_grid):
                return grid

    def handle_special_tile_effects(self, initial_matches):
        """
        Recursively handle special tile effects, creating a chain reaction of tile removals.
        
        Args:
            initial_matches (set): Initial set of matches to process
        
        Returns:
            set: All tiles to be removed, including those from special tile chain reactions
        """
        tiles_to_remove = set(initial_matches)
        processed_special_tiles = set()
        
        def process_special_tile(y, x):
            # Prevent processing the same special tile multiple times
            if (y, x) in processed_special_tiles:
                return set()
            
            tile = self.grid[y][x]
            special_removal = set()
            
            if tile and tile.special_type:
                processed_special_tiles.add((y, x))
                
                if tile.special_type == 'L':  # Horizontal line
                    for col in range(GRID_WIDTH):
                        special_removal.add((y, col))
                elif tile.special_type == 'D':  # Vertical line
                    for row in range(GRID_HEIGHT):
                        special_removal.add((row, x))
                elif tile.special_type == 'X':  # Cross
                    for col in range(GRID_WIDTH):
                        special_removal.add((y, col))
                    for row in range(GRID_HEIGHT):
                        special_removal.add((row, x))
            
            return special_removal

        # First pass: process initial special tiles in the matches
        additional_special_removals = set()
        for y, x in initial_matches:
            special_removals = process_special_tile(y, x)
            additional_special_removals.update(special_removals)
        
        tiles_to_remove.update(additional_special_removals)
        
        # Recursive pass: check if new special tile removals create more special tile effects
        while additional_special_removals:
            next_special_removals = set()
            for y, x in additional_special_removals:
                special_removals = process_special_tile(y, x)
                next_special_removals.update(special_removals)
            
            tiles_to_remove.update(next_special_removals)
            additional_special_removals = next_special_removals
        
        return tiles_to_remove

    def handle_match_creation(self, matches):
        match_count = len(matches)
        
        # Get the columns where matches occurred
        match_columns = set(x for (y, x) in matches)
        
        # Only proceed if we have enough matches to create a special tile
        if match_count >= 4:
            random_color = random.choice(COLORS[:self.current_color_count])
            special_tile = None

            if match_count == 4:
                # L tile for 4-match
                special_tile = Tile(random_color, special_type='L')
            elif match_count == 5:
                # D tile for 5-match (vertical line)
                special_tile = Tile(random_color, special_type='D')
            elif match_count >= 6:
                # X tile for 6+ match (full cross)
                special_tile = Tile(random_color, special_type='X')
            
            if special_tile:
                # Choose a random column from the columns where matches occurred
                random_col = random.choice(list(match_columns))
                # Simply replace the top tile with the special tile
                self.grid[0][random_col] = special_tile

    def check_matches(self, grid=None):
        if grid is None:
            grid = self.grid
        matches = set()
        
        # Horizontal matches
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH-2):
                if (grid[y][x] and grid[y][x+1] and grid[y][x+2] and
                    grid[y][x].color == grid[y][x+1].color == grid[y][x+2].color):
                    matches.update([(y, x), (y, x+1), (y, x+2)])

        # Vertical matches
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT-2):
                if (grid[y][x] and grid[y+1][x] and grid[y+2][x] and
                    grid[y][x].color == grid[y+1][x].color == grid[y+2][x].color):
                    matches.update([(y, x), (y+1, x), (y+2, x)])

        return matches

    def draw_gradient_rect(self, surface, color, rect):
        # Create a gradient effect for tiles
        base_color = pygame.Color(color)
        
        # Create a lighter version of the base color
        lighter_color = base_color.lerp(pygame.Color('white'), 0.3)
        
        # Create gradient surface
        gradient_surf = pygame.Surface(rect.size)
        for y in range(rect.height):
            # Interpolate between base color and lighter color
            inter_color = base_color.lerp(lighter_color, y / rect.height)
            pygame.draw.line(gradient_surf, inter_color, (0, y), (rect.width, y))
        
        surface.blit(gradient_surf, rect)

    def draw_grid(self):
        if self.in_start_menu or self.grid is None:
            return  # Don't try to draw grid during start menu
            
        mouse_pos = pygame.mouse.get_pos()
        
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                tile = self.grid[y][x]
                if tile:
                    tile_rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE + 36, TILE_SIZE, TILE_SIZE)
                    
                    # Draw gradient tile
                    self.draw_gradient_rect(self.screen, tile.color, tile_rect)
                    
                    # Draw special tile marker if it's a special tile
                    if tile.special_type:
                        # Draw glowing effect
                        glow_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        glow_color = pygame.Color('yellow')
                        glow_color.a = 100 + int(50 * math.sin(pygame.time.get_ticks() / 200))  # Pulsing effect
                        pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect(), 4)
                        self.screen.blit(glow_surf, tile_rect)
                        
                        # Try to draw PNG image, fall back to letter if not available
                        if tile.special_type in self.special_tile_images:
                            # Draw PNG image
                            image = self.special_tile_images[tile.special_type]
                            self.screen.blit(image, tile_rect)
                        else:
                            # Fallback to letter representation
                            font = pygame.font.Font(None, 48)
                            symbol = font.render(tile.special_type, True, pygame.Color('white'))
                            symbol_rect = symbol.get_rect(center=tile_rect.center)
                            self.screen.blit(symbol, symbol_rect)
                    
                    # Draw white border
                    pygame.draw.rect(self.screen, pygame.Color('white'), tile_rect, 1)

                    # Hover highlight
                    if tile_rect.collidepoint(mouse_pos):
                        highlight_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        pygame.draw.rect(highlight_surface, (255, 255, 255, 200), highlight_surface.get_rect(), 4)
                        self.screen.blit(highlight_surface, tile_rect)

                    # Selected tile highlight
                    if self.selected_tile and (x, y) == self.selected_tile:
                        highlight_rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE + 36, TILE_SIZE, TILE_SIZE)
                        highlight_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        pygame.draw.rect(highlight_surface, (255, 255, 255, 100), highlight_surface.get_rect(), 8)
                        self.screen.blit(highlight_surface, highlight_rect)

    def draw_fade_effect(self, surface, rect, alpha):
        # Ensure alpha is within valid range
        alpha = max(0, min(255, int(alpha)))  # Clamp between 0 and 255
        effect_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(effect_surface, (255, 255, 255, alpha), effect_surface.get_rect())
        surface.blit(effect_surface, rect)

    def get_tile_at_pos(self, pos):
        x, y = pos
        grid_x = x // TILE_SIZE
        grid_y = y // TILE_SIZE
        return (grid_x, grid_y)

    def swap_tiles(self, tile1, tile2):
        self.grid[tile1[1]][tile1[0]], self.grid[tile2[1]][tile2[0]] = \
        self.grid[tile2[1]][tile2[0]], self.grid[tile1[1]][tile1[0]]

    def check_valid_moves(self):
        """
        Check if there are any valid moves left on the board
        
        Returns:
            bool: True if moves are available, False otherwise
        """
        # Similar to previous implementation
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                # Check horizontal swaps
                if x < GRID_WIDTH - 1:
                    # Simulate swap
                    self.grid[y][x], self.grid[y][x+1] = self.grid[y][x+1], self.grid[y][x]
                    matches = self.check_matches()
                    # Swap back
                    self.grid[y][x], self.grid[y][x+1] = self.grid[y][x+1], self.grid[y][x]
                    if matches:
                        return True
                
                # Check vertical swaps
                if y < GRID_HEIGHT - 1:
                    # Simulate swap
                    self.grid[y][x], self.grid[y+1][x] = self.grid[y+1][x], self.grid[y][x]
                    matches = self.check_matches()
                    # Swap back
                    self.grid[y][x], self.grid[y+1][x] = self.grid[y+1][x], self.grid[y][x]
                    if matches:
                        return True
        
        return False

    def animate_swap(self, tile1, tile2):
        x1, y1 = tile1
        x2, y2 = tile2
        
        for step in range(6):
            progress = (step + 1) / 6
            
            # Clear the screen
            self.screen.fill(pygame.Color('black'))
            
            # Draw score and other UI elements
            self.draw_score()
            
            # Draw other tiles
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if (x, y) != tile1 and (x, y) != tile2 and self.grid[y][x]:
                        tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE + 36, TILE_SIZE, TILE_SIZE)
                        self.draw_gradient_rect(self.screen, self.grid[y][x].color, tile_rect)
                        pygame.draw.rect(self.screen, pygame.Color('white'), tile_rect, 1)
            
            # Interpolate swap positions
            swap_x1 = x1 * TILE_SIZE + (x2 - x1) * TILE_SIZE * progress
            swap_y1 = y1 * TILE_SIZE + (y2 - y1) * TILE_SIZE * progress + 36
            swap_x2 = x2 * TILE_SIZE - (x2 - x1) * TILE_SIZE * progress
            swap_y2 = y2 * TILE_SIZE - (y2 - y1) * TILE_SIZE * progress + 36
            
            # Draw swapping tiles with gradient and border
            tile1_rect = pygame.Rect(swap_x1, swap_y1, TILE_SIZE, TILE_SIZE)
            tile2_rect = pygame.Rect(swap_x2, swap_y2, TILE_SIZE, TILE_SIZE)
            
            self.draw_gradient_rect(self.screen, self.grid[y1][x1].color, tile1_rect)
            self.draw_gradient_rect(self.screen, self.grid[y2][x2].color, tile2_rect)
            
            pygame.draw.rect(self.screen, pygame.Color('white'), tile1_rect, 1)
            pygame.draw.rect(self.screen, pygame.Color('white'), tile2_rect, 1)
            
            # Update the display
            pygame.display.flip()
            
            # Add a small delay to control animation speed
            pygame.time.delay(ANIMATION_SPEED * 10)
            
            # Process events to keep the window responsive
            pygame.event.pump()

    def animate_fall(self):
        # Falling animation logic
        for x in range(GRID_WIDTH):
            column = [self.grid[y][x] for y in range(GRID_HEIGHT)]
            empty_slots = column.count(None)
            if empty_slots > 0:
                # Remove None values and shift down
                non_empty = [tile for tile in column if tile is not None]
                # Add new tiles to the top
                non_empty = [None] * empty_slots + non_empty
                
                # Update grid column
                for y in range(GRID_HEIGHT):
                    self.grid[y][x] = non_empty[y] or self.create_random_tile()

    def fill_grid(self):
        # Ensure grid is filled with tiles
        for x in range(GRID_WIDTH):
            column = [self.grid[y][x] for y in range(GRID_HEIGHT)]
            empty_slots = column.count(None)
            if empty_slots > 0:
                # Remove None values and shift down
                non_empty = [tile for tile in column if tile is not None]
                # Add new tiles to the top
                non_empty = [None] * empty_slots + non_empty
                
                # Update grid column
                for y in range(GRID_HEIGHT):
                    self.grid[y][x] = non_empty[y] or self.create_random_tile()

    def calculate_match_score(self, matches):
        # Calculate base score based on number of matches
        match_count = len(matches)
        base_score = 0
        
        if match_count == 3:
            base_score = 30 * self.chain_multiplier
        elif match_count == 4:
            base_score = 50 * self.chain_multiplier
        elif match_count == 5:
            base_score = 100 * self.chain_multiplier
        elif match_count >= 6:
            base_score = 200 * self.chain_multiplier
        
        # Calculate bonus points from special tile explosions
        # Regular matches are 3-5 tiles, so any additional tiles 
        # must be from special tile effects
        explosion_tiles = match_count - 3  # Subtract minimum match size
        if explosion_tiles > 0:
            bonus_score = explosion_tiles * 10 * self.chain_multiplier
            return base_score + bonus_score
        
        return base_score

    def animate_fall_with_delay(self):
        # Falling animation with delay
        for x in range(GRID_WIDTH):
            column = [self.grid[y][x] for y in range(GRID_HEIGHT)]
            empty_slots = column.count(None)
            if empty_slots > 0:
                # Remove None values and shift down
                non_empty = [tile for tile in column if tile is not None]
                # Add new tiles to the top
                non_empty = [None] * empty_slots + non_empty
                
                # Animate falling with a delay between each step
                for y in range(GRID_HEIGHT):
                    self.grid[y][x] = non_empty[y] or self.create_random_tile()
                    
                    # Redraw screen to show gradual falling
                    self.screen.fill(pygame.Color('black'))
                    self.draw_score()
                    self.draw_grid()
                    self.draw_game_state()
                    pygame.time.delay(ANIMATION_SPEED * 15)  # Add a small delay between falling blocks

    def draw_score(self):
        # Draw current score
        score_text = self.font.render(f'Score: {self.score}', True, pygame.Color('white'))
        self.screen.blit(score_text, (10, 8))
        
        # Draw high score
        high_score_text = self.font.render(f'High Score: {self.high_score}', True, pygame.Color('yellow'))
        high_score_rect = high_score_text.get_rect(right=SCREEN_WIDTH-10, top=8)
        self.screen.blit(high_score_text, high_score_rect)


    def get_random_game_tip(self):
        tips = [
            "Try to look for matches\nthat create chain reactions!",
            "Focus on creating matches at\nthe bottom of the grid first.",
            "Sometimes sacrificing a move\nto set up a big combo is worth it.",
            "Pay attention to potential\nmatches before making a swap.",
            "Try to create special matches\nof 4 or 5 tiles for bonus points!",
            "Don't rush - take your time\nto plan your moves carefully."
        ]
        return random.choice(tips)

    def game_over_screen(self):

        # Update high score if current score is higher
        if self.score > int(self.high_scores[str(self.current_color_count)]):
            self.high_scores[str(self.current_color_count)] = self.score
            self.save_high_scores()
       
        # Select a random game tip if not already selected
        if not self.game_over_tip:
            self.game_over_tip = self.get_random_game_tip()

        self.screen.fill(pygame.Color('black'))
        
        # Game Over text
        font = pygame.font.Font(None, 74)
        text = font.render('Game Over', True, pygame.Color('white'))
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 150))
        
        # Check for new high score
        is_new_highscore = self.score > int(self.high_scores[str(self.current_color_count)])
        
        # New High Score text
        if is_new_highscore:
            highscore_font = pygame.font.Font(None, 48)
            highscore_text = highscore_font.render('NEW HIGH SCORE!', True, pygame.Color('gold'))
            highscore_rect = highscore_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
            self.screen.blit(highscore_text, highscore_rect)
        
        # Tip text
        tip_font = pygame.font.Font(None, 36)
        tip_text = tip_font.render('Tip: ' + self.game_over_tip, True, pygame.Color('yellow'), pygame.Color('black'))
        tip_rect = tip_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        # Restart instructions
        restart_font = pygame.font.Font(None, 36)
        restart_text = restart_font.render('Click to Restart', True, pygame.Color('white'))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100))
        
        self.screen.blit(text, text_rect)
        self.screen.blit(tip_text, tip_rect)
        self.screen.blit(restart_text, restart_rect)
        
        pygame.display.flip()
        # self.draw_game_state()

    def draw_game_state(self):
        if not self.in_start_menu:
            self.screen.fill(pygame.Color('black'))
            self.draw_score()
            self.draw_grid()
            
            # Draw chain multiplier
            if self.chain_multiplier > 1:
                self.multiplier_display.draw(self.screen, (SCREEN_WIDTH - 100, 100))
            
            # Draw score popups
            for popup in self.score_popups[:]:
                popup.draw(self.screen)
                popup.update()
                if popup.lifetime <= 0:
                    self.score_popups.remove(popup)
            
            # Draw removal effects
            for effect in self.removal_effects[:]:
                rect, alpha = effect
                self.draw_fade_effect(self.screen, rect, alpha)
                if alpha > 0:
                    self.removal_effects[self.removal_effects.index(effect)] = (rect, alpha - 10)
                else:
                    self.removal_effects.remove(effect)
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            if self.in_start_menu:
                self.draw_start_menu()  # Ensure menu is redrawn each frame
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        for button_rect, num_colors in self.color_buttons:
                            if button_rect.collidepoint(mouse_pos):
                                # Define colors based on selected count
                                global COLORS
                                COLORS = ['red', 'blue', 'green', 'yellow', 'purple', 'aqua', 'hotpink', 'chocolate'][:int(num_colors)]
                                self.current_color_count = int(num_colors)
                                
                                self.high_score = self.high_scores.get(str(self.current_color_count), 0)
                                
                                self.in_start_menu = False
                                self.reset_game()
                                break
                
                self.clock.tick(30)  # Control frame rate

            elif self.game_over:
                self.game_over_screen() 
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        # Reset the game state
                        self.game_over_tip = None
                        self.in_start_menu = True
                    
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            # Reset game state and return to start menu
                            self.game_over_tip = None
                            self.in_start_menu = True
        
            else:  # Main gameplay
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                    # Check if any moves left
                    if not self.game_over and not self.check_valid_moves():
                        self.game_over = True  

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            # Save high score if applicable and return to menu
                            if self.score > int(self.high_scores[str(self.current_color_count)]):
                                self.high_scores[str(self.current_color_count)] = self.score
                                self.save_high_scores()
                            self.in_start_menu = True
                            self.game_over_tip = None
                    
                    if self.game_over and event.type == pygame.MOUSEBUTTONDOWN:
                        # Update high score if needed before resetting
                        if self.score > int(self.high_scores[str(self.current_color_count)]):
                            self.high_scores[str(self.current_color_count)] = self.score
                            self.save_high_scores()

                        # Restart game on mouse click when game is over
                        self.reset_game()
                    
                    if not self.game_over and event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        clicked_tile = self.get_tile_at_pos((pos[0], pos[1] - 36))  # Adjust for score area
                        
                        if not self.selected_tile:
                            self.selected_tile = clicked_tile
                        else:
                            # Check if tiles are adjacent
                            if abs(self.selected_tile[0] - clicked_tile[0]) + \
                            abs(self.selected_tile[1] - clicked_tile[1]) == 1:
                                # Temporarily swap to check for matches BEFORE animation
                                temp_grid = [row[:] for row in self.grid]
                                temp_grid[self.selected_tile[1]][self.selected_tile[0]], \
                                temp_grid[clicked_tile[1]][clicked_tile[0]] = \
                                temp_grid[clicked_tile[1]][clicked_tile[0]], \
                                temp_grid[self.selected_tile[1]][self.selected_tile[0]]
                                
                                # Check for matches in temporary grid
                                test_matches = self.check_matches(temp_grid)
                                
                                if test_matches:
                                    # Actually swap in real grid
                                    self.animate_swap(self.selected_tile, clicked_tile)
                                    self.swap_tiles(self.selected_tile, clicked_tile)
                                    
                                    # Reset chain multiplier
                                    self.chain_multiplier = 1
                                    chain_reaction_occurred = False
                                    
                                    # Repeat match and fall process with cascading matches
                                    while True:
                                        matches = self.check_matches()
                                        if not matches:
                                            break

                                        # Track if chain reaction occurs
                                        if matches:
                                            chain_reaction_occurred = True

                                        # Calculate and add score
                                        round_score = self.calculate_match_score(matches)
                                        self.score += round_score

                                        # Determine tiles to remove with special tile chain reactions
                                        tiles_to_remove = self.handle_special_tile_effects(matches)

                                        # Optional: Add special tile creation logic
                                        if len(matches) >= 4:
                                            self.handle_match_creation(matches)

                                        # Remove tiles with visual feedback
                                        for y, x in tiles_to_remove:
                                            rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE + 36, TILE_SIZE, TILE_SIZE)
                                            self.removal_effects.append((rect, 255))
                                            self.grid[y][x] = None
                                            
                                        # Visual updates with delay
                                        self.screen.fill(pygame.Color('black'))
                                        self.draw_score()
                                        self.draw_grid()
                                        self.draw_game_state()
                                        pygame.time.delay(ANIMATION_SPEED * 15)  # Add a slight delay for visual excitement
                                        
                                        # Animate falling with delay
                                        self.animate_fall_with_delay()
                                        self.fill_grid()
                                        
                                        # Increase chain multiplier, cap at 5x
                                        if chain_reaction_occurred:
                                            self.chain_multiplier = min(5, self.chain_multiplier + 1)
                                            self.multiplier_display.update(self.chain_multiplier)

                                    # After the main matching loop, check for valid moves
                                    if not self.game_over and not self.check_valid_moves():
                                        self.game_over = True
                                else:
                                    # Illegal move, do nothing
                                    pass
                                
                                # Check if any moves left
                                if not self.game_over and not self.check_valid_moves():
                                    self.game_over = True
                                
                            self.selected_tile = None

                        # Check for game over AFTER move processing
                        if not self.game_over and not self.check_valid_moves():
                            self.game_over = True

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            # Save high score if applicable and return to menu
                            if self.score > int(self.high_scores[str(self.current_color_count)]):
                                self.high_scores[str(self.current_color_count)] = self.score
                                self.save_high_scores()
                            self.in_start_menu = True
                            self.game_over_tip = None

                # Remove the separate game over rendering block
                self.screen.fill(pygame.Color('black'))
                self.draw_score()
                self.draw_grid()
                self.draw_game_state()
                
                # Check for game over at the end of the game loop
                if not self.game_over and not self.check_valid_moves():
                    self.game_over = True

                self.clock.tick(30)

        # Update high score before quitting if needed
        if self.score > int(self.high_scores[str(self.current_color_count)]):
            self.high_scores[str(self.current_color_count)] = self.score
            self.save_high_scores()

        pygame.quit()

if __name__ == '__main__':
    game = MatchThreeGame()
    game.run()