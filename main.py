import argparse
from ERMiner import ERMiner


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="path to the file containing sequential database")
    parser.add_argument("support", help="minimal support threshold in float format, eg: 0.5",
                        type=float, default=0.5)
    parser.add_argument("confidence", help="minimal confidence threshold in float format, eg: 0.75",
                        type=float, default=0.75)
    args = parser.parse_args()
    print(f"> Starting ERMiner with min_sup={args.support} and min_con={args.confidence}...")
    erminer = ERMiner(args.filename, args.support, args.confidence)
    erminer.run()
