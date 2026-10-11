import pygame
import random
import numpy as np

# Initialize Pygame
pygame.init()
pygame.font.init()

# Screen Setup
WIDTH, HEIGHT = 1100, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Market Battlefront - Dynamic Camera Order Book")

# Color Palette
BG_COLOR = (11, 15, 25)
PANEL_BG = (21, 29, 46)
TEXT_COLOR = (240, 244, 248)
MUTED_TEXT = (130, 145, 165)
BID_GREEN = (34, 197, 94)
ASK_RED = (239, 68, 68)
MID_YELLOW = (234, 179, 8)
CAVALRY_GREEN = (134, 239, 172)
CAVALRY_RED = (252, 165, 165)

FONT = pygame.font.SysFont("Consolas", 15)
HEADER_FONT = pygame.font.SysFont("Consolas", 20, bold=True)
TITLE_FONT = pygame.font.SysFont("Consolas", 26, bold=True)

clock = pygame.time.Clock()
FPS = 60

# Order Book Setup
PRICE_STEP = 0.50

def draw_text(text, font, color, x, y):
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))

def ensure_orderbook_depth(bids, asks, mid_price, depth=12):
    """Spawns liquidity around the current mid_price if depth runs thin."""
    # Build bids below best bid
    best_b = max(bids.keys()) if bids else mid_price - PRICE_STEP
    for i in range(depth):
        p = round(best_b - i * PRICE_STEP, 2)
        if p not in bids and p > 0:
            bids[p] = random.randint(30, 90)

    # Build asks above best ask
    best_a = min(asks.keys()) if asks else mid_price + PRICE_STEP
    for i in range(depth):
        p = round(best_a + i * PRICE_STEP, 2)
        if p not in asks:
            asks[p] = random.randint(30, 90)

