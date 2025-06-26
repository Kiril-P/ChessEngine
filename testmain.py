import pygame
import chess
import chess.pgn
import time
from var import *
from initi import *
from savingtsptables import enhanced_best_move, load_transposition_table, save_transposition_table, enhanced_tt

MaxDepth = 4

def board_score_fast(board):
    """Lightning-fast evaluation using python-chess"""
    if board.is_checkmate():
        return -9999 if board.turn else 9999
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    piece_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0
    }
    
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value
    return score

def convert_square_to_chess(rank, file):
    """Convert pygame coordinates to chess square"""
    # pygame uses (rank, file) where rank 0 is top, file 0 is left
    # chess uses algebraic notation where a1 is bottom-left
    chess_file = file  # a=0, b=1, ..., h=7
    chess_rank = 7 - rank  # 1st rank = 7, 8th rank = 0 in pygame
    return chess.square(chess_file, chess_rank)

def convert_chess_to_square(chess_square):
    """Convert chess square to pygame coordinates"""
    file = chess.square_file(chess_square)
    rank = chess.square_rank(chess_square)
    pygame_rank = 7 - rank
    pygame_file = file
    return pygame_rank, pygame_file

def get_piece_at_pygame_pos(board, rank, file):
    """Get piece at pygame position"""
    chess_square = convert_square_to_chess(rank, file)
    return board.piece_at(chess_square)

def is_valid_position(rank, file):
    """Check if position is within board bounds"""
    return 0 <= rank < 8 and 0 <= file < 8

def get_legal_moves_for_square(board, rank, file):
    """Get legal moves for a piece at pygame coordinates"""
    chess_square = convert_square_to_chess(rank, file)
    piece = board.piece_at(chess_square)
    
    if not piece:
        return []
    
    legal_moves = []
    for move in board.legal_moves:
        if move.from_square == chess_square:
            to_rank, to_file = convert_chess_to_square(move.to_square)
            legal_moves.append((to_rank, to_file))
    
    return legal_moves

def make_move_from_pygame(board, from_rank, from_file, to_rank, to_file):
    """Make a move using pygame coordinates"""
    from_square = convert_square_to_chess(from_rank, from_file)
    to_square = convert_square_to_chess(to_rank, to_file)
    
    # Handle pawn promotion - always promote to queen for simplicity
    piece = board.piece_at(from_square)
    move = chess.Move(from_square, to_square)
    
    if piece and piece.piece_type == chess.PAWN:
        # Check if it's a promotion move
        if (piece.color == chess.WHITE and to_rank == 0) or \
           (piece.color == chess.BLACK and to_rank == 7):
            move = chess.Move(from_square, to_square, promotion=chess.QUEEN)
    
    if move in board.legal_moves:
        board.push(move)
        return True
    return False

