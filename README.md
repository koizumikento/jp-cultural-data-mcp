# jp-cultural-data-mcp

国立国会図書館、ジャパンサーチ、メディア芸術データベースの資料を調べるMCPサーバーです。MCP、CLI、Pythonライブラリから同じ機能を使えます。

[準備](#準備) · [MCP登録](#mcpクライアントに登録する) · [CLI](#cliで使う) · [Python](#pythonで使う) · [移行手順](docs/migration.md)

## 準備

Python 3.12以上、[uv](https://docs.astral.sh/uv/)、Gitが必要です。

```sh
git clone https://github.com/koizumikento/jp-cultural-data-mcp.git
cd jp-cultural-data-mcp
uv sync --locked
```

APIキーは不要です。

## MCPクライアントに登録する

設定例の `/absolute/path/to/jp-cultural-data-mcp` をクローン先の絶対パスに置き換えます。Windowsでは `C:/projects/jp-cultural-data-mcp` のように書けます。

### Codex

```sh
codex mcp add jp-cultural-data-mcp -- uv --directory "/absolute/path/to/jp-cultural-data-mcp" run --locked jp-cultural-data-mcp
codex mcp list
```

新しいセッションで `/mcp` を開いて接続状態を確認します。

### Claude Desktop / Cursor

Claude DesktopはOSに応じて次のファイルに設定します。

- Windowsは `%APPDATA%/Claude/claude_desktop_config.json`
- macOSは `~/Library/Application Support/Claude/claude_desktop_config.json`

Cursorはプロジェクト内の `.cursor/mcp.json` を使います。`mcpServers` に次の項目を追加し、クライアントを再起動してください。

```json
{
  "mcpServers": {
    "jp-cultural-data-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/jp-cultural-data-mcp",
        "run",
        "--locked",
        "jp-cultural-data-mcp"
      ]
    }
  }
}
```

`uv` が見つからない場合は、`command` に実行ファイルの絶対パスを指定してください。

## ツール

データごとの入力条件、結果、出典と利用条件は、表のリンク先に記載しています。

| ツール | データと操作の説明 |
| --- | --- |
| `search_bibliography` | [国立国会図書館](docs/ndl.md) |
| `get_digitized_pages` | [国立国会図書館](docs/ndl.md) |
| `search_items` | [ジャパンサーチ](docs/japan-search.md) |
| `get_item` | [ジャパンサーチ](docs/japan-search.md) |
| `search_collections` | [ジャパンサーチ](docs/japan-search.md) |
| `get_manga_issue_contents` | [メディア芸術データベース](docs/mediaarts.md) |
| `search_manga_issues` | [メディア芸術データベース](docs/mediaarts.md) |
| `search_works` | [メディア芸術データベース](docs/mediaarts.md) |

## CLIで使う

クローン先で実行します。取得結果はUTF-8のJSONとして標準出力に書き出します。

```sh
uv run jp-cultural-data-mcp ndl search-bibliography --title 源氏物語 --limit 3
uv run jp-cultural-data-mcp japan-search search-items --query モネ --limit 3
uv run jp-cultural-data-mcp mediaarts get-manga-issue-contents --query 週刊少年マガジン --limit 3
```

引数の説明は、各サブコマンドに `--help` を付けて確認できます。

## Pythonで使う

自分のPythonプロジェクトの依存関係に追加します。

```sh
uv add "git+https://github.com/koizumikento/jp-cultural-data-mcp.git@main"
```

次のコードを `example.py` に保存し、`uv run python example.py` で実行します。

```python
import asyncio

from jp_cultural_data_mcp import search_bibliography

result = asyncio.run(search_bibliography(title="源氏物語", limit=3))
print(result)
```

ツールと同じ名前の非同期関数を利用できます。すでにイベントループがある場合は、直接 `await` してください。

## 出典と利用条件

コードはMITライセンスです。データは実行時に各提供元から取得します。取得データには、データ別の説明に記載した提供元の利用条件が適用されます。

## 開発

```sh
uv sync --locked
uv run ruff check .
uv run ty check
uv run pytest
uv build
```
