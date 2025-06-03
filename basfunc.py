from var import *

king_cache={'w':None,'b':None}

def update_king_cache():
    global king_cache
    king_cache = {'w': None, 'b': None}
    for rank in range(ROWS):
        for file in range(COLS):
            piece=game_state.board[rank][file]
            if piece and piece[1]=='K':
                king_cache[piece[0]]=(rank,file)

def get_king_pos(color):
    if king_cache[color] is None:
        update_king_cache()
    return king_cache[color]

def is_square_attacked(rank,file,color):
    pawn_direction= 1 if color=='w' else -1
    pawn_rank=rank-pawn_direction
    
    if 0<=pawn_rank<ROWS:
        for pawn_file in [file-1,file+1]:
            if 0<=pawn_file<COLS:
                piece=game_state.board[pawn_rank][pawn_file]
                if piece==color+'P':
                    return True
    
    knight_moves=[(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]
    for dr,df in knight_moves:
        r=rank+dr
        f=file+df
        if 0<=r<ROWS and 0<=f<COLS:
            piece=game_state.board[r][f]
            if piece and piece==color+'N':
                return True
            
    directions={
        'R': [(1,0),(-1,0),(0,1),(0,-1)],
        'B': [(1,1),(1,-1),(-1,1),(-1,-1)],
        'Q': [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    }
    
    for piece_type,directs in directions.items():
        for dr,df in directs:
            for squares in range(1,8):
                r=rank+dr*squares
                f=file+df*squares
                if 0<=r<ROWS and 0<=f<COLS:
                    piece=game_state.board[r][f]
                    if piece:
                        if piece==color+piece_type:
                            return True
                        break
                else:
                    break
    
    king_moves=[(-1,-1),(-1,0),(-1,1),(1,1),(1,0),(1,-1),(0,1),(0,-1)]
    
    for dr,df in king_moves:
        r=rank+dr
        f=file+df
        if 0<=r<ROWS and 0<=f<COLS:
            piece=game_state.board[r][f]
            if piece and piece==color+'K':
                return True
    
    return False

def is_king_in_check(color):
    king_pos=get_king_pos(color)
    if not king_pos:
        return False
    opp_color='w' if color=='b' else 'b'
    return is_square_attacked(king_pos[0],king_pos[1],opp_color)

# Optimized version from paste
def is_king_in_check_fast(color):
    """Optimized check detection"""
    # Find king position
    king_pos = get_king_pos(color)
    if not king_pos:
        return False
    
    kr, kf = king_pos
    opp_color = 'b' if color == 'w' else 'w'
    
    # Check for pawn attacks (most common)
    pawn_dir = 1 if color == 'w' else -1
    pawn_rank = kr - pawn_dir
    if 0 <= pawn_rank < ROWS:
        for pf in [kf-1, kf+1]:
            if 0 <= pf < COLS and game_state.board[pawn_rank][pf] == opp_color + 'P':
                return True
    
    # Check knight attacks
    knight_moves = [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]
    for dr, df in knight_moves:
        r, f = kr + dr, kf + df
        if 0 <= r < ROWS and 0 <= f < COLS:
            if game_state.board[r][f] == opp_color + 'N':
                return True
    
    # Check sliding pieces (rook, bishop, queen)
    directions = [
        (1,0), (-1,0), (0,1), (0,-1),  # Rook directions
        (1,1), (1,-1), (-1,1), (-1,-1)  # Bishop directions
    ]
    
    for dr, df in directions:
        for dist in range(1, 8):
            r, f = kr + dr*dist, kf + df*dist
            if not (0 <= r < ROWS and 0 <= f < COLS):
                break
            
            piece = game_state.board[r][f]
            if piece:
                if piece[0] == opp_color:
                    # Check if this piece can attack along this direction
                    if ((dr == 0 or df == 0) and piece[1] in ['R', 'Q']) or \
                       ((dr != 0 and df != 0) and piece[1] in ['B', 'Q']):
                        return True
                break
    
    # Check king attacks
    for dr in [-1, 0, 1]:
        for df in [-1, 0, 1]:
            if dr == 0 and df == 0:
                continue
            r, f = kr + dr, kf + df
            if 0 <= r < ROWS and 0 <= f < COLS:
                if game_state.board[r][f] == opp_color + 'K':
                    return True
    
    return False

move_history=[]

def make_move(from_p,to_p,piece):
    from_r,from_f=from_p
    to_r,to_f=to_p
    
    captured=game_state.board[to_r][to_f]
    
    move_info={
        'from_p':from_p,
        'to_p': to_p,
        'piece':piece,
        'captured':captured,
        'king_cache':king_cache.copy()
        }
    
    game_state.board[to_r][to_f]=piece
    game_state.board[from_r][from_f]=""
    
    if piece[1]=='K':
        king_cache[piece[0]]=to_p
        
    move_history.append(move_info)
    return move_info
    
def undo_move(move_info):
    from_r,from_f=move_info['from_p']
    to_r,to_f=move_info['to_p']
    
    game_state.board[from_r][from_f]=move_info['piece']
    game_state.board[to_r][to_f]=move_info['captured']
    
    global king_cache
    king_cache=move_info['king_cache']
    
    move_history.pop()
    return

def order_moves(color):
    captures=[]
    nishe=[]
    
    for rank in range(ROWS):
        for file in range(COLS):
            piece=game_state.board[rank][file]
            if piece and piece[0]==color:
                moves=get_legal_moves(piece, rank, file)
                
                for to_r,to_f in moves:
                    move_info2=((rank,file),(to_r,to_f),piece)
                    
                    if game_state.board[to_r][to_f]:
                        captures.append(move_info2)
                    else:
                        nishe.append(move_info2)
                        
    return captures+nishe

# Optimized move ordering from paste
def order_moves_aggressive(color):
    """Order moves for maximum alpha-beta efficiency"""
    captures_high = []  # High-value captures
    captures_low = []   # Low-value captures
    checks = []         # Moves that give check
    others = []         # Other moves
    
    capture_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    for rank in range(ROWS):
        for file in range(COLS):
            piece = game_state.board[rank][file]
            if piece and piece[0] == color:
                moves = get_potential_moves(piece, rank, file)
                
                for to_r, to_f in moves:
                    move_tuple = ((rank, file), (to_r, to_f), piece)
                    target = game_state.board[to_r][to_f]
                    
                    if target:  # Capture
                        target_value = capture_values.get(target[1], 0)
                        attacker_value = capture_values.get(piece[1], 0)
                        
                        # Good captures (win material or equal trades)
                        if target_value >= attacker_value:
                            captures_high.append(move_tuple)
                        else:
                            captures_low.append(move_tuple)
                    else:
                        others.append(move_tuple)
    
    # Return in order of likely best moves first
    return captures_high + captures_low + others

# Fast pseudo-legal move generation (no legality checking)
def get_pseudo_legal_moves_fast(color):
    """Generate all pseudo-legal moves without expensive legality checks"""
    moves = []
    
    for rank in range(ROWS):
        for file in range(COLS):
            piece = game_state.board[rank][file]
            if piece and piece[0] == color:
                piece_moves = get_potential_moves(piece, rank, file)
                for to_r, to_f in piece_moves:
                    moves.append(((rank, file), (to_r, to_f), piece))
    
    return moves

def can_castle_kingside(color):
    if color == 'w':
        king_start = (7,4)
        rook_start = (7,7)
        rank = 7
    else:
        king_start = (0,4)
        rook_start = (0,7)
        rank = 0

    if game_state.piece_has_moved.get(king_start, False):
        return False
    if game_state.piece_has_moved.get(rook_start, False):
        return False

    if game_state.board[rank][5] != "" or game_state.board[rank][6] != "":
        return False

    if is_king_in_check(color):
        return False
    
    if is_square_attacked(rank, 5, 'b' if color == 'w' else 'w'):
        return False
    if is_square_attacked(rank, 6, 'b' if color == 'w' else 'w'):
        return False

    return True

def can_castle_queenside(color):
    if color == 'w':
        king_start = (7,4)
        rook_start = (7,0)
        rank = 7
    else:
        king_start = (0,4)
        rook_start = (0,0)
        rank = 0

    if game_state.piece_has_moved.get(king_start, False):
        return False
    if game_state.piece_has_moved.get(rook_start, False):
        return False

    if (game_state.board[rank][1] != "" or
        game_state.board[rank][2] != "" or
        game_state.board[rank][3] != ""):
        return False

    if is_king_in_check(color):
       return False
   
    if is_square_attacked(rank, 2, 'b' if color == 'w' else 'w'):
        return False
    if is_square_attacked(rank, 3, 'b' if color == 'w' else 'w'):
        return False

    return True

def get_potential_moves(piece, rank, file):
    moves = []
    if not piece:
        return moves
    color = piece[0]
    opponent = 'b' if color == 'w' else 'w'

    if piece[1] == "P":
        direction = -1 if color == 'w' else 1
        start_row = 6 if color == 'w' else 1
        # single step
        if is_valid_position(rank+direction,file) and game_state.board[rank+direction][file] == "":
            moves.append((rank+direction, file))
            # double step
            if rank == start_row and game_state.board[rank+2*direction][file] == "":
                moves.append((rank+2*direction, file))
        # diagonal captures
        for dx in [-1,1]:
            r_cap = rank+direction
            f_cap = file+dx
            if is_valid_position(r_cap,f_cap):
                target = game_state.board[r_cap][f_cap]
                if target and target[0] == opponent:
                    moves.append((r_cap,f_cap))

    elif piece[1] == "R":
        moves.extend(generate_moves_in_directions(rank,file,[(1,0),(-1,0),(0,1),(0,-1)]))

    elif piece[1] == "B":
        moves.extend(generate_moves_in_directions(rank,file,[(1,1),(1,-1),(-1,1),(-1,-1)]))

    elif piece[1] == "Q":
        moves.extend(generate_moves_in_directions(rank,file,[
            (1,0),(-1,0),(0,1),(0,-1),
            (1,1),(1,-1),(-1,1),(-1,-1)
        ]))

    elif piece[1] == "N":
        knight_moves = [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]
        for (dr,df) in knight_moves:
            rr = rank+dr
            ff = file+df
            if is_valid_position(rr,ff):
                if game_state.board[rr][ff] == "" or game_state.board[rr][ff][0] == opponent:
                    moves.append((rr,ff))

    elif piece[1] == "K":
        king_moves = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
        for (dr,df) in king_moves:
            rr=rank+dr
            ff=file+df
            if is_valid_position(rr,ff):
                if game_state.board[rr][ff]=="" or game_state.board[rr][ff][0]==opponent:
                    moves.append((rr,ff))

        # castling squares
        if color=='w' and rank==7 and file==4:
            if can_castle_kingside('w'):
                moves.append((7,6))
            if can_castle_queenside('w'):
                moves.append((7,2))
        if color=='b' and rank==0 and file==4:
            if can_castle_kingside('b'):
                moves.append((0,6))
            if can_castle_queenside('b'):
                moves.append((0,2))

    return moves

def get_legal_moves(piece, rank, file):
    naive_moves = get_potential_moves(piece, rank, file)
    color = piece[0]
    legal = []
    for (r,f) in naive_moves:
        move=make_move((rank,file),(r,f),piece)

        if not is_king_in_check(color):
            legal.append((r,f))

        undo_move(move)
    return legal

def promote_pawn(rank, file):
    piece = game_state.board[rank][file]
    if piece and piece[1]=='P' and (rank==0 or rank==7):
        game_state.board[rank][file] = piece[0]+'Q'

def check_game_end():
    if is_king_in_check(game_state.current_turn):
        moves_exist = False
        for r in range(ROWS):
            for c in range(COLS):
                piece = game_state.board[r][c]
                if piece and piece[0] == game_state.current_turn:
                    if get_legal_moves(piece, r, c):
                        moves_exist = True
                        break
            if moves_exist:
                break
        if not moves_exist:
            game_state.winner = 'White' if game_state.current_turn=='b' else 'Black'
            print(f'Checkmate! {game_state.winner} wins!')
            game_state.game_over = True
        else:
            print(f'{game_state.current_turn} is in check!')

def is_valid_position(rank, file):
    return 0 <= rank < ROWS and 0 <= file < COLS

def generate_moves_in_directions(rank, file, directions, max_steps=8):
    moves = []
    curpiece = game_state.board[rank][file]
    if not curpiece:
        return moves
    color = curpiece[0]
    for dr, df in directions:
        for step in range(1, max_steps+1):
            r, f = rank + dr*step, file + df*step
            if not is_valid_position(r, f):
                break
            if game_state.board[r][f] == "":
                moves.append((r, f))
            elif game_state.board[r][f][0] != color:
                moves.append((r, f))
                break
            else:
                break
    return moves