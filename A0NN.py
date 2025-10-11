import tensorflow as tf
from tensorflow.keras import Model,layers
import numpy as np
import chess
from savingtsptables import enhanced_best_move,board_score_enhanced

def create_alpha0():
    input_layer=layers.Input(shape=(8,8,12))

    x=layers.Conv2D(64,3,padding='same',activation='relu')(input_layer)
    x=layers.Conv2D(64,3,padding='same',activation='relu')(x)


    x=layers.Flatten()(x)
    x=layers.Dense(256,activation='relu')(x)

    policy=layers.Dense(4672,activation='softmax',name='policy')(x)
    value=layers.Dense(1,activation='tanh',name='value')(x)

    model=Model(inputs=input_layer,outputs=[policy,value])

    model.compile(loss={
        'policy':'categorical_crossentropy',
        'value': 'mean_squared_error'},
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001)
        )
    return model

def board_to_tensor(board):
    piece_dict={
        'P':0,'N':1,'B':2,'R':3,'Q':4,'K':5
    }
    tensor=np.zeros((8,8,12))

    for square in chess.SQUARES:
        piece=board.piece_at(square)
        if piece:
            plane=piece_dict[(str(piece)).upper()]+(0 if piece.color==chess.WHITE else 6)
            row,col=divmod(square,8)
            tensor[row,col,plane]=1

    return tensor


class MCTS_NODE:
    def __init__(self,board,parent=None):
        self.board=board
        self.parent=parent
        self.children={}
        self.visits=0
        self.values=0
        self.mean_values=0
        self.prob=None

def mcts_search(model,board,num_simulations=100):
    root=MCTS_NODE(board)
    for i in range(0,num_simulations):
        node=root
        path=[node]

        while node.children:
            max_ucb=float('-inf')
            best_move=None
            for move,child in node.children.items():
                ucb=child.mean_values+1.41*child.prob*np.sqrt(node.visits)/(1+child.visits)
                if ucb>max_ucb:
                    max_ucb=ucb
                    best_move=move
            node=node.children[best_move]
            path.append(node)

        if not node.board.is_game_over():
            legal_moves=list(node.board.legal_moves)
            board_tensor=board_to_tensor(node.board)[None,...]
            policy,value=model.predict(board_tensor)
            policy=policy[0]
            value=value[0][0]

            for move in legal_moves:
                idx=move_to_idx(move)
                child_board=node.board.copy()
                child_board.push(move)
                
                child=MCTS_NODE(board=child_board,parent=node)
                child.prob=policy[idx]
                node.children[move]=child

        else:
            value=1 if node.board.result()=='1-0' else -1 if node.board.result()=='0-1' else 0

        for r_node in reversed(path):
            r_node.visits+=1
            r_node.values+=value
            r_node.mean_values=r_node.values/r_node.visits

            value=-value
    best_move=max(root.children.items(),key= lambda item:item[1].visits)[0]
    return best_move



def move_to_idx(move):
    return hash(move)%4672




