// Constants
const SCREEN_WIDTH = 512;
const SCREEN_HEIGHT = 548;
const GRID_WIDTH = 8;
const GRID_HEIGHT = 8;
const TILE_SIZE = 64;
const ANIMATION_SPEED = 15;

// Color configurations
const COLORS = {
    5: ['#ff0000', '#0000ff', '#00ff00', '#ffff00', '#a020f0'],  // Red, Blue, Green, Yellow, Purple
    6: ['#ff0000', '#0000ff', '#00ff00', '#ffff00', '#a020f0', '#00ffff'],  // Added Aqua
    7: ['#ff0000', '#0000ff', '#00ff00', '#ffff00', '#a020f0', '#00ffff', '#ff69b4'],  // Added Hot Pink
    8: ['#ff0000', '#0000ff', '#00ff00', '#ffff00', '#a020f0', '#00ffff', '#ff69b4', '#d2691e']  // Added Chocolate
};

class Tile {
    constructor(color, specialType = null) {
        this.color = color;
        this.specialType = specialType;
    }
}

class Game {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Base game dimensions
        this.baseWidth = 512;
        this.baseHeight = 548;
        
        // Set initial size
        this.resizeCanvas();
        
        // Add resize listener
        window.addEventListener('resize', () => this.resizeCanvas());

        this.currentColorCount = 8; // Default difficulty
        this.inStartMenu = true;
        this.gameOver = false;
        this.score = 0;
        this.chainMultiplier = 1;
        this.selectedTile = null;
        this.grid = null;
        this.highScores = this.loadHighScores();

        this.isProcessing = false;
        this.fallingTiles = new Set();

        // Initialize color buttons for menu - adjusted positions
        this.colorButtons = [
            { 
                rect: { x: SCREEN_WIDTH/2 - 200, y: 300, width: 100, height: 50 }, 
                colors: 5,
                color: '#00ff00'
            },
            { 
                rect: { x: SCREEN_WIDTH/2 - 100, y: 300, width: 100, height: 50 }, 
                colors: 6,
                color: '#0000ff'
            },
            { 
                rect: { x: SCREEN_WIDTH/2, y: 300, width: 100, height: 50 }, 
                colors: 7,
                color: '#ff0000'
            },
            { 
                rect: { x: SCREEN_WIDTH/2 + 100, y: 300, width: 100, height: 50 }, 
                colors: 8,
                color: '#ff00ff'
            }
        ];

        this.specialTileImages = {};
        this.loadSpecialTileImages();

        // Add mouse position tracking
        this.mousePosition = { x: 0, y: 0 };
        this.canvas.addEventListener('mousemove', (e) => this.updateMousePosition(e));

