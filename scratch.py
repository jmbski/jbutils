import argparse

parser = argparse.ArgumentParser(description="test parser")
parser.add_argument("--test", "-t", type=int, action="append", help="num list")

args = parser.parse_args()

print("args:", args)