def main():
    running = True
    frame_count = 0
    auto_battle = True

    # Initialize State inside main() to avoid global scoping issues
    center_price = 100.0
    bids = {round(center_price - (i + 1) * PRICE_STEP, 2): random.randint(40, 100) for i in range(12)}
    asks = {round(center_price + (i + 1) * PRICE_STEP, 2): random.randint(40, 100) for i in range(12)}
    attackers = []

    best_bid = max(bids.keys())
    best_ask = min(asks.keys())
    mid_price = round((best_bid + best_ask) / 2.0, 2)
    price_history = [mid_price]

    # Camera smooth x-offset tracking
    camera_mid = mid_price

    while running:
        dt = clock.tick(FPS) / 1000.0
        frame_count += 1

        # Smooth camera tracking towards current mid-price
        camera_mid += (mid_price - camera_mid) * 0.1

        # --- 1. HANDLE INPUT ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    auto_battle = not auto_battle
                # Launch Manual BUY Cavalry Charge (Hits Ask Wall)
                elif event.key == pygame.K_b:
                    attackers.append({
                        'x': 50,
                        'target_price': best_ask,
                        'side': 'BUY',
                        'size': random.randint(50, 120),
                        'speed': 14
                    })
                # Launch Manual SELL Cavalry Charge (Hits Bid Wall)
                elif event.key == pygame.K_s:
                    attackers.append({
                        'x': WIDTH - 50,
                        'target_price': best_bid,
                        'side': 'SELL',
                        'size': random.randint(50, 120),
                        'speed': 14
                    })

        # --- 2. RANDOM MARKET FLOW (REINFORCEMENTS) ---
        if auto_battle and frame_count % 10 == 0:
            if random.random() < 0.5:
                attackers.append({
                    'x': 80,
                    'target_price': best_ask,
                    'side': 'BUY',
                    'size': random.randint(15, 50),
                    'speed': random.randint(8, 16)
                })
            else:
                attackers.append({
                    'x': WIDTH - 80,
                    'target_price': best_bid,
                    'side': 'SELL',
                    'size': random.randint(15, 50),
                    'speed': random.randint(8, 16)
                })

        # --- 3. REPLENISH LIMIT ORDERS & KEEP DEPTH FULL ---
        ensure_orderbook_depth(bids, asks, mid_price)

        if frame_count % 20 == 0:
            for p in list(bids.keys()):
                if bids[p] < 120 and random.random() < 0.3:
                    bids[p] += random.randint(5, 15)
            for p in list(asks.keys()):
                if asks[p] < 120 and random.random() < 0.3:
                    asks[p] += random.randint(5, 15)

        # --- 4. UPDATE ATTACKERS & RESOLVE COMBAT ---
        best_bid = max(bids.keys())
        best_ask = min(asks.keys())
        mid_x = WIDTH // 2

        active_attackers = []
        for att in attackers:
            if att['side'] == 'BUY':
                att['x'] += att['speed']
                # Calculate dynamic ask wall position on screen
                ask_x = mid_x + int((best_ask - camera_mid) * 140)

                if att['x'] >= ask_x:
                    absorbed = min(asks[best_ask], att['size'])
                    asks[best_ask] -= absorbed
                    att['size'] -= absorbed

                    if asks[best_ask] <= 0:
                        del asks[best_ask]
                        if len(asks) > 0:
                            best_ask = min(asks.keys())

                    if att['size'] > 0 and len(asks) > 0:
                        active_attackers.append(att)
                else:
                    active_attackers.append(att)

            elif att['side'] == 'SELL':
                att['x'] -= att['speed']
                # Calculate dynamic bid wall position on screen
                bid_x = mid_x - int((camera_mid - best_bid) * 140)

                if att['x'] <= bid_x:
                    absorbed = min(bids[best_bid], att['size'])
                    bids[best_bid] -= absorbed
                    att['size'] -= absorbed

                    if bids[best_bid] <= 0:
                        del bids[best_bid]
                        if len(bids) > 0:
                            best_bid = max(bids.keys())

                    if att['size'] > 0 and len(bids) > 0:
                        active_attackers.append(att)
                else:
                    active_attackers.append(att)

        attackers = active_attackers

        # Recalculate Mid Price & History
        if bids and asks:
            best_bid = max(bids.keys())
            best_ask = min(asks.keys())
            mid_price = round((best_bid + best_ask) / 2.0, 2)
            price_history.append(mid_price)
            if len(price_history) > 400:
                price_history.pop(0)

        # --- 5. RENDER BATTLEFRONT UI ---
        screen.fill(BG_COLOR)

        # Title
        draw_text("ORDER BOOK BATTLEFRONT", TITLE_FONT, TEXT_COLOR, 30, 20)
        draw_text("Dynamic Camera Tracking & Liquidity Spawning System", FONT, MUTED_TEXT, 30, 55)

        # Battle Status Banner
        pygame.draw.rect(screen, PANEL_BG, (30, 85, WIDTH - 60, 60), border_radius=8)
        draw_text(f"BUYERS FRONTLINE: ${best_bid:.2f}", HEADER_FONT, BID_GREEN, 50, 105)
        draw_text(f"SPREAD: ${best_ask - best_bid:.2f}", HEADER_FONT, MID_YELLOW, 440, 105)
        draw_text(f"SELLERS FRONTLINE: ${best_ask:.2f}", HEADER_FONT, ASK_RED, 780, 105)

        # Main Battlefield Canvas
        battle_y = 160
        battle_h = 320
        pygame.draw.rect(screen, PANEL_BG, (30, battle_y, WIDTH - 60, battle_h), border_radius=8)

        # Draw Dynamic Centerline (Relative to camera_mid)
        centerline_x = mid_x + int((mid_price - camera_mid) * 140)
        if 40 < centerline_x < WIDTH - 40:
            pygame.draw.line(screen, MID_YELLOW, (centerline_x, battle_y + 10), (centerline_x, battle_y + battle_h - 10), 2)
            draw_text(f"MID ${mid_price:.2f}", FONT, MID_YELLOW, centerline_x - 35, battle_y + 15)

        # Draw Bid Fortifications (Left Side of Camera)
        for price, vol in list(bids.items()):
            x_pos = mid_x - int((camera_mid - price) * 140)
            if 40 < x_pos < WIDTH - 40:
                bar_h = min(200, vol * 2)
                pygame.draw.rect(screen, BID_GREEN, (x_pos - 8, battle_y + battle_h - bar_h - 30, 16, bar_h), border_radius=3)
                draw_text(f"${price:.1f}", FONT, TEXT_COLOR, x_pos - 20, battle_y + battle_h - 25)
                draw_text(f"{vol}", FONT, MUTED_TEXT, x_pos - 10, battle_y + battle_h - bar_h - 48)

        # Draw Ask Fortifications (Right Side of Camera)
        for price, vol in list(asks.items()):
            x_pos = mid_x + int((price - camera_mid) * 140)
            if 40 < x_pos < WIDTH - 40:
                bar_h = min(200, vol * 2)
                pygame.draw.rect(screen, ASK_RED, (x_pos - 8, battle_y + battle_h - bar_h - 30, 16, bar_h), border_radius=3)
                draw_text(f"${price:.1f}", FONT, TEXT_COLOR, x_pos - 20, battle_y + battle_h - 25)
                draw_text(f"{vol}", FONT, MUTED_TEXT, x_pos - 10, battle_y + battle_h - bar_h - 48)

        # Draw Charging Attackers
        for att in attackers:
            color = CAVALRY_GREEN if att['side'] == 'BUY' else CAVALRY_RED
            size_radius = max(6, int(att['size'] ** 0.5 * 2.2))
            pygame.draw.circle(screen, color, (int(att['x']), battle_y + 160), size_radius)
            draw_text(f"{att['size']}", FONT, BG_COLOR, int(att['x']) - 8, battle_y + 153)

        # Chart Panel
        chart_y = 500
        chart_h = 210
        pygame.draw.rect(screen, PANEL_BG, (30, chart_y, WIDTH - 60, chart_h), border_radius=8)
        draw_text("FRONTLINE PRICE TRAJECTORY", HEADER_FONT, TEXT_COLOR, 50, chart_y + 15)

        if len(price_history) > 1:
            min_p = min(price_history) - 0.50
            max_p = max(price_history) + 0.50
            p_range = max(0.01, max_p - min_p)

            points = []
            for i, p in enumerate(price_history):
                x = 50 + i * (WIDTH - 100) / 400
                y = (chart_y + chart_h - 20) - ((p - min_p) / p_range) * (chart_h - 60)
                points.append((x, y))

            pygame.draw.lines(screen, MID_YELLOW, False, points, 2)

        # Controls Instructions
        draw_text("Controls: [SPACE] Toggle Auto Flow | [B] Manual BUY Attack | [S] Manual SELL Attack", FONT, MUTED_TEXT, 50, chart_y + chart_h - 25)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()