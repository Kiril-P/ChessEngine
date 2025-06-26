import pygame
import os
import random
from var import *
from basfunc import is_king_in_check
import chess

pygame.init()

# Load piece images
PIECE_IMAGES = {}
def load_piece_images():
    pieces = [
        "wP", "wR", "wN", "wB", "wQ", "wK",
        "bP", "bR", "bN", "bB", "bQ", "bK"
    ]
    for piece in pieces:
        try:
            PIECE_IMAGES[piece] = pygame.transform.scale(
                pygame.image.load(os.path.join("pieces", f"{piece}.png")),
                (SQUARE_SIZE, SQUARE_SIZE)
            )
        except:
            print(f"Missing image for {piece}")
            # Create blank surface as fallback
            PIECE_IMAGES[piece] = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
            PIECE_IMAGES[piece].fill((255,0,0))  # Red as error indicator

def draw_square(color, position):
    pygame.draw.rect(screen, color, position)

def highlight_squares(squares, color_light, color_dark):
    """
    Fills squares[] with a highlight that depends on
    whether the square is 'light' or 'dark'.
    """
    for (r, f) in squares:
        base_color = color_light if (r + f) % 2 == 0 else color_dark
        rect = (f * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        pygame.draw.rect(screen, base_color, rect)

def draw_board():
    """
    Draw the board, highlight squares, draw pieces,
    and show if there's a check/checkmate.
    """
    # 1. Draw squares
    for file in range(COLS):
        for rank in range(ROWS):
            square_color = LIGHT_COLOR if (file + rank) % 2 != 0 else DARK_COLOR
            x, y = file * SQUARE_SIZE, rank * SQUARE_SIZE
            draw_square(square_color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

    # 2. Highlight last move squares
    if game_state.last_move:
        # Convert python-chess move to coordinates
        from_coords = square_to_coords(game_state.last_move.from_square)
        to_coords = square_to_coords(game_state.last_move.to_square)
        
        for (r, f) in [from_coords, to_coords]:
            rect = (f * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(screen, LAST_MOVE_COLOR, rect)

    # 3. Highlight selected square
    if game_state.selected_piece and game_state.selected_pos is not None:
        (sel_r, sel_f) = game_state.selected_pos
        rect = (sel_f * SQUARE_SIZE, sel_r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        pygame.draw.rect(screen, SELECTED_COLOR, rect)

    # 4. Draw pieces (unless currently dragging)
    for rank in range(ROWS):
        for file in range(COLS):
            piece_str = game_state.get_piece_at(rank, file)
            if piece_str and not (game_state.selected_piece and (rank, file) == game_state.selected_pos):
                x, y = file * SQUARE_SIZE, rank * SQUARE_SIZE
                if piece_str in PIECE_IMAGES:
                    screen.blit(PIECE_IMAGES[piece_str], (x, y))

    # 5. Highlight legal moves
    if game_state.legal_moves:
        # Convert legal moves to coordinates
        legal_coords = []
        for move in game_state.legal_moves:
            if hasattr(move, 'to_square'):
                # It's a python-chess Move object
                to_coords = square_to_coords(move.to_square)
                legal_coords.append(to_coords)
            else:
                # It's already coordinates
                legal_coords.append(move)
        
        highlight_squares(legal_coords, HIGHLIGHT_COLOR_LIGHT, HIGHLIGHT_COLOR_DARK)

    # 6. Highlight king in check with a red border
    for color in ['w', 'b']:
        if is_king_in_check(color):
            king_pos = get_king_pos(color)
            if king_pos:
                kr, kf = king_pos
                check_rect = pygame.Rect(kf * SQUARE_SIZE, kr * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(screen, CHECK_COLOR, check_rect, 4)

    # 7. Checkmate overlay
    if game_state.game_over and game_state.winner:
        display_text = f"Checkmate! {game_state.winner} wins!"
        text_surface = SMALL_FONT.render(display_text, True, (255, 255, 255))

        # Center text
        text_x = (WIDTH - text_surface.get_width()) // 2
        text_y = (HEIGHT - text_surface.get_height()) // 2

        padding = 10
        box_rect = pygame.Rect(
            text_x - padding,
            text_y - padding,
            text_surface.get_width() + 2*padding,
            text_surface.get_height() + 2*padding
        )
        pygame.draw.rect(screen, (0,0,0), box_rect)
        screen.blit(text_surface, (text_x, text_y))