import json
import os
import hashlib
from collections import OrderedDict
from var import *
from basfunc import *
MaxDepth=4
class EnhancedTranspositionTable:
    def __init__(self, max_size=500000):
        self.table = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _get_position_hash(self, board, current_turn, piece_has_moved):
        """Generate proper hash including all game state"""
        # Board state
        board_str = ""
        for row in board:
            for piece in row:
                board_str += piece if piece else "."
        
        # Castling rights
        castling = ""
        if not piece_has_moved.get((7, 4), False):  # White king
            if not piece_has_moved.get((7, 7), False):
                castling += "K"
            if not piece_has_moved.get((7, 0), False):
                castling += "Q"
        if not piece_has_moved.get((0, 4), False):  # Black king
            if not piece_has_moved.get((0, 7), False):
                castling += "k"
            if not piece_has_moved.get((0, 0), False):
                castling += "q"
        
        state_str = f"{board_str}|{current_turn}|{castling}"
        return hashlib.md5(state_str.encode()).hexdigest()
    
    def lookup(self, board, current_turn, piece_has_moved, depth, alpha, beta):
        """Lookup with proper bounds checking"""
        pos_hash = self._get_position_hash(board, current_turn, piece_has_moved)
        
        if pos_hash in self.table:
            entry = self.table[pos_hash]
            self.table.move_to_end(pos_hash)  # LRU update
            
            if entry['depth'] >= depth:
                self.hits += 1
                score = entry['score']
                node_type = entry['type']
                
                if node_type == 'exact':
                    return score, entry.get('best_move')
                elif node_type == 'lower' and score >= beta:
                    return score, entry.get('best_move')
                elif node_type == 'upper' and score <= alpha:
                    return score, entry.get('best_move')
        
        self.misses += 1
        return None, None
    
    def store(self, board, current_turn, piece_has_moved, score, depth, best_move=None, node_type='exact'):
        """Store position with LRU eviction"""
        if len(self.table) >= self.max_size:
            self.table.popitem(last=False)  # Remove oldest
        
        pos_hash = self._get_position_hash(board, current_turn, piece_has_moved)
        self.table[pos_hash] = {
            'score': score,
            'depth': depth,
            'best_move': best_move,
            'type': node_type
        }
        self.table.move_to_end(pos_hash)
    
    def get_stats(self):
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return f"TT: {len(self.table)} entries, {hit_rate:.1f}% hit rate"

# Global enhanced transposition table
enhanced_tt = EnhancedTranspositionTable()

