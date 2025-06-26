import chess.pgn
import pandas as pd
import os
def games_pgn():
    def load_pgn_games(pgn_dir_path):
        all_games=[]
        if not os.path.exists(pgn_dir_path):
            print("Error opening directory")
            return []
        for file in os.listdir(pgn_dir_path):
            games=[]
            file_path=os.path.join(pgn_dir_path,file)
            
            try:
                with open(file_path,encoding="utf-8") as pgnfile:
                    while True:
                        game=chess.pgn.read_game(pgnfile)
                        if not game:
                            break
                        
                        all_games.append(game)
            except UnicodeDecodeError:
                try:
                    with open(file_path,encoding="latin-1") as pgnfile:
                        while True:
                            game=chess.pgn.read_game(pgnfile)
                            if not game:
                                break
                            
                            all_games.append(game)
                except Exception as e:
                    print(f"Error loading file: {file} in latin-1 : {e}")
            except Exception as e:
                print(f"Error finding file {file} : {e}")
        return all_games
    
    pgn_games=load_pgn_games("latin-1")
    #print(carlsen_games[0])
    
    def convert_gamedata(game):
        board=game.board()
        game_data=[]
        for move in game.mainline_moves():
            game_data.append((board.fen(),move.uci()))
            board.push(move)
        return game_data
    
    training_data=[]
    for game in pgn_games:
        training_data.extend(convert_gamedata(game))
        
    #print(training_data[0])
    game_df=pd.DataFrame(training_data,columns=["fen","move"])
    game_df.to_csv("chess_training.csv",mode='a')
    return training_data

training_data=games_pgn()
opening_book={}
for fen,move in training_data:
    if fen not in opening_book:
        opening_book[fen]=[]
        
    opening_book[fen].append(move)
def get_opening_move(fen):
    return opening_book.get(fen,None)


def get_Fen(board):
    maherstr=""
    space_count=0
    for row in range(8):
        space_count=0
        for col in range(8):
            piece=board[row][col]
            if piece=="":
                space_count+=1
            else:
                if space_count>0:
                    maherstr+=str(space_count)
                    space_count=0
                maherstr+=(piece[1].lower() if piece[0]=='b' else piece[1])
        if space_count>0:
            maherstr+=str(space_count)
        if row<7:
            maherstr+='/'  
    print(maherstr)
    return maherstr  

    
        