def draw_board_from_chess(screen, board, selected_pos=None, legal_moves=None, last_move=None):
    """Draw the chess board using python-chess board state"""
    # Draw squares
    for rank in range(8):
        for file in range(8):
            color = LIGHT_COLOR if (rank + file) % 2 == 0 else DARK_COLOR
            
            # Highlight selected square
            if selected_pos and selected_pos == (rank, file):
                color = SELECTED_COLOR
            
            # Highlight legal moves
            if legal_moves and (rank, file) in legal_moves:
                color = HIGHLIGHT_COLOR_LIGHT if (rank + file) % 2 == 0 else HIGHLIGHT_COLOR_DARK
            
            # Highlight last move
            if last_move:
                from_rank, from_file = convert_chess_to_square(last_move.from_square)
                to_rank, to_file = convert_chess_to_square(last_move.to_square)
                if (rank, file) in [(from_rank, from_file), (to_rank, to_file)]:
                    color = LAST_MOVE_COLOR
            
            rect = pygame.Rect(file * SQUARE_SIZE, rank * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(screen, color, rect)
    
    # Draw pieces
    for rank in range(8):
        for file in range(8):
            chess_square = convert_square_to_chess(rank, file)
            piece = board.piece_at(chess_square)
            
            if piece:
                # Convert python-chess piece to our piece notation
                color_char = 'w' if piece.color == chess.WHITE else 'b'
                piece_char = piece.symbol().upper()
                piece_key = color_char + piece_char
                
                if piece_key in PIECE_IMAGES:
                    piece_image = PIECE_IMAGES[piece_key]
                    piece_rect = piece_image.get_rect()
                    piece_rect.center = (file * SQUARE_SIZE + SQUARE_SIZE // 2,
                                       rank * SQUARE_SIZE + SQUARE_SIZE // 2)
                    screen.blit(piece_image, piece_rect)

def check_game_over(board):
    """Check if the game is over and update game state"""
    if board.is_game_over():
        if board.is_checkmate():
            winner = "White" if board.turn == chess.BLACK else "Black"
            print(f"Checkmate! {winner} wins!")
            game_state.winner = winner
        elif board.is_stalemate():
            print("Stalemate!")
            game_state.winner = "Draw"
        elif board.is_insufficient_material():
            print("Draw by insufficient material!")
            game_state.winner = "Draw"
        else:
            print("Game over!")
            game_state.winner = "Draw"
        
        game_state.game_over = True
        return True
    return False

def main():
    pygame.init()
    load_piece_images()
    load_transposition_table()
    
    # Initialize python-chess board
    board = chess.Board()
    
    running = True
    selected_piece_pos = None
    legal_moves = []
    
    print("Enhanced Chess AI loaded with python-chess!")
    print("Transposition table ready.")
    print(f"Starting position: {board.fen()}")
    
    while running:
        mouse_pos = pygame.mouse.get_pos()

        # AI's turn (Black)
        if board.turn == chess.BLACK and not board.is_game_over():
            start_time = time.time()
            
            print(f"\nBlack thinking (depth {MaxDepth})...")
            print(f"Position: {board.fen()}")
            
            # Use the enhanced best move function
            best_move = enhanced_best_move(board, save=True, load=False)
            
            if best_move:
                print(f"Black plays: {best_move}")
                board.push(best_move)
                
                end_time = time.time()
                print(f"Black move completed in {end_time-start_time:.3f}s")
                print(enhanced_tt.get_stats())
                
                check_game_over(board)
            else:
                print("No legal moves found for black!")
                game_state.game_over = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Saving transposition table...")
                save_transposition_table()
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not board.is_game_over():
                if board.turn == chess.WHITE:  # Only allow moves on White's turn
                    rank = mouse_pos[1] // SQUARE_SIZE
                    file = mouse_pos[0] // SQUARE_SIZE
                    
                    if is_valid_position(rank, file):
                        piece = get_piece_at_pygame_pos(board, rank, file)
                        
                        # Only allow selection of White pieces
                        if piece and piece.color == chess.WHITE:
                            possible_moves = get_legal_moves_for_square(board, rank, file)
                            if possible_moves:
                                selected_piece_pos = (rank, file)
                                legal_moves = possible_moves
                                print(f"Selected {piece.symbol()} at ({rank},{file}) with {len(possible_moves)} legal moves")

            elif event.type == pygame.MOUSEBUTTONUP and not board.is_game_over():
                if board.turn == chess.WHITE and selected_piece_pos:
                    rank = mouse_pos[1] // SQUARE_SIZE
                    file = mouse_pos[0] // SQUARE_SIZE
                    orig_rank, orig_file = selected_piece_pos
                    
                    if is_valid_position(rank, file) and (rank, file) in legal_moves:
                        piece = get_piece_at_pygame_pos(board, orig_rank, orig_file)
                        print(f"White moves {piece.symbol()} from ({orig_rank},{orig_file}) to ({rank},{file})")
                        
                        # Make the move
                        if make_move_from_pygame(board, orig_rank, orig_file, rank, file):
                            print(f"Move successful. New position: {board.fen()}")
                            check_game_over(board)
                        else:
                            print("Invalid move!")
                    
                    # Clear selection
                    selected_piece_pos = None
                    legal_moves = []

        # Draw everything
        screen.fill((0, 0, 0))
        last_move = board.peek() if board.move_stack else None
        draw_board_from_chess(screen, board, selected_piece_pos, legal_moves, last_move)

        # If a piece is selected, show it following the mouse
        if selected_piece_pos and board.turn == chess.WHITE and not board.is_game_over():
            piece = get_piece_at_pygame_pos(board, selected_piece_pos[0], selected_piece_pos[1])
            if piece:
                color_char = 'w' if piece.color == chess.WHITE else 'b'
                piece_char = piece.symbol().upper()
                piece_key = color_char + piece_char
                
                if piece_key in PIECE_IMAGES:
                    piece_image = PIECE_IMAGES[piece_key]
                    piece_rect = piece_image.get_rect(center=mouse_pos)
                    screen.blit(piece_image, piece_rect.topleft)

        # Display game status
        if board.is_game_over():
            if board.is_checkmate():
                winner = "White" if board.turn == chess.BLACK else "Black"
                status_text = f"Checkmate! {winner} wins!"
            elif board.is_stalemate():
                status_text = "Stalemate!"
            else:
                status_text = "Game Over!"
            
            text_surface = SMALL_FONT.render(status_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(text_surface, text_rect)

        pygame.display.flip()
    
    print("Final save of transposition table...")
    save_transposition_table()
    print(f"Final stats: {enhanced_tt.get_stats()}")
    pygame.quit()

if __name__ == '__main__':
    main()