def save_transposition_table(filename="enhanced_tt.json"):
    """Save the enhanced transposition table"""
    global enhanced_tt
    
    # Keep only the most valuable entries (deeper searches)
    sorted_entries = sorted(enhanced_tt.table.items(), 
                          key=lambda x: x[1]['depth'], 
                          reverse=True)
    
    keep_count = min(len(sorted_entries), enhanced_tt.max_size // 2)
    entries_to_save = dict(sorted_entries[:keep_count])
    
    # Convert to serializable format
    serializable = {}
    for hash_key, entry in entries_to_save.items():
        serializable[hash_key] = {
            'score': float(entry['score']),
            'depth': int(entry['depth']),
            'best_move': entry.get('best_move'),
            'type': entry['type']
        }
    
    with open(filename, 'w') as f:
        json.dump(serializable, f)
    
    print(f"Saved {len(entries_to_save)} enhanced TT entries to {filename}")

def load_transposition_table(filename="enhanced_tt.json"):
    """Load the enhanced transposition table"""
    global enhanced_tt
    
    if not os.path.exists(filename):
        print(f"Enhanced TT file {filename} not found, starting fresh")
        return
    
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        enhanced_tt.table.clear()
        for hash_key, entry in data.items():
            enhanced_tt.table[hash_key] = entry
        
        print(f"Loaded {len(enhanced_tt.table)} enhanced TT entries from {filename}")
        
    except Exception as e:
        print(f"Error loading enhanced TT: {e}")

# Enhanced minimax that integrates with your existing code
def enhanced_minimax(depth, current_turn, alpha, beta, max_depth):
    """Enhanced minimax using your existing game_state and functions"""
    global enhanced_tt
    
    # Transposition table lookup
    tt_score, tt_best_move = enhanced_tt.lookup(
        game_state.board, current_turn, game_state.piece_has_moved, 
        depth, alpha, beta
    )
    if tt_score is not None:
        return tt_score, tt_best_move
    
    # Terminal conditions
    if depth == 0 or game_state.game_over:
        score = board_score_enhanced()
        # Only store deeper searches to avoid cache pollution
        if depth < max_depth - 1:
            enhanced_tt.store(
                game_state.board, current_turn, game_state.piece_has_moved,
                score, depth, node_type='exact'
            )
        return score, None
    
    # Move ordering - try TT move first, then captures, then others
    moves = get_ordered_moves_enhanced(current_turn, tt_best_move)
    if not moves:
        return board_score_enhanced(), None
    
    best_move = None
    original_alpha = alpha
    
    if current_turn == 'w':  # Maximizing
        max_score = -float('inf')
        
        for move_tuple in moves:
            from_p, to_p, piece = move_tuple
            
            # Make move using your existing function
            move_info = make_move(from_p, to_p, piece)
            
            # Recursive call
            score, _ = enhanced_minimax(depth - 1, 'b', alpha, beta, max_depth)
            
            # Undo move using your existing function
            undo_move(move_info)
            
            if score > max_score:
                max_score = score
                best_move = move_tuple
            
            alpha = max(alpha, score)
            if beta <= alpha:
                break  # Alpha-beta pruning
        
        # Store in transposition table with proper node type
        node_type = 'exact'
        if max_score <= original_alpha:
            node_type = 'upper'
        elif max_score >= beta:
            node_type = 'lower'
        
        enhanced_tt.store(
            game_state.board, current_turn, game_state.piece_has_moved,
            max_score, depth, best_move, node_type
        )
        
        return max_score, best_move
    
    else:  # Minimizing
        min_score = float('inf')
        
        for move_tuple in moves:
            from_p, to_p, piece = move_tuple
            
            # Make move using your existing function
            move_info = make_move(from_p, to_p, piece)
            
            # Recursive call
            score, _ = enhanced_minimax(depth - 1, 'w', alpha, beta, max_depth)
            
            # Undo move using your existing function
            undo_move(move_info)
            
            if score < min_score:
                min_score = score
                best_move = move_tuple
            
            beta = min(beta, score)
            if beta <= alpha:
                break  # Alpha-beta pruning
        
        # Store in transposition table with proper node type
        node_type = 'exact'
        if min_score <= original_alpha:
            node_type = 'upper'
        elif min_score >= beta:
            node_type = 'lower'
        
        enhanced_tt.store(
            game_state.board, current_turn, game_state.piece_has_moved,
            min_score, depth, best_move, node_type
        )
        
        return min_score, best_move

def get_ordered_moves_enhanced(color, tt_best_move=None):
    """Enhanced move ordering using your existing functions"""
    # Get all legal moves using your existing order_moves function
    all_moves = order_moves(color)
    
    ordered_moves = []
    
    # 1. Try transposition table best move first
    if tt_best_move and tt_best_move in all_moves:
        ordered_moves.append(tt_best_move)
        all_moves.remove(tt_best_move)
    
    # 2. Separate captures and quiet moves
    captures = []
    quiet_moves = []
    
    piece_values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}
    
    for move_tuple in all_moves:
        from_p, to_p, piece = move_tuple
        to_r, to_f = to_p
        target = game_state.board[to_r][to_f]
        
        if target:  # Capture
            # Calculate capture value (victim - attacker for MVV-LVA)
            victim_value = piece_values.get(target[1], 0)
            attacker_value = piece_values.get(piece[1], 0)
            capture_score = victim_value - attacker_value
            captures.append((capture_score, move_tuple))
        else:
            quiet_moves.append(move_tuple)
    
    # Sort captures by value (best captures first)
    captures.sort(key=lambda x: x[0], reverse=True)
    capture_moves = [move for _, move in captures]
    
    return ordered_moves + capture_moves + quiet_moves

def board_score_enhanced():
    """Enhanced board evaluation"""
    piece_values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}
    
    score = 0
    for rank in range(ROWS):
        for file in range(COLS):
            piece = game_state.board[rank][file]
            if piece:
                value = piece_values[piece[1]]
                if piece[0] == 'w':
                    score += value
                else:
                    score -= value
    
    # Add simple positional bonuses
    # Center control bonus
    center_squares = [(3,3), (3,4), (4,3), (4,4)]
    for r, f in center_squares:
        piece = game_state.board[r][f]
        if piece:
            bonus = 10 if piece[1] in ['P', 'N', 'B'] else 5
            if piece[0] == 'w':
                score += bonus
            else:
                score -= bonus
    
    return score

