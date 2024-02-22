


def arguments() -> argparse:
    logger.info("Retrieving arguments")
    parser = argparse.ArgumentParser(
        description="Retreive block reward payments from SapceFarmers.com api and write to csv"
    )
    parser.add_argument("-l", help="launcher_id", type=str)
    parser.add_argument("-a", help="retieve all payments from api", action="store_true")
    parser.add_argument("-u", help="update payments from api", action="store_true")
    parser.add_argument("-w", help="weekly earning report", action="store_true")
    parser.add_argument("-d", help="daily earning report", action="store_true")
    parser.add_argument(
        "-p", help="space farmer normal payout report", action="store_true"
    )
    args = parser.parse_args()

    if args.u and args.a:
        text = (
            "Can't both update payments and retrieve all payments please pick only one."
        )
        logger.warning(text)
        sys.exit(text)

    if not args.u and not args.a and not args.w and not args.d and not args.p:
        text = "need to either update payments or retrieve all payments please pick only one."
        logger.warning(text)
        sys.exit(text)

    return args


def main() -> None:
    logger.info("starting main")
    # args = arguments()
    
    #ap = APIHandler(synced=1708368372)
    a = APIHandler()
    a.blocks(sync_d=1708368372)
    fm = FileManager()
    data = fm.read_all_transactions()
    print(data)
    
if __name__ == "__main__":
    main()
