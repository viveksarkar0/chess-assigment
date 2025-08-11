#!/usr/bin/env python3
import os, sys, json
import chess, chess.engine, chess.pgn

ENGINE_TIME = 0.12  # per-position engine time
PIECE_VALUE = {chess.KING:1000, chess.QUEEN:9, chess.ROOK:5, chess.BISHOP:3, chess.KNIGHT:3, chess.PAWN:1}
DELTAS = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]

# helpers
def sq_file(sq): return chess.square_file(sq)
def sq_rank(sq): return chess.square_rank(sq)

def squares_between(sq1, sq2):
    """List squares strictly between sq1 and sq2 (collinear), else []"""
    x1,y1 = sq_file(sq1), sq_rank(sq1)
    x2,y2 = sq_file(sq2), sq_rank(sq2)
    dx,dy = x2-x1, y2-y1
    if not (dx==0 or dy==0 or abs(dx)==abs(dy)): return []
    sx = (dx>0) - (dx<0); sy = (dy>0) - (dy<0)
    x,y = x1+sx, y1+sy
    out = []
    while (x,y) != (x2,y2):
        out.append(chess.square(x,y))
        x += sx; y += sy
    return out

def detect_pins(board):
    events = []
    king_white = board.king(chess.WHITE)
    king_black = board.king(chess.BLACK)
    sliders = list(board.pieces(chess.BISHOP, chess.WHITE)|board.pieces(chess.ROOK, chess.WHITE)|board.pieces(chess.QUEEN, chess.WHITE)) + \
              list(board.pieces(chess.BISHOP, chess.BLACK)|board.pieces(chess.ROOK, chess.BLACK)|board.pieces(chess.QUEEN, chess.BLACK))
    for attacker_sq in sliders:
        attacker = board.piece_at(attacker_sq)
        if not attacker: continue
        target_king = king_black if attacker.color==chess.WHITE else king_white
        if target_king is None: continue
        between = squares_between(attacker_sq, target_king)
        occupied_between = [sq for sq in between if board.piece_at(sq)]
        if len(occupied_between) == 1:
            pinned_sq = occupied_between[0]
            pinned_piece = board.piece_at(pinned_sq)
            if pinned_piece and pinned_piece.color != attacker.color:
                dx = sq_file(target_king)-sq_file(attacker_sq)
                dy = sq_rank(target_king)-sq_rank(attacker_sq)
                if dx==0 or dy==0:
                    if attacker.piece_type in (chess.ROOK, chess.QUEEN):
                        events.append({"pinner_sq":attacker_sq,"pinned_sq":pinned_sq,"pinner_color":attacker.color,"pinned_color":pinned_piece.color})
                elif abs(dx)==abs(dy):
                    if attacker.piece_type in (chess.BISHOP, chess.QUEEN):
                        events.append({"pinner_sq":attacker_sq,"pinned_sq":pinned_sq,"pinner_color":attacker.color,"pinned_color":pinned_piece.color})
    return events

def detect_skewers(board):
    events = []
    sliders = list(board.pieces(chess.BISHOP, chess.WHITE)|board.pieces(chess.ROOK, chess.WHITE)|board.pieces(chess.QUEEN, chess.WHITE)) + \
              list(board.pieces(chess.BISHOP, chess.BLACK)|board.pieces(chess.ROOK, chess.BLACK)|board.pieces(chess.QUEEN, chess.BLACK))
    for a in sliders:
        attacker = board.piece_at(a)
        if not attacker: continue
        fx,fy = sq_file(a), sq_rank(a)
        for dx,dy in DELTAS:
            x,y = fx+dx, fy+dy
            first = None
            while 0 <= x < 8 and 0 <= y < 8:
                s = chess.square(x,y)
                p = board.piece_at(s)
                if p:
                    if first is None:
                        if p.color == attacker.color:
                            break
                        first = (s,p)
                        x += dx; y += dy
                        continue
                    else:
                        if p.color == first[1].color and p.color != attacker.color:
                            if PIECE_VALUE[first[1].piece_type] > PIECE_VALUE[p.piece_type]:
                                events.append({"attacker_sq":a,"victim_sq":first[0],"behind_sq":s,"attacker_color":attacker.color})
                        break
                x += dx; y += dy
    seen = set()
    uniq = []
    for e in events:
        key = (e["attacker_sq"],e["victim_sq"],e["behind_sq"])
        if key not in seen:
            seen.add(key); uniq.append(e)
    return uniq

