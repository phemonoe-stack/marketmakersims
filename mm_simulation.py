import pygame
import random
import math
import numpy as np

# Initialize Pygame
pygame.init()
pygame.font.init()

# Screen Dimensions & Colors
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Market Maker Simulator - Spread Capture & Hedging")

# Colors
BG_COLOR = (15, 23, 42)
PANEL_BG = (30, 41, 59)
TEXT_COLOR = (241, 245, 249)
MUTED_TEXT = (148, 163, 184)
GREEN = (34, 197, 94)
RED = (239, 68, 68)
BLUE = (59, 130, 246)
YELLOW = (234, 179, 8)

FONT = pygame.font.SysFont("Consolas", 16)
HEADER_FONT = pygame.font.SysFont("Consolas", 20, bold=True)
TITLE_FONT = pygame.font.SysFont("Consolas", 28, bold=True)

# Game State Variables
clock = pygame.time.Clock()
FPS = 60

# Market Mechanics Variables
fair_price = 100.00
market_trend = 0.0
volatility = 0.15

# MM Position & State
cash = 10000.0
inventory = 0  # Net stock position
spread = 0.15  # Half-spread from mid
skew = 0.0     # Quote offset relative to fair price
pnl_history = []
price_history = [fair_price]

# Market Order Log
recent_trades = []

def draw_text(text, font, color, x, y):
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))

