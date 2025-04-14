import sqlite3
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from Board import Board
from evaluate import Parameters, score_position
import time
import random
from tqdm import tqdm

def get_conn(db_path=r"C:\Users\rafae\PycharmProjects\santoriniMediator\data\matches.db"):
    return sqlite3.connect(db_path)
def load_dataset():
    conn = get_conn()
    positions_df = pd.read_sql_query("SELECT position, match_id, move_count FROM TB_POSITIONS", conn)
    match_df = pd.read_sql_query("SELECT Id, Result FROM TB_MATCHES", conn)
    conn.close()
    match_results = dict(zip(match_df["Id"], match_df["Result"]))

    match_lengths = positions_df.groupby("match_id")["move_count"].max().to_dict()

    data = []
    for _, row in positions_df.iterrows():
        pos = row["position"]
        match_id = row["match_id"]
        move_count = row["move_count"]
        result = match_results.get(match_id, 0)
        if result == 0 or abs(result) >= 2:
            continue
        board = Board(pos)
        turn = board.turn
        match_len = match_lengths.get(match_id, 1)
        data.append((board, turn, result))
    return data

dataset = load_dataset()

def evaluate_entropy(centrality_gap, h2_gap, sh1, sh2, nh1, nh2):
    sigmoid_scale = 259.44  # from previous best fit
    params = Parameters(centrality_gap, h2_gap, sh1, sh2, nh1, nh2)
    scores = []
    labels = []
    for board, turn, result in dataset:
        score = score_position(board, params)
        if turn == -1:
            score = -score
        scaled_score = score * sigmoid_scale
        scores.append(scaled_score)
        labels.append(int(result == turn))

    X = np.array(scores).reshape(-1, 1)
    y = np.array(labels)

    model = LogisticRegression(solver="lbfgs", fit_intercept=False)
    model.fit(X, y)
    probs = model.predict_proba(X)[:, 1]
    return log_loss(y, probs)


import optuna

def objective(trial):
    centrality_gap = trial.suggest_int("centrality_gap", 0, 60, step=5)
    h2_gap = trial.suggest_int("h2_gap", 50, 600, step=5)
    sh1 = trial.suggest_int("sh1", -50, 250, step=5)
    sh2 = trial.suggest_int("sh2", -50, 250, step=5)
    nh1 = trial.suggest_int("nh1", -50, 250, step=5)
    nh2 = trial.suggest_int("nh2", -50, 250, step=5)

    # Your evaluate_entropy function returns the weighted log loss
    return evaluate_entropy(centrality_gap, h2_gap, sh1, sh2, nh1, nh2)

study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=10000)  # or however many you can afford

print("Best parameters:", study.best_params)
print("Best log loss:", study.best_value)
