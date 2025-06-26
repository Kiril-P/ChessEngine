from var import *
import chess

# King cache is no longer needed with python-chess
# The library handles this internally

def get_king_pos(color):
    """Get king position for given color"""
    chess_color = chess.WHITE if color == 'w' else chess.BLACK
    king_square = game_state.board.king(chess_color)
    if king_square is None:
        return None
    return square_to_coords(king_square)

def is_square_attacked(rank, file, attacking_color):
    """Check if square is attacked by given color"""
    square = coords_to_square(rank, file)
    chess_color = chess.WHITE if attacking_color == 'w' else chess.BLACK
    return game_state.board.is_attacked_by(chess_color, square)

def is_king_in_check(color):
    """Check if king is in check"""
    chess_color = chess.WHITE if color == 'w' else chess.BLACK
    # Temporarily set the turn to check if this color's king is in check
    original_turn = game_state.board.turn
    game_state.board.turn = not chess_color  # Opponent's turn
    result = game_state.board.is_check()
    game_state.board.turn = original_turn
    return result

def is_king_in_check_fast(color):
    """Optimized check detection - same as above since python-chess is already optimized"""
    return is_king_in_check(color)

# Move history is handled by python-chess internally
move_history = []

def make_move(from_p, to_p, piece=None):
    """Make a move using python-chess"""
    from_r, from_f = from_p
    to_r, to_f = to_p
    
    from_square = coords_to_square(from_r, from_f)
    to_square = coords_to_square(to_r, to_f)
    
    # Find the matching legal move
    move = None
    for legal_move in game_state.board.legal_moves:
        if legal_move.from_square == from_square and legal_move.to_square == to_square:
            move = legal_move
            break
    
    if move is None:
        # Create basic move if not found in legal moves (for AI purposes)
        move = chess.Move(from_square, to_square)
    
    # Store move info for undo capability
    move_info = {
        'move': move,
        'board_copy': game_state.board.copy()
    }
    
    # Make the move
    game_state.board.push(move)
    move_history.append(move_info)
    
    return move_info

def undo_move(move_info):
    """Undo a move"""
    if move_history:
        game_state.board = move_info['board_copy']
        move_history.pop()

def order_moves(color):
    """Order moves for better alpha-beta pruning"""
    chess_color = chess.WHITE if color == 'w' else chess.BLACK
    
    if game_state.board.turn != chess_color:
        return []
    
    captures = []
    quiet_moves = []
    
    for move in game_state.board.legal_moves:
        from_coords = square_to_coords(move.from_square)
        to_coords = square_to_coords(move.to_square)
        piece_str = game_state.get_piece_at(from_coords[0], from_coords[1])
        
        move_tuple = (from_coords, to_coords, piece_str)
        
        if game_state.board.is_capture(move):
            captures.append(move_tuple)
        else:
            quiet_moves.append(move_tuple)
    
    return captures + quiet_moves

def order_moves_aggressive(color):
    """Order moves for maximum alpha-beta efficiency"""
    chess_color = chess.WHITE if color == 'w' else chess.BLACK
    
    if game_state.board.turn != chess_color:
        return []
    
    captures_high = []
    captures_low = []
    others = []
    
    capture_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    for move in game_state.board.legal_moves:
        from_coords = square_to_coords(move.from_square)
        to_coords = square_to_coords(move.to_square)
        piece_str = game_state.get_piece_at(from_coords[0], from_coords[1])
        
        move_tuple = (from_coords, to_coords, piece_str)
        
        if game_state.board.is_capture(move):
            # Get captured piece value
            captured_piece = game_state.board.piece_at(move.to_square)
            if captured_piece:
                target_value = capture_values.get(captured_piece.symbol().upper(), 0)
                attacker_value = capture_values.get(piece_str[1], 0)
                
                if target_value >= attacker_value:
                    captures_high.append(move_tuple)
                else:
                    captures_low.append(move_tuple)
            else:
                others.append(move_tuple)
        else:
            others.append(move_tuple)
    
    return captures_high + captures_low + others

def get_pseudo_legal_moves_fast(color):
    """Generate all pseudo-legal moves"""
    chess_color = chess.WHITE if color == 'w' else chess.BLACK
    
    if game_state.board.turn != chess_color:
        return []
    
    moves = []
    for move in game_state.board.legal_moves:
        from_coords = square_to_coords(move.from_square)
        to_coords = square_to_coords(move.to_square)
        piece_str = game_state.get_piece_at(from_coords[0], from_coords[1])
        moves.append((from_coords, to_coords, piece_str))
    
    return moves

def can_castle_kingside(color):
    """Check if kingside castling is possible"""
    chess_color = chess.WHITE if color == 'w' else chess.BLACK
    if chess_color == chess.WHITE:
        return game_state.board.has_kingside_castling_rights(chess.WHITE)
    else:
        return game_state.board.has_kingside_castling_rights(chess.BLACK)

def can_castle_queenside(color):
    """Check if queenside castling is possible"""
    chess_color = chess.WHITE if color == 'w' else chess.BLACK
    if chess_color == chess.WHITE:
        return game_state.board.has_queenside_castling_rights(chess.WHITE)
    else:
        return game_state.board.has_queenside_castling_rights(chess.BLACK)

def get_potential_moves(piece_str, rank, file):
    """Get potential moves for a piece at given position"""
    square = coords_to_square(rank, file)
    piece = game_state.board.piece_at(square)
    
    if piece is None:
        return []
    
    moves = []
    for move in game_state.board.legal_moves:
        if move.from_square == square:
            to_coords = square_to_coords(move.to_square)
            moves.append(to_coords)
    
    return moves

def get_legal_moves(piece_str, rank, file):
    """Get legal moves for a piece at given position"""
    return get_potential_moves(piece_str, rank, file)

def promote_pawn(rank, file):
    """Handle pawn promotion - python-chess handles this automatically"""
    pass

def check_game_end():
    """Check if game has ended"""
    if game_state.board.is_game_over():
        if game_state.board.is_checkmate():
            game_state.winner = 'White' if game_state.board.turn == chess.BLACK else 'Black'
            print(f'Checkmate! {game_state.winner} wins!')
        elif game_state.board.is_stalemate():
            print('Stalemate! Draw!')
        elif game_state.board.is_insufficient_material():
            print('Draw by insufficient material!')
        elif game_state.board.is_fivefold_repetition():
            print('Draw by fivefold repetition!')
        
        game_state.game_over = True
    elif game_state.board.is_check():
        color = 'White' if game_state.board.turn == chess.WHITE else 'Black'
        print(f'{color} is in check!')

def is_valid_position(rank, file):
    """Check if position is valid"""
    return 0 <= rank < ROWS and 0 <= file < COLS

def generate_moves_in_directions(rank, file, directions, max_steps=8):
    """Generate moves in given directions - now using python-chess"""
    square = coords_to_square(rank, file)
    moves = []
    
    for move in game_state.board.legal_moves:
        if move.from_square == square:
            to_coords = square_to_coords(move.to_square)
            moves.append(to_coords)
    
    return moves