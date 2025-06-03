import pygame
from var import *
from initi import *
from basfunc import *

from savingtsptables import enhanced_best_move, load_transposition_table, save_transposition_table, enhanced_tt

MaxDepth = 4

piece_value = {'P': 10, 'N': 30, 'B': 30, 'R': 50, 'Q': 90, 'K': 1000}

def board_score():
    score = 0
    for rank in range(ROWS):
        for file in range(COLS):
            curpiece = game_state.board[rank][file]
            if curpiece != "":
                value = piece_value[curpiece[1]]
                score += (value if curpiece[0] == 'w' else -value)
    return score

def board_score_fast():
    """Lightning-fast evaluation"""
    score = 0
    piece_values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}
    
    for rank in range(ROWS):
        for file in range(COLS):
            piece = game_state.board[rank][file]
            if piece:
                value = piece_values[piece[1]]
                if piece[0] == 'w':
                    score += value
                else:
                    score -= value
    return score

# Keep your existing minimax for comparison/fallback
def basicMinMax(depth, current_turn, alpha, beta):
    if depth == 0 or game_state.game_over:
        return board_score()
    
    moves = order_moves(current_turn)
    
    if current_turn == 'w':
        max_score = -float('inf')
        for (from_p, to_p, piece) in moves:
            move = make_move(from_p, to_p, piece)            
            move_value = basicMinMax(depth-1, 'b', alpha, beta)
            undo_move(move)
            max_score = max(max_score, move_value)
            alpha = max(alpha, move_value)
            if beta <= alpha:
                break
        return max_score
    else:
        min_score = float('inf')
        for (from_p, to_p, piece) in moves:
            move = make_move(from_p, to_p, piece)            
            move_value = basicMinMax(depth-1, 'w', alpha, beta)
            undo_move(move)
            min_score = min(min_score, move_value)
            beta = min(beta, move_value)
            if beta <= alpha:
                break
        return min_score

def switch_turn():
    game_state.current_turn = 'b' if game_state.current_turn == 'w' else 'w'

import time

def main():
    load_piece_images()
    load_transposition_table()  # Load the enhanced transposition table
    
    running = True
    game_state.current_turn = 'w'
    update_king_cache()
    
    print("Enhanced Chess AI loaded!")
    print("Transposition table ready.")
    
    while running:
        mouse_pos = pygame.mouse.get_pos()

        # Black's turn - use the enhanced AI
        if game_state.current_turn == 'b' and not game_state.game_over:
            start_time = time.time()
            
            print(f"\nBlack thinking (depth {MaxDepth})...")
            
            # Use the enhanced best move function instead of bMMbestmove_fast
            best_move = enhanced_best_move('b', save=True, load=False)
            
            if best_move: 
                switch_turn()
                end_time = time.time()
                print(f"Black move completed in {end_time-start_time:.3f}s")
                print(enhanced_tt.get_stats())  # Show cache performance
                check_game_end()
            else:
                print("No legal moves found for black!")
                game_state.game_over = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Saving transposition table...")
                save_transposition_table()
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not game_state.game_over:
                # Only let user move if it's White's turn
                if game_state.current_turn == 'w':
                    rank = mouse_pos[1] // SQUARE_SIZE
                    file = mouse_pos[0] // SQUARE_SIZE
                    if is_valid_position(rank, file):
                        piece = game_state.board[rank][file]
                        # Only allow selection if it's White's piece with legal moves
                        if piece and piece[0] == 'w':
                            possible_legal_moves = get_legal_moves(piece, rank, file)
                            if possible_legal_moves:
                                game_state.selected_piece = piece
                                game_state.selected_pos = (rank, file)
                                game_state.legal_moves = possible_legal_moves
                                print(f"Selected {piece} at ({rank},{file}) with {len(possible_legal_moves)} legal moves")

            elif event.type == pygame.MOUSEBUTTONUP and not game_state.game_over:
                if game_state.current_turn == 'w' and game_state.selected_piece:
                    rank = mouse_pos[1] // SQUARE_SIZE
                    file = mouse_pos[0] // SQUARE_SIZE
                    orig_rank, orig_file = game_state.selected_pos
                    
                    if is_valid_position(rank, file) and (rank, file) in game_state.legal_moves:
                        print(f"White moves {game_state.selected_piece} from ({orig_rank},{orig_file}) to ({rank},{file})")
                        
                        # Handle castling for White
                        if game_state.selected_piece[1] == 'K':
                            # White short castle
                            if (game_state.selected_piece[0] == 'w' and orig_rank == 7 and orig_file == 4
                                    and rank == 7 and file == 6):
                                game_state.board[7][5] = 'wR'
                                game_state.board[7][7] = ''
                                print("White castles kingside")
                            # White long castle
                            elif (game_state.selected_piece[0] == 'w' and orig_rank == 7 and orig_file == 4
                                    and rank == 7 and file == 2):
                                game_state.board[7][3] = 'wR'
                                game_state.board[7][0] = ''
                                print("White castles queenside")

                        game_state.board[rank][file] = game_state.selected_piece
                        game_state.board[orig_rank][orig_file] = ""
                        game_state.last_move = [(orig_rank, orig_file), (rank, file)]

                        # Mark if King/Rook moved
                        if (orig_rank, orig_file) in game_state.piece_has_moved:
                            game_state.piece_has_moved[(orig_rank, orig_file)] = True
                        if game_state.selected_piece[1] in ['K','R']:
                            game_state.piece_has_moved[(rank, file)] = True

                        promote_pawn(rank, file)  # Handle pawn promotion
                        switch_turn()
                        check_game_end()

                    game_state.selected_piece = None
                    game_state.selected_pos = None
                    game_state.legal_moves = []

        # Draw everything
        screen.fill((0, 0, 0))
        draw_board()

        # If a White piece is selected, let user drag it
        if game_state.current_turn == 'w' and game_state.selected_piece and not game_state.game_over:
            piece_image = PIECE_IMAGES[game_state.selected_piece]
            piece_rect = piece_image.get_rect(center=mouse_pos)
            screen.blit(piece_image, piece_rect.topleft)

        pygame.display.flip()
    
    print("Final save of transposition table...")
    save_transposition_table()
    print(f"Final stats: {enhanced_tt.get_stats()}")
    pygame.quit()

if __name__ == '__main__':
    main()