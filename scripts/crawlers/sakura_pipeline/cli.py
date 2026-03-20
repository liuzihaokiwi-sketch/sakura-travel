from __future__ import annotations
import argparse
from .providers.jma import fetch_and_parse_jma
from .providers.jmc import fetch_jmc
from .providers.weathernews import fetch_weathernews
from .providers.local_official import fetch_local_sites
from .fusion import build_all


def main():
    parser = argparse.ArgumentParser("sakura_pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("fetch-jma")
    p1.add_argument("--year", type=int, default=2026)

    sub.add_parser("fetch-jmc")
    sub.add_parser("fetch-weathernews")

    p4 = sub.add_parser("fetch-local")
    p4.add_argument("--config", required=True)

    p5 = sub.add_parser("fuse")
    p5.add_argument("--year", type=int, default=2026)

    args = parser.parse_args()

    if args.cmd == "fetch-jma":
        payload = fetch_and_parse_jma(year=args.year)
        print(f"Fetched JMA city truth for {args.year}: {len(payload['bloom'])} bloom rows")
    elif args.cmd == "fetch-jmc":
        fetch_jmc()
        print("Fetched JMC metadata")
    elif args.cmd == "fetch-weathernews":
        fetch_weathernews()
        print("Fetched Weathernews metadata")
    elif args.cmd == "fetch-local":
        payload = fetch_local_sites(config_path=args.config)
        print(f"Fetched local official sites: {len(payload['sites'])}")
    elif args.cmd == "fuse":
        build_all(year=args.year)
        print(f"Built fused output for {args.year}")


if __name__ == "__main__":
    main()
