import json
import os
import hashlib
from collections import OrderedDict
from var import *
import pandas as pd
import chess
import chess.engine

# from basfunc import *
MaxDepth = 4    
game_df = pd.read_csv("chess_training.csv",nrows=100000)
opening_book = {}
for fen, move in game_df[['fen', 'move']].values:
    if fen not in opening_book:
        opening_book[fen] = []
    opening_book[fen].append(move)

def get_opening_move(fen):
    return opening_book.get(fen, None)

class EnhancedTranspositionTable:
    def __init__(self, max_size=500000):
        self.table = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _get_position_hash(self, board):
        """Generate proper hash from python-chess board"""
        # Use the board's FEN string as a unique identifier
        # This includes position, castling rights, en passant, and turn
        return hashlib.md5(board.fen().encode()).hexdigest()
    
    def lookup(self, board, depth, alpha, beta):
        """Lookup with proper bounds checking"""
        pos_hash = self._get_position_hash(board)
        
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
    
    def store(self, board, score, depth, best_move=None, node_type='exact'):
        """Store position with LRU eviction"""
        if len(self.table) >= self.max_size:
            self.table.popitem(last=False)  # Remove oldest
        
        pos_hash = self._get_position_hash(board)
        # Convert move to string for JSON serialization
        move_str = str(best_move) if best_move else None
        self.table[pos_hash] = {
            'score': score,
            'depth': depth,
            'best_move': move_str,
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

def board_score_enhanced(board):
    """Enhanced board evaluation using python-chess"""
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
    
    # Material evaluation
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value
    
    # Simple positional evaluation
    # Center control bonus
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    for square in center_squares:
        piece = board.piece_at(square)
        if piece:
            bonus = 10 if piece.piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP] else 5
            if piece.color == chess.WHITE:
                score += bonus
            else:
                score -= bonus
    
    # King safety - penalty for exposed king
    white_king_square = board.king(chess.WHITE)
    black_king_square = board.king(chess.BLACK)
    
    if white_king_square:
        # Penalty for king in center during opening/middlegame
        if chess.square_file(white_king_square) in [3, 4] and chess.square_rank(white_king_square) in [3, 4]:
            score -= 20
    
    if black_king_square:
        if chess.square_file(black_king_square) in [3, 4] and chess.square_rank(black_king_square) in [3, 4]:
            score += 20
    
    return score

def get_ordered_moves_enhanced(board, tt_best_move=None):
    """Enhanced move ordering using python-chess"""
    legal_moves = list(board.legal_moves)
    
    if not legal_moves:
        return []
    
    ordered_moves = []
    
    # 1. Try transposition table best move first
    if tt_best_move:
        try:
            # Convert string back to Move object
            move = chess.Move.from_uci(tt_best_move)
            if move in legal_moves:
                ordered_moves.append(move)
                legal_moves.remove(move)
        except:
            pass  # Invalid move string
    
    # 2. Separate captures and quiet moves
    captures = []
    quiet_moves = []
    
    piece_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0
    }
    
    for move in legal_moves:
        if board.is_capture(move):
            # Calculate capture value (victim - attacker for MVV-LVA)
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            
            if victim and attacker:
                victim_value = piece_values.get(victim.piece_type, 0)
                attacker_value = piece_values.get(attacker.piece_type, 0)
                capture_score = victim_value - attacker_value
                captures.append((capture_score, move))
        else:
            quiet_moves.append(move)
    
    # Sort captures by value (best captures first)
    captures.sort(key=lambda x: x[0], reverse=True)
    capture_moves = [move for _, move in captures]
    
    return ordered_moves + capture_moves + quiet_moves

def enhanced_minimax(board, depth, alpha, beta, max_depth, maximizing_player=True):
    """Enhanced minimax using python-chess board"""
    global enhanced_tt
    
    # Transposition table lookup
    tt_score, tt_best_move = enhanced_tt.lookup(board, depth, alpha, beta)
    if tt_score is not None:
        return tt_score, tt_best_move
    
    # Terminal conditions
    if depth == 0 or board.is_game_over():
        score = board_score_enhanced(board)
        # Only store deeper searches to avoid cache pollution
        if depth < max_depth - 1:
            enhanced_tt.store(board, score, depth, node_type='exact')
        return score, None
    
    # Move ordering - try TT move first, then captures, then others
    moves = get_ordered_moves_enhanced(board, tt_best_move)
    if not moves:
        return board_score_enhanced(board), None
    
    best_move = None
    original_alpha = alpha
    
    if maximizing_player:  # White to move
        max_score = -float('inf')
        
        for move in moves:
            # Make move
            board.push(move)
            
            # Recursive call
            score, _ = enhanced_minimax(board, depth - 1, alpha, beta, max_depth, False)
            
            # Undo move
            board.pop()
            
            if score > max_score:
                max_score = score
                best_move = move
            
            alpha = max(alpha, score)
            if beta <= alpha:
                break  # Alpha-beta pruning
        
        # Store in transposition table with proper node type
        node_type = 'exact'
        if max_score <= original_alpha:
            node_type = 'upper'
        elif max_score >= beta:
            node_type = 'lower'
        
        enhanced_tt.store(board, max_score, depth, best_move, node_type)
        return max_score, best_move
    
    else:  # Black to move
        min_score = float('inf')
        
        for move in moves:
            # Make move
            board.push(move)
            
            # Recursive call
            score, _ = enhanced_minimax(board, depth - 1, alpha, beta, max_depth, True)
            
            # Undo move
            board.pop()
            
            if score < min_score:
                min_score = score
                best_move = move
            
            beta = min(beta, score)
            if beta <= alpha:
                break  # Alpha-beta pruning
        
        # Store in transposition table with proper node type
        node_type = 'exact'
        if min_score <= original_alpha:
            node_type = 'upper'
        elif min_score >= beta:
            node_type = 'lower'
        
        enhanced_tt.store(board, min_score, depth, best_move, node_type)
        return min_score, best_move

def enhanced_best_move(board, save=False, load=False):
    """Enhanced best move using python-chess board"""
    global enhanced_tt
    
    if load:
        load_transposition_table()
    
    # Check opening book first
    cur_fen = board.fen()  
    player_moves = get_opening_move(cur_fen)
    
    if player_moves:
        # Try to convert opening book move to chess.Move
        try:
            # Assuming opening book moves are in UCI format
            move_str = player_moves[0]
            move = chess.Move.from_uci(move_str)
            if move in board.legal_moves:
                print(f"Using opening book move: {move}")
                return move
        except:
            print("Failed to parse opening book move, using search")
    
    print(f"Searching depth {MaxDepth}...")
    
    # Determine if we're maximizing (White to move)
    maximizing = board.turn == chess.WHITE
    
    # Use the enhanced minimax
    score, best_move = enhanced_minimax(
        board, MaxDepth, -float('inf'), float('inf'), MaxDepth, maximizing
    )
    
    print(enhanced_tt.get_stats())
    print(f"Best move score: {score}")
    
    if save:
        save_transposition_table()
    
    return best_move