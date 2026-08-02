# 未来の技術者必修! 生成AI活用とAI駆動開発の基礎を1.5日で完全習得

生成AI利活用ワークショップ (2026年8月・お茶の水女子大学) の講義資料です。
ANEC (国際原子力人材育成) 事業の一環として実施する 1.5日集中ワークショップで、
原子力・エネルギー系を中心とした理系の学部生・大学院生を対象に、
生成AIの基礎から AI駆動開発の実践までをハンズオン中心で扱います。

## ワークショップの概要

- 対象: 理系の学部4年生・大学院生 (Python は入門書レベル、生成AIは利用経験あり)
- 形式: 1.5日 (1日目 10:00〜18:00、2日目 9:00〜12:00)。講義 + ハンズオン
- ゴール: 「仕様書を書く → AI に生成させる → 検証する → コミットする」という
  AI駆動開発のサイクルを一人で回せるようになり、自作アプリを GitHub に push して
  ライトニングトークで発表する
- 使用ツール: Google AI Studio ／ uv ／ VS Code + GitHub Copilot ／ Git + GitHub

## 資料構成 (pdfs/)

| ファイル | パート | 内容 | 時間 |
|---|---|---|---|
| [part1.pdf](pdfs/part1.pdf) | Part 1 | イントロダクション — 1.5日の地図とマインドセット | 1日目 10:00〜10:30 |
| [part2.pdf](pdfs/part2.pdf) | Part 2 | 生成AIの衝撃 2026 — 原理・到達点・責任 | 1日目 10:30〜11:30 |
| [part3.pdf](pdfs/part3.pdf) | Part 3 | AI駆動開発の体験 — プロンプト設計と Google AI Studio Build | 1日目 12:30〜14:00 |
| [part4.pdf](pdfs/part4.pdf) | Part 4 | AI駆動開発の環境整備 — Git・uv・VS Code + Copilot | 1日目 14:15〜16:15 |
| [part5.pdf](pdfs/part5.pdf) | Part 5 | 開発実践 — 仕様書から動くアプリまで | 1日目 16:30〜18:00 + 2日目 9:00〜10:45 |
| [part6.pdf](pdfs/part6.pdf) | Part 6 | ライトニングトーク大会 + まとめ | 2日目 11:00〜12:00 |

## Pythonサンプルプログラム

AI駆動開発とuvを体験する3つの独立プロジェクトを [`samples/`](samples/) に収録して
います。すべて有料APIなしで動作します。

| サンプル | 内容 |
|---|---|
| [Evolving Game](samples/01_evolving_game/) | 参加者の要望をその場で追加して進化させるブロック崩し |
| [Spaceship Debug](samples/02_spaceship_debug/) | 失敗するテストから宇宙船制御ソフトのバグを調査・修正する演習 |
| [Gesture Arena](samples/03_gesture_arena/) | 手のジェスチャーで操作するローカル画像認識ゲーム |

基本的な実行方法は共通です。

```bash
cd samples/01_evolving_game
uv sync
uv run python main.py
```

各サンプルの操作、テスト、AIへの依頼例は、それぞれのREADMEを参照してください。

## 参加者向けの事前準備

当日の実習をスムーズに実施できるように、以下を事前に済ませてください:

1. Google アカウント (18歳以上) を用意し、[Google AI Studio](https://aistudio.google.com) にログインできることを確認する
2. GitHub アカウントを作成し、Student Developer Pack (GitHub Copilot) を有効化する

## 備考

- スライドは 2026年7〜8月時点のツール仕様 (uv 0.12、Google AI Studio、VS Code +
  Copilot) に基づいています。各ツールの UI・仕様は変わる可能性があります
- 本教材のスライドは、AI駆動開発の実践例として、生成AI (LLM + 画像生成) を
  活用して制作しています

## 講師

巽 雅洋 (たつみ まさひろ) — 株式会社原子力エンジニアリング 解析サービス本部
システム技術グループ 主幹技師長、博士(工学)
