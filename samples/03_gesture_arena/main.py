"""別プロセス起動時にPygameを読み込まないための軽量エントリーポイント。"""


def main() -> None:
    from arena import main as run_game

    run_game()


if __name__ == "__main__":
    main()