# Enhanced best move function that replaces your bMMbestmove_fast
def enhanced_best_move(current_turn, save=False, load=False):
    """Enhanced best move using the new transposition table"""
    global enhanced_tt
    
    if load:
        load_transposition_table()
    
    print(f"Searching depth {MaxDepth}...")
    
    # Use the enhanced minimax
    score, best_move_tuple = enhanced_minimax(
        MaxDepth, current_turn, -float('inf'), float('inf'), MaxDepth
    )
    
    print(enhanced_tt.get_stats())
    print(f"Best move score: {score}")
    
    if best_move_tuple:
        from_p, to_p, piece = best_move_tuple
        orig_r, orig_c = from_p
        dest_r, dest_c = to_p
        
        # Handle castling (keeping your existing logic)
        if piece[1] == 'K':
            # Black short castle
            if orig_r == 0 and orig_c == 4 and dest_r == 0 and dest_c == 6:
                game_state.board[0][5] = 'bR'
                game_state.board[0][7] = ''
            # Black long castle
            elif orig_r == 0 and orig_c == 4 and dest_r == 0 and dest_c == 2:
                game_state.board[0][3] = 'bR'
                game_state.board[0][0] = ''
            # White short castle
            elif orig_r == 7 and orig_c == 4 and dest_r == 7 and dest_c == 6:
                game_state.board[7][5] = 'wR'
                game_state.board[7][7] = ''
            # White long castle
            elif orig_r == 7 and orig_c == 4 and dest_r == 7 and dest_c == 2:
                game_state.board[7][3] = 'wR'
                game_state.board[7][0] = ''
        
        # Make the move
        game_state.board[dest_r][dest_c] = piece
        game_state.board[orig_r][orig_c] = ""
        game_state.last_move = [(orig_r, orig_c), (dest_r, dest_c)]
        
        # Update piece movement tracking
        if (orig_r, orig_c) in game_state.piece_has_moved:
            game_state.piece_has_moved[(orig_r, orig_c)] = True
        if piece[1] in ['K', 'R']:
            game_state.piece_has_moved[(dest_r, dest_c)] = True
        
        # Handle pawn promotion
        promote_pawn(dest_r, dest_c)
        
        # Update king cache
        update_king_cache()
        
        if save:
            save_transposition_table()
    
    return (from_p, to_p) if best_move_tuple else None

# Modified main function - add these imports at the top of your testmain.py
"""
At the top of your testmain.py, add these imports:
from enhanced_savingtsptables import enhanced_best_move, load_transposition_table, save_transposition_table
"""

# Replace your main() function with this enhanced version:
def enhanced_main():
    load_piece_images()
    load_transposition_table()  # Load the enhanced TT
    
    running = True
    game_state.current_turn = 'w'
    update_king_cache()
    
    while running:
        mouse_pos = pygame.mouse.get_pos()

        # Black's turn - use enhanced AI
        if game_state.current_turn == 'b' and not game_state.game_over:
            start_time = time.time()
            
            # Use the enhanced best move function
            best_move = enhanced_best_move('b', save=True, load=False)
            
            if best_move: 
                switch_turn()
                end_time = time.time()
                print(f"Black move time: {end_time-start_time:.3f}s")
                check_game_end()

        # Handle user input (keeping your existing code)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not game_state.game_over:
                if game_state.current_turn == 'w':
                    rank = mouse_pos[1] // SQUARE_SIZE
                    file = mouse_pos[0] // SQUARE_SIZE
                    if is_valid_position(rank, file):
                        piece = game_state.board[rank][file]
                        if piece and piece[0] == 'w':
                            possible_legal_moves = get_legal_moves(piece, rank, file)
                            if possible_legal_moves:
                                game_state.selected_piece = piece
                                game_state.selected_pos = (rank, file)
                                game_state.legal_moves = possible_legal_moves

            elif event.type == pygame.MOUSEBUTTONUP and not game_state.game_over:
                if game_state.current_turn == 'w' and game_state.selected_piece:
                    rank = mouse_pos[1] // SQUARE_SIZE
                    file = mouse_pos[0] // SQUARE_SIZE
                    orig_rank, orig_file = game_state.selected_pos
                    if is_valid_position(rank, file) and (rank, file) in game_state.legal_moves:
                        # Handle white castling
                        if game_state.selected_piece[1] == 'K':
                            if (game_state.selected_piece[0] == 'w' and orig_rank == 7 and orig_file == 4
                                    and rank == 7 and file == 6):
                                game_state.board[7][5] = 'wR'
                                game_state.board[7][7] = ''
                            elif (game_state.selected_piece[0] == 'w' and orig_rank == 7 and orig_file == 4
                                    and rank == 7 and file == 2):
                                game_state.board[7][3] = 'wR'
                                game_state.board[7][0] = ''

                        game_state.board[rank][file] = game_state.selected_piece
                        game_state.board[orig_rank][orig_file] = ""
                        game_state.last_move = [(orig_rank, orig_file), (rank, file)]

                        if (orig_rank, orig_file) in game_state.piece_has_moved:
                            game_state.piece_has_moved[(orig_rank, orig_file)] = True
                        if game_state.selected_piece[1] in ['K','R']:
                            game_state.piece_has_moved[(rank, file)] = True

                        promote_pawn(rank, file)
                        switch_turn()
                        check_game_end()

                    game_state.selected_piece = None
                    game_state.selected_pos = None
                    game_state.legal_moves = []

        screen.fill((0,0,0))
        draw_board()

        if game_state.current_turn == 'w' and game_state.selected_piece and not game_state.game_over:
            piece_image = PIECE_IMAGES[game_state.selected_piece]
            piece_rect = piece_image.get_rect(center=mouse_pos)
            screen.blit(piece_image, piece_rect.topleft)

        pygame.display.flip()
    
    save_transposition_table()  # Save on exit
    pygame.quit()