def main():
    global fair_price, market_trend, cash, inventory, spread, skew

    running = True
    frame_count = 0

    # Initialize toggles & parameters
    paused = False
    auto_skew_enabled = False
    gamma = 0.001  # Avellaneda-Stoikov risk aversion parameter

    while running:
        dt = clock.tick(FPS) / 1000.0

        # --- 1. HANDLE USER INPUT ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Pause Toggle
                if event.key == pygame.K_p:
                    paused = not paused
                # Auto-Skew Toggle
                elif event.key == pygame.K_a:
                    auto_skew_enabled = not auto_skew_enabled
                # Adjust Spread
                elif event.key == pygame.K_UP:
                    spread = min(1.00, spread + 0.02)
                elif event.key == pygame.K_DOWN:
                    spread = max(0.02, spread - 0.02)
                # Adjust Skew Manually (Disables Auto-Skew)
                elif event.key == pygame.K_LEFT:
                    auto_skew_enabled = False
                    skew -= 0.02
                elif event.key == pygame.K_RIGHT:
                    auto_skew_enabled = False
                    skew += 0.02
                # Manual Delta Hedge
                elif event.key == pygame.K_SPACE:
                    if inventory != 0:
                        hedge_price = fair_price + (0.02 if inventory < 0 else -0.02)
                        cash += inventory * hedge_price
                        recent_trades.append((f"HEDGED {inventory} @ ${hedge_price:.2f}", YELLOW))
                        inventory = 0

        # Pause Logic
        if paused:
            draw_text("|| PAUSED - Press 'P' to Resume", TITLE_FONT, YELLOW, 300, 10)
            pygame.display.flip()
            continue

        frame_count += 1

        # Dynamic Auto-Skew (Avellaneda-Stoikov model)
        if auto_skew_enabled:
            skew = -inventory * gamma

        # --- 2. SIMULATE UNDERLYING MARKET (GBM Process) ---
        if frame_count % 5 == 0:
            drift = market_trend * dt
            shock = np.random.normal(0, volatility)
            fair_price += drift + shock
            fair_price = max(10.0, fair_price)
            price_history.append(fair_price)
            if len(price_history) > 300:
                price_history.pop(0)

        # Periodic trend changes
        if frame_count % 300 == 0:
            market_trend = random.choice([-0.2, -0.1, 0.0, 0.1, 0.2])

        # --- 3. SIMULATE ORDER FLOW & FILL MECHANICS ---
        my_bid = fair_price + skew - spread
        my_ask = fair_price + skew + spread

        bid_fill_prob = 0.03 + max(0, (my_bid - fair_price) * 0.2)
        ask_fill_prob = 0.03 + max(0, (fair_price - my_ask) * 0.2)

        if random.random() < bid_fill_prob:
            qty = random.randint(10, 50)
            inventory += qty
            cash -= qty * my_bid
            recent_trades.append((f"BOUGHT {qty} shs @ ${my_bid:.2f}", GREEN))

        if random.random() < ask_fill_prob:
            qty = random.randint(10, 50)
            inventory -= qty
            cash += qty * my_ask
            recent_trades.append((f"SOLD {qty} shs @ ${my_ask:.2f}", RED))

        if len(recent_trades) > 8:
            recent_trades.pop(0)

        # --- 4. CALCULATE PnL ---
        unrealized_pnl = inventory * fair_price
        total_pnl = (cash + unrealized_pnl) - 10000.0

        # --- 5. RENDER UI ---
        screen.fill(BG_COLOR)

        # Title Panel
        draw_text("MARKET MAKER SIMULATOR", TITLE_FONT, TEXT_COLOR, 30, 20)
        draw_text("Manage inventory skew & capture spread without getting caught in directional flow.", FONT, MUTED_TEXT, 30, 55)

        # Left Panel: Market & Quotes Data
        pygame.draw.rect(screen, PANEL_BG, (30, 90, 440, 260), border_radius=8)
        draw_text("MARKET & QUOTES", HEADER_FONT, TEXT_COLOR, 50, 105)

        draw_text(f"Fair Value (Mid):    ${fair_price:.2f}", FONT, TEXT_COLOR, 50, 145)
        draw_text(f"Your Bid Quote:      ${my_bid:.2f}", FONT, GREEN, 50, 175)
        draw_text(f"Your Ask Quote:      ${my_ask:.2f}", FONT, RED, 50, 205)
        draw_text(f"Half-Spread:         ${spread:.2f}  (↑/↓ to change)", FONT, MUTED_TEXT, 50, 245)
        
        auto_text = " [AUTO]" if auto_skew_enabled else ""
        draw_text(f"Quote Skew:          ${skew:+.2f}{auto_text} (←/→ or 'A')", FONT, YELLOW if auto_skew_enabled else MUTED_TEXT, 50, 275)

        # Right Panel: Risk & Position Data
        pygame.draw.rect(screen, PANEL_BG, (490, 90, 480, 260), border_radius=8)
        draw_text("RISK & INVENTORY", HEADER_FONT, TEXT_COLOR, 510, 105)

        inv_color = GREEN if inventory == 0 else (YELLOW if abs(inventory) < 150 else RED)
        draw_text(f"Net Inventory:       {inventory} shares", FONT, inv_color, 510, 145)
        draw_text(f"Delta Risk Exp:      ${inventory * fair_price:,.2f}", FONT, TEXT_COLOR, 510, 175)
        
        pnl_color = GREEN if total_pnl >= 0 else RED
        draw_text(f"Total Realized PnL:  ${total_pnl:,.2f}", FONT, pnl_color, 510, 205)

        pygame.draw.rect(screen, BLUE, (510, 245, 180, 35), border_radius=5)
        draw_text("[SPACE] DELTA HEDGE", FONT, TEXT_COLOR, 520, 255)

        # Controls Hint
        draw_text("Controls: [P] Pause | [A] Auto-Skew | [SPACE] Hedge | [←/→] Skew | [↑/↓] Spread", FONT, MUTED_TEXT, 30, 350)

        # Price Chart Panel
        pygame.draw.rect(screen, PANEL_BG, (30, 370, 600, 300), border_radius=8)
        draw_text("REAL-TIME MID-PRICE CHART", HEADER_FONT, TEXT_COLOR, 50, 385)

        if len(price_history) > 1:
            min_p = min(price_history) - 0.5
            max_p = max(price_history) + 0.5
            p_range = max(0.01, max_p - min_p)

            points = []
            for i, p in enumerate(price_history):
                x = 50 + i * (560 / 300)
                y = 650 - ((p - min_p) / p_range) * 230
                points.append((x, y))

            pygame.draw.lines(screen, BLUE, False, points, 2)

        # Order Flow Tape Panel
        pygame.draw.rect(screen, PANEL_BG, (640, 370, 330, 300), border_radius=8)
        draw_text("LIVE ORDER FLOW", HEADER_FONT, TEXT_COLOR, 660, 385)

        for i, (msg, col) in enumerate(reversed(recent_trades)):
            draw_text(msg, FONT, col, 660, 420 + i * 28)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()