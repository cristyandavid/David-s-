"""
smart-contract-generator CLI

Usage:
    python cli.py --type erc20 --name MyToken --symbol MTK
"""

import argparse
import sys

from src.generator import generate, SUPPORTED_TYPES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smart-contract-generator",
        description="Generate smart contract scaffolds from the command line.",
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=SUPPORTED_TYPES,
        metavar="TYPE",
        help=f"Contract type. Options: {', '.join(SUPPORTED_TYPES)}",
    )
    parser.add_argument("--name", default="MyContract", help="Contract name")
    parser.add_argument("--symbol", default="", help="Token symbol (erc20/erc721)")
    parser.add_argument("--owner", default="", help="Owner address (multisig)")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    params = {
        "name": args.name,
        "symbol": args.symbol,
        "owner": args.owner,
    }

    try:
        output = generate(args.type, params)
        print(output)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
