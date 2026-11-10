# ジャパンサーチ

## ツール

| ツール | 用途 |
| --- | --- |
| `search_items` | キーワードで作品・資料を探し、連携元・利用条件・資料の種類で絞り込み |
| `get_item` | アイテムIDでメタデータを取得 |
| `search_collections` | 連携データベース、連携機関、ギャラリー、テーマ別検索を探す |

連携機関がAPI提供を許可した作品・資料メタデータが対象です。画像等の利用条件はアイテムの提供元で確認してください。

`search_items` の `database` を指定すると、ジャパンサーチで公開されているメタデータを連携元で絞り込めます。

| 指定値 | 対象 |
| --- | --- |
| `najda` | 国立公文書館デジタルアーカイブ |
| `syozo` | 国立美術館所蔵作品総合目録 |

データベースIDを省略すると横断検索になります。検索結果のIDは `get_item` で参照できます。[検索APIの仕様](https://jpsearch.go.jp/static/developer/webapi/ch3_search_api.html)・[連携データベース一覧](https://jpsearch.go.jp/stats)

`rights` と `item_type` は、それぞれ利用条件と資料の種類を絞るコードです。データベースIDと併用できます。利用条件のコードは、提供元が登録したコンテンツの条件を検索するためのものです。実際に使う場合はアイテムの提供元を確認してください。[絞り込みの仕様](https://jpsearch.go.jp/static/developer/webapi/ch5_facet_param.html) · [コード表](https://jpsearch.go.jp/static/developer/webapi/ch3_search_api.html)

| 引数 | 指定例 |
| --- | --- |
| `rights` | `cc0`（CC0）、`pdm`（パブリックドメイン・マーク）、`com`（商用利用） |
| `item_type` | `book`（図書）、`paint`（絵画）、`offdoc`（公文書） |

連携元や特集ページは `search_collections` で探します。`kind` に次の値を指定してください。

| 指定値 | 対象 |
| --- | --- |
| `database` | データベース |
| `organization` | 機関 |
| `gallery` | ギャラリー |
| `theme` | テーマ別検索 |

名前などで絞りたい場合は `query` を指定します。結果の `source_url` からジャパンサーチの紹介ページを開けます。`api_type` が `ok` のデータベースIDは、`search_items` の `database` に渡せます。


## 出典と利用条件

コードはMIT Licenseです。取得するデータの権利と利用条件は、API提供元と各データ提供機関の定めに従います。[公式API仕様](https://jpsearch.go.jp/static/developer/webapi/ch2_inquiry_api.html) · [利用案内](https://jpsearch.go.jp/static/developer/webapi/ch1_intro.html)


## 連携元を指定する例

Codexなどでは「国立公文書館の資料から『日本国憲法』を探して」と聞けます。

```sh
uv run japan-search-mcp search-items --database najda --query "日本国憲法" --limit 3
uv run japan-search-mcp search-items --database apmoa_mapps --query "浮世絵" --rights pdm --item-type paint --limit 3
```

Pythonでは `await search_items("モネ", database="syozo")` のように指定します。
