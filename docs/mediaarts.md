# メディア芸術データベース

## MCPツール

各ツールで `limit` は1〜50件、`start` は1から始まる取得位置です。次のページがある場合は、返された `next_start` を次回の `start` に指定します。`start` の上限は10001です。

### `search_manga_issues`

`query` に雑誌名の一部を指定します。必要に応じて `year`（西暦）、`volume_number`（巻）、`issue_number`（号）で絞り込みます。巻と号は文字列で完全一致します。号は誌面表記を優先し、誌面表記が未収録の場合はデータベースの号番号を使います。返された `issue_id` を `get_manga_issue_contents` に渡せます。

### `get_manga_issue_contents`

`issue_id` に `M` から始まる雑誌号IDを指定します。`start_page` はデータベースの表記のまま返します。目次が未収録の号では結果が空になることがあります。

### `search_works`

`query` にタイトルの一部、`medium` に `manga`、`anime`、`game` のいずれかを指定します。結果には作品・シリーズのID、タイトル、データベース上の分類、詳細ページが含まれます。

| `medium` | 検索対象 |
| --- | --- |
| `manga` | マンガ単行本シリーズ、マンガ雑誌の刊行物 |
| `anime` | TVレギュラー、TVスペシャル、劇場アニメのシリーズ |
| `game` | ゲーム作品 |

検索はデータベースのタイトル表記に対する部分一致です。巻、話、ゲームの機種別パッケージなどの個別資料は、詳細ページから確認してください。


## 出典と利用条件

コードはMIT Licenseです。メディア芸術データベースの公開SPARQLサービスを使用します。取得した情報の利用条件は配布元に従ってください。[公式SPARQL仕様](https://mediag.bunka.go.jp/madb_lab/lod/howto/) · [データセットとライセンス](https://github.com/mediaarts-db/dataset) · [MADB Lab 利用規約](https://mediag.bunka.go.jp/madb_lab/user_terms/)
