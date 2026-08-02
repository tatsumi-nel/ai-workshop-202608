# Pythonサンプルプログラム

各フォルダは独立したuvプロジェクトです。試したいフォルダへ移動し、同じ2コマンドで
環境構築と実行ができます。

```bash
uv sync
uv run python main.py
```

| サンプル | 学ぶこと | 通常のテスト結果 |
|---|---|---|
| [01_evolving_game](01_evolving_game/) | AIによる機能追加、ロジックと表示の分離 | すべて成功 |
| [02_spaceship_debug](02_spaceship_debug/) | テストを手掛かりにした原因調査と修正 | 9件失敗（教材仕様） |
| [03_gesture_arena](03_gesture_arena/) | カメラ、画像認識、ゲームの技術統合 | すべて成功 |

詳細な操作方法とAIへの依頼例は、各フォルダのREADMEを参照してください。

## uvで観察するポイント

初回の `uv sync` の前後で、フォルダの内容を比較します。

- `.python-version`: 使用するPythonの系列
- `pyproject.toml`: 直接利用する依存パッケージ
- `uv.lock`: 間接依存を含む、解決済みの正確なバージョン
- `.venv/`: `uv sync` がローカルに作る実行環境（Git管理外）

`uv.lock` はGitへコミットします。参加者が依存関係を追加するときは、例えば
`uv add package-name` を使います。

