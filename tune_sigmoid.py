import sqlite3
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from Board import Board
from evaluate import Parameters, score_position
import time

start_time = time.perf_counter()

def get_conn(db_path=r"C:\Users\rafae\PycharmProjects\santoriniMediator\data\matches.db"):
    return sqlite3.connect(db_path)

# Load all labeled positions
conn = get_conn()
query = "SELECT position, match_id, move_count FROM TB_POSITIONS"
positions_df = pd.read_sql_query(query, conn)
match_df = pd.read_sql_query("SELECT Id, Result FROM TB_MATCHES", conn)
conn.close()

match_results = dict(zip(match_df["Id"], match_df["Result"]))

params = Parameters(20, 300, 30, 55, 35, 85)

scores = []
labels = []

for _, row in positions_df.iterrows():
    pos = row["position"]
    match_id = row["match_id"]

    result = match_results.get(match_id, 0)
    if result == 0 or abs(result) >= 2:
        continue

    board = Board(pos)
    turn = board.turn
    score = score_position(board, params)
    if turn == -1:
        score = -score

    correct = (result == turn)
    scores.append(score)
    labels.append(int(correct))

X = np.array(scores).reshape(-1, 1)
y = np.array(labels)

model = LogisticRegression(solver="lbfgs", fit_intercept=False)
model.fit(X, y)

scale = 1 / model.coef_[0][0]
print(f"Best sigmoid scale ≈ {scale:.2f}")

probs = model.predict_proba(X)[:, 1]
entropy = log_loss(y, probs)
print(f"Average entropy (log loss): {entropy:.4f}")

end_time = time.perf_counter()
print(f"Execution time: {end_time - start_time:.2f} seconds")
