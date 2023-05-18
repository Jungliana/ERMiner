import argparse
from ERMiner import ERMiner


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="path to the file containing sequential database")
    parser.add_argument("support", help="minimal support threshold in float format, eg: 0.5",
                        type=float, default=0.5)
    parser.add_argument("confidence", help="minimal confidence threshold in float format, eg: 0.75",
                        type=float, default=0.75)
    parser.add_argument("-v", "--verbose", help="print detected rules",
                        action="store_true")
    parser.add_argument("-w", "--write", help="write rules to `output.txt` file",
                        action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    print(f"> Starting ERMiner with min_sup={args.support} and min_con={args.confidence}...")
    erminer = ERMiner(args.filename, args.support, args.confidence)
    erminer.run(printing=args.verbose, out_file=args.write)
