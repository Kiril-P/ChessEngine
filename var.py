import pygame
import chess

# Screen setup
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Board")

# Fonts
pygame.font.init()
SMALL_FONT = pygame.font.SysFont("Arial", 36, bold=True)

# Colors
LIGHT_COLOR = (240, 217, 181)
DARK_COLOR = (181, 136, 99)
HIGHLIGHT_COLOR_LIGHT = (246, 246, 105)
HIGHLIGHT_COLOR_DARK = (180, 180, 30)
LAST_MOVE_COLOR = (255, 223, 88)
SELECTED_COLOR = (255, 160, 122)
CHECK_COLOR = (255, 99, 71)

# Utility functions for coordinate conversion
def square_to_coords(square):
    """Convert python-chess square to (rank, file) coordinates"""
    file = chess.square_file(square)
    rank = 7 - chess.square_rank(square)  # Flip rank for display
    return (rank, file)

def coords_to_square(rank, file):
    """Convert (rank, file) coordinates to python-chess square"""
    chess_rank = 7 - rank  # Flip rank for chess library
    return chess.square(file, chess_rank)

def piece_to_string(piece):
    """Convert python-chess piece to string representation"""
    if piece is None:
        return ""
    color = 'w' if piece.color == chess.WHITE else 'b'
    piece_type = piece.symbol().upper()
    return color + piece_type

def string_to_piece(piece_str):
    """Convert string representation to python-chess piece"""
    if not piece_str:
        return None
    color = chess.WHITE if piece_str[0] == 'w' else chess.BLACK
    piece_type = getattr(chess, piece_str[1].upper())
    return chess.Piece(piece_type, color)

# Chessboard setup
class GameState:
    def __init__(self):
        self.board = chess.Board()  # Use python-chess Board
        self.selected_piece = None
        self.selected_pos = None  # Still use (rank, file) for UI consistency
        self.legal_moves = []  # Will store python-chess Move objects
        self.last_move = None  # Will store python-chess Move object
        self.game_over = False
        self.winner = None  # "White" or "Black"
    
    @property
    def current_turn(self):
        """Get current turn as 'w' or 'b'"""
        return 'w' if self.board.turn == chess.WHITE else 'b'
    
    def get_piece_at(self, rank, file):
        """Get piece at board coordinates as string"""
        square = coords_to_square(rank, file)
        piece = self.board.piece_at(square)
        return piece_to_string(piece)
    
    def is_king_in_check(self, color=None):
        """Check if king is in check"""
        if color is None:
            return self.board.is_check()
        chess_color = chess.WHITE if color == 'w' else chess.BLACK
        return self.board.is_attacked_by(not chess_color, self.board.king(chess_color))
    
    def is_game_over(self):
        """Check if game is over"""
        return self.board.is_game_over()
    
    def get_result(self):
        """Get game result"""
        if self.board.is_checkmate():
            if self.board.turn == chess.WHITE:
                return "Black"  # Black wins
            else:
                return "White"  # White wins
        elif self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.is_fivefold_repetition():
            return "Draw"
        return None

game_state = GameState()