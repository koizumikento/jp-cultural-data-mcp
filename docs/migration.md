# 移行手順

## インストールと登録

同じPython環境に元のパッケージと統合パッケージを重ねてインストールすると、同名のモジュールやコマンドが競合します。
`ndl-search-mcp`、`japan-search-mcp`、`mediaarts-db-mcp` のうち依存関係に追加済みのものを、`uv remove パッケージ名` で外してください。その後、統合パッケージを追加します。

```sh
uv add "git+https://github.com/koizumikento/jp-cultural-data-mcp.git@main"
```

MCPクライアントでは `jp-cultural-data-mcp` を登録します。登録方法は[README](../README.md#mcpクライアントに登録する)を参照してください。

Codexでは `codex mcp list` で元の登録名を確認し、`codex mcp remove 登録名` で削除してから新しい登録に切り替えます。Claude Desktop・Cursorでは `mcpServers` の元の項目を、READMEの設定例に置き換えてください。

## CLIとPython

このパッケージには次のコマンドとPythonモジュールが含まれます。既存の引数と公開関数を使えます。

| コマンド | Pythonモジュール | 新しいCLIの指定 |
| --- | --- | --- |
| `ndl-search-mcp` | `ndl_search_mcp` | `jp-cultural-data-mcp ndl ...` |
| `japan-search-mcp` | `japan_search_mcp` | `jp-cultural-data-mcp japan-search ...` |
| `mediaarts-db-mcp` | `mediaarts_db_mcp` | `jp-cultural-data-mcp mediaarts ...` |

Pythonでは統合パッケージからも関数をインポートできます。データの出典、ページ送り、キャッシュ、認証情報の設定は各データの説明を確認してください。
