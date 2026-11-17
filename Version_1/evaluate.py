import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.evaluation.evaluate import *

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Retrieval eval")
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--expand", action="store_true")
    args = parser.parse_args()
    run(top_k=args.top_k, expand=args.expand)