def get_best_move(engine, board):
    try:
        res = engine.play(board, chess.engine.Limit(time=ENGINE_TIME))
        return res.move
    except Exception:
        return None

def key_for_pin(p): return (p["pinner_sq"], p["pinned_sq"])
def key_for_skewer(s): return (s["attacker_sq"], s["victim_sq"], s["behind_sq"])

def classify_game(game, engine):
    board = game.board()
    out = {"executed": [], "missed": [], "allowed": []}
    ply = 0
    for move in game.mainline_moves():
        ply += 1
        player_color = board.turn

        pins_before = detect_pins(board)
        skew_before = detect_skewers(board)
        pin_keys_before = set(key_for_pin(p) for p in pins_before)
        skewer_keys_before = set(key_for_skewer(s) for s in skew_before)

        best = get_best_move(engine, board)
        if best and best != move:
            tb = board.copy()
            try:
                tb.push(best)
                pb = [p for p in detect_pins(tb) if p["pinner_color"] == player_color]
                sb = [s for s in detect_skewers(tb) if s["attacker_color"] == player_color]
                for p in pb:
                    if key_for_pin(p) not in pin_keys_before:
                        out["missed"].append({"ply":ply,"tactic":"pin","pinner":chess.square_name(p["pinner_sq"]), "pinned":chess.square_name(p["pinned_sq"])} )
                for s in sb:
                    if key_for_skewer(s) not in skewer_keys_before:
                        out["missed"].append({"ply":ply,"tactic":"skewer","attacker":chess.square_name(s["attacker_sq"])})
            except Exception:
                pass

        b_after_play = board.copy()
        b_after_play.push(move)
        pb_after = [p for p in detect_pins(b_after_play) if p["pinner_color"] == player_color]
        sb_after = [s for s in detect_skewers(b_after_play) if s["attacker_color"] == player_color]
        for p in pb_after:
            if key_for_pin(p) not in pin_keys_before:
                out["executed"].append({"ply":ply,"tactic":"pin","pinner":chess.square_name(p["pinner_sq"]), "pinned":chess.square_name(p["pinned_sq"])} )
        for s in sb_after:
            if key_for_skewer(s) not in skewer_keys_before:
                out["executed"].append({"ply":ply,"tactic":"skewer","attacker":chess.square_name(s["attacker_sq"])})

        board.push(move)

        best_resp = get_best_move(engine, board)
        if best_resp:
            tb = board.copy()
            try:
                tb.push(best_resp)
                pb = [p for p in detect_pins(tb) if p["pinner_color"] != player_color]
                sb = [s for s in detect_skewers(tb) if s["attacker_color"] != player_color]
                for p in pb:
                    out["allowed"].append({"ply":ply,"tactic":"pin","pinner":chess.square_name(p["pinner_sq"])} )
                for s in sb:
                    out["allowed"].append({"ply":ply,"tactic":"skewer","attacker":chess.square_name(s["attacker_sq"])})
            except Exception:
                pass

    return out

def load_games_from_file(pgn_path):
    games = []
    with open(pgn_path) as f:
        while True:
            game = chess.pgn.read_game(f)
            if not game: break
            games.append(game)
    return games

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <pgn_file> <stockfish_path>")
        sys.exit(1)

    pgn_file = sys.argv[1]
    stockfish_path = sys.argv[2]

    if not os.path.exists(pgn_file):
        print("Missing PGN file.")
        sys.exit(1)
    if not os.path.exists(stockfish_path):
        print("Missing Stockfish binary.")
        sys.exit(1)

    games = load_games_from_file(pgn_file)

    results = {}
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        for i, game in enumerate(games[:5], start=1):
            print(f"Analyzing game {i} ...")
            results[f"game_{i}"] = classify_game(game, engine)
            s = results[f"game_{i}"]
            print(f" Game {i}: Executed {len(s['executed'])}, Missed {len(s['missed'])}, Allowed {len(s['allowed'])}")

    with open("pins_skewers_results.json","w") as f:
        json.dump(results, f, indent=2)
    print("Saved pins_skewers_results.json")

if __name__ == "__main__":
    main()