        // Event listeners
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));

        // Start game loop
        this.gameLoop();
    }

    async loadSpecialTileImages() {
        const imageNames = {
            'L': 'horizontal.png',
            'D': 'vertical.png',
            'X': 'double.png'
        };
        
        for (const [type, filename] of Object.entries(imageNames)) {
            try {
                const img = new Image();
                img.src = `assets/${filename}`;
                await new Promise((resolve, reject) => {
                    img.onload = () => {
                        console.log(`Loaded special tile image: ${filename}`);
                        resolve();
                    };
                    img.onerror = () => {
                        console.error(`Failed to load special tile image: ${filename}`);
                        reject();
                    };
                });
                this.specialTileImages[type] = img;
            } catch (error) {
                console.warn(`Could not load special tile image: ${type}`, error);
            }
        }
    }

    updateMousePosition(event) {
        const rect = this.canvas.getBoundingClientRect();
        this.mousePosition = {
            x: (event.clientX - rect.left) / this.scale,
            y: (event.clientY - rect.top) / this.scale
        };
    }

    getMousePosition() {
        return this.mousePosition;
    }

    resizeCanvas() {
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        
        // Calculate the scaling factor to fit the screen while maintaining aspect ratio
        const scale = Math.min(
            windowWidth / this.baseWidth,
            windowHeight / this.baseHeight
        );
        
        // Set canvas size
        this.canvas.width = this.baseWidth * scale;
        this.canvas.height = this.baseHeight * scale;
        
        // Store the scale for use in input calculations
        this.scale = scale;
        
        // Scale the context to maintain the game's internal coordinate system
        this.ctx.scale(scale, scale);
    }

    loadHighScores() {
        const scores = localStorage.getItem('swapEmHighScores');
        return scores ? JSON.parse(scores) : { "5": 0, "6": 0, "7": 0, "8": 0 };
    }

    saveHighScores() {
        localStorage.setItem('swapEmHighScores', JSON.stringify(this.highScores));
    }

    createRandomTile() {
        try {
            const availableColors = COLORS[this.currentColorCount];
            if (!availableColors) {
                console.error('No colors available for count:', this.currentColorCount);
                return new Tile('red'); // Fallback
            }
            return new Tile(availableColors[Math.floor(Math.random() * availableColors.length)]);
        } catch (error) {
            console.error('Error in createRandomTile:', error);
            return new Tile('red'); // Fallback
        }
    }

    createGrid() {
        this.grid = Array(GRID_HEIGHT).fill().map(() => 
            Array(GRID_WIDTH).fill().map(() => this.createRandomTile())
        );
        
        // Keep recreating until no matches exist
        while (this.checkMatches().size > 0) {
            for (let y = 0; y < GRID_HEIGHT; y++) {
                for (let x = 0; x < GRID_WIDTH; x++) {
                    if (this.hasMatchAt(x, y)) {
                        // Find a color that doesn't create a match
                        let availableColors = [...COLORS[this.currentColorCount]];
                        while (availableColors.length > 0) {
                            const randomIndex = Math.floor(Math.random() * availableColors.length);
                            const testColor = availableColors[randomIndex];
                            this.grid[y][x] = new Tile(testColor);
                            if (!this.hasMatchAt(x, y)) {
                                break;
                            }
                            availableColors.splice(randomIndex, 1);
                        }
                    }
                }
            }
        }
    }

    hasMatchAt(x, y) {
        const color = this.grid[y][x].color;
        
        // Check horizontal
        if (x >= 2 && 
            this.grid[y][x-1]?.color === color && 
            this.grid[y][x-2]?.color === color) return true;
        if (x >= 1 && x < GRID_WIDTH-1 && 
            this.grid[y][x-1]?.color === color && 
            this.grid[y][x+1]?.color === color) return true;
        if (x < GRID_WIDTH-2 && 
            this.grid[y][x+1]?.color === color && 
            this.grid[y][x+2]?.color === color) return true;
        
        // Check vertical
        if (y >= 2 && 
            this.grid[y-1][x]?.color === color && 
            this.grid[y-2][x]?.color === color) return true;
        if (y >= 1 && y < GRID_HEIGHT-1 && 
            this.grid[y-1][x]?.color === color && 
            this.grid[y+1][x]?.color === color) return true;
        if (y < GRID_HEIGHT-2 && 
            this.grid[y+1][x]?.color === color && 
            this.grid[y+2][x]?.color === color) return true;
            
        return false;
    }

    drawGradientRect(x, y, width, height, color, isHovered) {
        const gradient = this.ctx.createLinearGradient(x, y, x, y + height);
        const baseColor = isHovered ? this.lightenColor(color, 15) : color;
        
        // Use a smaller gradient area to keep colors more vibrant
        gradient.addColorStop(0, baseColor);
        gradient.addColorStop(0.7, baseColor);  // Keep solid color for longer
        gradient.addColorStop(1, this.lightenColor(baseColor, 30));  // Less lightening at the bottom
        
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(x, y, width, height);
        this.ctx.strokeStyle = 'white';
        this.ctx.strokeRect(x, y, width, height);
        
        // Only check for special tiles if we're not in the start menu
        if (!this.inStartMenu && this.grid) {
            // Calculate grid position
            const gridY = Math.floor((y - 36) / TILE_SIZE);
            const gridX = Math.floor(x / TILE_SIZE);
            
            // Check if position is within grid bounds
            if (gridY >= 0 && gridY < GRID_HEIGHT && 
                gridX >= 0 && gridX < GRID_WIDTH) {
                const tile = this.grid[gridY][gridX];
                if (tile && tile.specialType && this.specialTileImages[tile.specialType]) {
                    const image = this.specialTileImages[tile.specialType];
                    this.ctx.drawImage(image, x, y, width, height);
                }
            }
        }
    }

    lightenColor(color, percent) {
        const hex = color.replace('#', '');
        const num = parseInt(hex, 16);
        const amt = Math.round(2.55 * percent);
        const R = Math.min(255, ((num >> 16) + amt));
        const G = Math.min(255, (((num >> 8) & 0x00FF) + amt));
        const B = Math.min(255, ((num & 0x0000FF) + amt));
        return `#${(1 << 24 | R << 16 | G << 8 | B).toString(16).slice(1)}`;
    }

    checkMatches() {
        const matches = new Set();
        
        // Horizontal matches
        for (let y = 0; y < GRID_HEIGHT; y++) {
            for (let x = 0; x < GRID_WIDTH - 2; x++) {
                if (this.grid[y][x] && this.grid[y][x+1] && this.grid[y][x+2] &&
                    this.grid[y][x].color === this.grid[y][x+1].color &&
                    this.grid[y][x].color === this.grid[y][x+2].color) {
                    matches.add(JSON.stringify([y, x]));
                    matches.add(JSON.stringify([y, x+1]));
                    matches.add(JSON.stringify([y, x+2]));
                }
            }
        }

        // Vertical matches
        for (let x = 0; x < GRID_WIDTH; x++) {
            for (let y = 0; y < GRID_HEIGHT - 2; y++) {
                if (this.grid[y][x] && this.grid[y+1][x] && this.grid[y+2][x] &&
                    this.grid[y][x].color === this.grid[y+1][x].color &&
                    this.grid[y][x].color === this.grid[y+2][x].color) {
                    matches.add(JSON.stringify([y, x]));
                    matches.add(JSON.stringify([y+1, x]));
                    matches.add(JSON.stringify([y+2, x]));
                }
            }
        }

        return matches;
    }

    handleSpecialTileEffects(matches) {
        const tilesToRemove = new Set(matches);
        const processedSpecialTiles = new Set();
        let newTilesToCheck = new Set(matches);

        while (newTilesToCheck.size > 0) {
            const tilesToCheck = new Set(newTilesToCheck);
            newTilesToCheck = new Set();

            for (const matchStr of tilesToCheck) {
                const [y, x] = JSON.parse(matchStr);
                if (this.grid[y][x]?.specialType && !processedSpecialTiles.has(matchStr)) {
                    processedSpecialTiles.add(matchStr);

                    switch(this.grid[y][x].specialType) {
                        case 'L': // Horizontal line
                            for (let col = 0; col < GRID_WIDTH; col++) {
                                const newTile = JSON.stringify([y, col]);
                                if (!tilesToRemove.has(newTile)) {
                                    tilesToRemove.add(newTile);
                                    newTilesToCheck.add(newTile);
                                }
                            }
                            break;
                        case 'D': // Vertical line
                            for (let row = 0; row < GRID_HEIGHT; row++) {
                                const newTile = JSON.stringify([row, x]);
                                if (!tilesToRemove.has(newTile)) {
                                    tilesToRemove.add(newTile);
                                    newTilesToCheck.add(newTile);
                                }
                            }
                            break;
                        case 'X': // Cross
                            for (let col = 0; col < GRID_WIDTH; col++) {
                                const newTile = JSON.stringify([y, col]);
                                if (!tilesToRemove.has(newTile)) {
                                    tilesToRemove.add(newTile);
                                    newTilesToCheck.add(newTile);
                                }
                            }
                            for (let row = 0; row < GRID_HEIGHT; row++) {
                                const newTile = JSON.stringify([row, x]);
                                if (!tilesToRemove.has(newTile)) {
                                    tilesToRemove.add(newTile);
                                    newTilesToCheck.add(newTile);
                                }
                            }
                            break;
                    }
                }
            }
        }

        return tilesToRemove;
    }

    handleMatchCreation(matches) {
        if (matches.size >= 4) {
            const matchArray = Array.from(matches).map(m => JSON.parse(m));
            const randomColor = COLORS[this.currentColorCount][
                Math.floor(Math.random() * this.currentColorCount)
            ];
            let specialType = null;

            if (matches.size === 4) specialType = 'L';
            else if (matches.size === 5) specialType = 'D';
            else if (matches.size >= 6) specialType = 'X';

            if (specialType) {
                const randomMatch = matchArray[Math.floor(Math.random() * matchArray.length)];
                this.grid[0][randomMatch[1]] = new Tile(randomColor, specialType);
            }
        }
    }

    animateFall() {
        let fell = false;
        
        for (let x = 0; x < GRID_WIDTH; x++) {
            let bottom = GRID_HEIGHT - 1;
            for (let y = GRID_HEIGHT - 1; y >= 0; y--) {
                if (this.grid[y][x]) {
                    if (bottom !== y) {
                        this.grid[bottom][x] = this.grid[y][x];
                        this.grid[y][x] = null;
                        fell = true;
                    }
                    bottom--;
                }
            }
            // Fill empty spaces with new tiles
            while (bottom >= 0) {
                this.grid[bottom][x] = this.createRandomTile();
                bottom--;
                fell = true;
            }
        }

        return fell;
    }

    calculateBaseScore(matches) {
        const matchCount = matches.size;
        let score = 0;

        if (matchCount === 3) score = 30;
        else if (matchCount === 4) score = 50;
        else if (matchCount === 5) score = 100;
        else if (matchCount >= 6) score = 200;

        return score;
    }

    calculateSpecialTileScore(tileCount) {
        return tileCount * 10; // 10 points per tile removed by special effects
    }

    drawGrid() {
        const mousePos = this.getMousePosition();
        const hoverX = Math.floor(mousePos.x / TILE_SIZE);
        const hoverY = Math.floor((mousePos.y - 36) / TILE_SIZE);

        for (let y = 0; y < GRID_HEIGHT; y++) {
            for (let x = 0; x < GRID_WIDTH; x++) {
                const tile = this.grid[y][x];
                if (tile) {
                    const isSelected = this.selectedTile && 
                        this.selectedTile[0] === x && 
                        this.selectedTile[1] === y;
                    const isHovered = !this.isProcessing && x === hoverX && y === hoverY;
                    const isFalling = this.fallingTiles.has(`${x},${y}`);
                    
                    // Add slight y-offset for falling animation
                    // const yOffset = isFalling ? 4 : 0;
                    
                    this.drawGradientRect(
                        x * TILE_SIZE, 
                        // y * TILE_SIZE + 36 + yOffset, 
                        y * TILE_SIZE + 36,
                        TILE_SIZE, 
                        TILE_SIZE, 
                        tile.color,
                        isHovered
                    );
                    
                    // Draw special tile image if exists
                    if (tile.specialType && this.specialTileImages[tile.specialType]) {
                        const image = this.specialTileImages[tile.specialType];
                        this.ctx.drawImage(
                            image,
                            x * TILE_SIZE,
                            y * TILE_SIZE + 36,
                            TILE_SIZE,
                            TILE_SIZE
                        );
                    }

                    // Selected tile highlight
                    if (isSelected) {
                        this.ctx.strokeStyle = 'white';
                        this.ctx.lineWidth = 4;
                        this.ctx.strokeRect(
                            x * TILE_SIZE,
                            y * TILE_SIZE + 36,
                            TILE_SIZE,
                            TILE_SIZE
                        );
                        this.ctx.lineWidth = 1;
                    }
                }
            }
        }
    }

    drawStartMenu() {
        this.ctx.fillStyle = 'black';
        this.ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

        // Title
        this.ctx.fillStyle = 'white';
        this.ctx.font = '48px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('Swap\'em!', SCREEN_WIDTH/2, 100);

        // Draw difficulty buttons
        this.colorButtons.forEach(button => {
            this.drawGradientRect(
                button.rect.x,
                button.rect.y,
                button.rect.width,
                button.rect.height,
                button.color
            );

            // Button text
            this.ctx.fillStyle = 'white';
            this.ctx.font = '24px Arial';
            this.ctx.fillText(
                `${button.colors} Col`,
                button.rect.x + button.rect.width/2,
                button.rect.y + button.rect.height/2 + 8
            );

            // High score
            this.ctx.fillStyle = 'yellow';
            this.ctx.font = '20px Arial';
            this.ctx.fillText(
                `${this.highScores[button.colors]}`,
                button.rect.x + button.rect.width/2,
                button.rect.y + button.rect.height + 30
            );
        });

        // Instructions
        this.ctx.fillStyle = 'yellow';
        this.ctx.font = '18px Arial';
        this.ctx.fillText('Click to swap em tiles!', SCREEN_WIDTH/2, SCREEN_HEIGHT - 80);

        this.ctx.fillStyle = 'gray';
        this.ctx.fillText('Made by Jussi & Claude', SCREEN_WIDTH/2, SCREEN_HEIGHT - 50);
    }

    drawGameOver() {
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

        // Game Over text
        this.ctx.fillStyle = 'white';
        this.ctx.font = '48px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('Game Over', SCREEN_WIDTH/2, 220);

        // Score
        this.ctx.font = '36px Arial';
        this.ctx.fillText(`Final Score: ${this.score}`, SCREEN_WIDTH/2, 280);

        // High score
        if (this.score > this.highScores[this.currentColorCount]) {
            this.ctx.fillStyle = 'yellow';
            this.ctx.fillText('New High Score!', SCREEN_WIDTH/2, 330);
        }

        // Restart instructions
        this.ctx.fillStyle = 'white';
        this.ctx.font = '24px Arial';
        this.ctx.fillText('Try harder!', SCREEN_WIDTH/2, SCREEN_HEIGHT - 100);
    }

    drawScore() {
        this.ctx.fillStyle = 'white';
        this.ctx.font = '24px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(`Score: ${this.score}`, 10, 28);

        this.ctx.textAlign = 'right';
        this.ctx.fillStyle = 'yellow';
        this.ctx.fillText(
            `High Score: ${this.highScores[this.currentColorCount]}`,
            SCREEN_WIDTH - 10,
            28
        );

        if (this.chainMultiplier > 1) {
            this.ctx.fillStyle = 'yellow';
            this.ctx.font = '36px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(
                `${this.chainMultiplier}x`,
                SCREEN_WIDTH - 100,
                100
            );
        }
    }

    handleStartMenuClick(x, y) {
        this.colorButtons.forEach(button => {
            if (x >= button.rect.x && 
                x <= button.rect.x + button.rect.width &&
                y >= button.rect.y && 
                y <= button.rect.y + button.rect.height) {
                
                this.currentColorCount = button.colors;
                this.inStartMenu = false;
                this.resetGame();
            }
        });
    }

    // Modify handleClick to account for scaling
    handleClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        // Convert click coordinates to game coordinates
        const x = (event.clientX - rect.left) / this.scale;
        const y = (event.clientY - rect.top) / this.scale;
        
        if (this.inStartMenu) {
            this.handleStartMenuClick(x, y);
        } else if (this.gameOver) {
            this.resetGame();
        } else {
            this.handleGameClick(x, y);
        }
    }

    handleGameClick(x, y) {
        if (this.isProcessing) return; // Ignore clicks while processing

        const gridX = Math.floor(x / TILE_SIZE);
        const gridY = Math.floor((y - 36) / TILE_SIZE);

        if (gridX >= 0 && gridX < GRID_WIDTH && gridY >= 0 && gridY < GRID_HEIGHT) {
            if (!this.selectedTile) {
                this.selectedTile = [gridX, gridY];
            } else {
                const [selectedX, selectedY] = this.selectedTile;
                if (Math.abs(selectedX - gridX) + Math.abs(selectedY - gridY) === 1) {
                    this.trySwap(selectedX, selectedY, gridX, gridY);
                }
                this.selectedTile = null;
            }
        }
    }

    handleKeyPress(event) {
        if (event.key === 'Escape') {
            if (!this.inStartMenu) {
                if (this.score > this.highScores[this.currentColorCount]) {
                    this.highScores[this.currentColorCount] = this.score;
                    this.saveHighScores();
                }
                this.inStartMenu = true;
            }
        }
    }

    async trySwap(x1, y1, x2, y2) {
        if (this.isProcessing) return;
        
        this.isProcessing = true;
        
        // Temporary swap to check if it creates a match
        const temp = this.grid[y1][x1];
        this.grid[y1][x1] = this.grid[y2][x2];
        this.grid[y2][x2] = temp;

        const matches = this.checkMatches();
        
        if (matches.size > 0) {
            // Valid swap, process matches
            this.chainMultiplier = 1;
            await this.processMatches();
        } else {
            // Invalid swap, swap back
            const temp = this.grid[y1][x1];
            this.grid[y1][x1] = this.grid[y2][x2];
            this.grid[y2][x2] = temp;
        }
        
        this.isProcessing = false;
    }

    async processMatches() {
        let matches;
        let chainReactionOccurred = false;

        while ((matches = this.checkMatches()).size > 0) {
            chainReactionOccurred = true;

            // Calculate match score
            const matchScore = this.calculateBaseScore(matches);
            
            // Process special tile effects
            const tilesToRemove = this.handleSpecialTileEffects(matches);
            
            // Calculate additional score from special tile effects
            // We subtract the original matches size since those are already counted in matchScore
            const additionalTiles = tilesToRemove.size - matches.size;
            const specialScore = this.calculateSpecialTileScore(additionalTiles);
            
            // Add both scores with multiplier
            this.score += (matchScore + specialScore) * this.chainMultiplier;

            // Remove matched tiles with animation
            for (const matchStr of tilesToRemove) {
                const [y, x] = JSON.parse(matchStr);
                this.grid[y][x] = null;
                await new Promise(resolve => setTimeout(resolve, 30)); // This is the delay between removal of each tile
                this.draw();
            }

            // Create special tile if needed
            this.handleMatchCreation(matches);

            // Animate falling tiles
            await this.animateFallWithDelay();

            if (chainReactionOccurred) {
                this.chainMultiplier = Math.min(5, this.chainMultiplier + 1);
            }

            // Check game over
            if (!this.checkValidMoves()) {
                this.gameOver = true;
                if (this.score > this.highScores[this.currentColorCount]) {
                    this.highScores[this.currentColorCount] = this.score;
                    this.saveHighScores();
                }
                // Return to main menu after delay
                setTimeout(() => {
                    this.inStartMenu = true;
                }, 2000);
                break;
            }

            // Delay between cascades
            await new Promise(resolve => setTimeout(resolve, 100)); // This is the delay between chain/combos
        }
    }

    async animateFallWithDelay() {
        let falling = true;
        while (falling) {
            falling = false;
            this.fallingTiles.clear();
            
            // Process column by column
            for (let x = 0; x < GRID_WIDTH; x++) {
                for (let y = GRID_HEIGHT - 1; y >= 0; y--) {
                    if (!this.grid[y][x]) {
                        // Find the first non-null tile above
                        let sourceY = y - 1;
                        while (sourceY >= 0 && !this.grid[sourceY][x]) {
                            sourceY--;
                        }
                        
                        if (sourceY >= 0) {
                            this.grid[y][x] = this.grid[sourceY][x];
                            this.grid[sourceY][x] = null;
                            this.fallingTiles.add(`${x},${y}`);
                            falling = true;
                        } else {
                            // Create new tile with delay
                            await new Promise(resolve => setTimeout(resolve, 50));
                            this.grid[y][x] = this.createRandomTile();
                            this.fallingTiles.add(`${x},${y}`);
                            falling = true;
                        }
                    }
                }
            }
            
            this.draw();
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }

    checkValidMoves() {
        // Check horizontal swaps
        for (let y = 0; y < GRID_HEIGHT; y++) {
            for (let x = 0; x < GRID_WIDTH - 1; x++) {
                // Try swap
                const temp = this.grid[y][x];
                this.grid[y][x] = this.grid[y][x + 1];
                this.grid[y][x + 1] = temp;

                const hasMatch = this.checkMatches().size > 0;

                // Swap back
                this.grid[y][x + 1] = this.grid[y][x];
                this.grid[y][x] = temp;

                if (hasMatch) return true;
            }
        }

        // Check vertical swaps
        for (let x = 0; x < GRID_WIDTH; x++) {
            for (let y = 0; y < GRID_HEIGHT - 1; y++) {
                // Try swap
                const temp = this.grid[y][x];
                this.grid[y][x] = this.grid[y + 1][x];
                this.grid[y + 1][x] = temp;

                const hasMatch = this.checkMatches().size > 0;

                // Swap back
                this.grid[y + 1][x] = this.grid[y][x];
                this.grid[y][x] = temp;

                if (hasMatch) return true;
            }
        }

        return false;
    }

    resetGame() {
        console.log('Starting reset game...'); // Debug log
        try {
            this.createGrid();
            console.log('Grid created'); // Debug log
            this.score = 0;
            this.chainMultiplier = 1;
            this.selectedTile = null;
            this.gameOver = false;
            console.log('Reset game completed'); // Debug log
        } catch (error) {
            console.error('Error in resetGame:', error);
        }
    }

    draw() {
        // Reset transformation matrix before drawing
        this.ctx.setTransform(1, 0, 0, 1, 0, 0);
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Apply scaling
        this.ctx.scale(this.scale, this.scale);
        
        if (this.inStartMenu) {
            this.drawStartMenu();
        } else {
            this.drawGrid();
            this.drawScore();
            if (this.gameOver) {
                this.drawGameOver();
            }
        }
    }

    gameLoop() {
        this.draw();
        requestAnimationFrame(() => this.gameLoop());
    }
}



// Initialize game when window loads
window.onload = () => {
    const game = new Game();
};