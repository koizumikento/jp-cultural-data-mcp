# 国立国会図書館

## ツール

| ツール | 用途 |
| --- | --- |
| `search_bibliography` | タイトル・著者・ISBNで書誌を検索し、デジタル資料のPIDも返す |
| `get_digitized_pages` | デジタルコレクションの公開資料のページリンクを取得 |

OpenSearchで公開されている書誌メタデータを検索します。利用目的と提供元に応じて申請や許諾が必要な場合があります。

`isbn` にはISBN-10またはISBN-13を指定します。ハイフンや空白は省略できます。

各検索結果の `digitized_pids` には、書誌データが参照しているデジタルコレクションのPIDが入ります。PIDがある場合は `get_digitized_pages` に渡せます。PIDがあっても公開IIIFマニフェストの有無は資料によります。

デジタルコレクションの資料ページが `https://dl.ndl.go.jp/pid/3048007` なら、`pid` は `3048007` です。1回に1〜100ページを指定できます。続きがあれば `next_start` を返します。取得するのはページのリンクと資料情報です。公開範囲や画像の利用条件は資料ごとに異なります。


## 出典と利用条件

コードはMIT Licenseです。取得するデータの権利と利用条件は、API提供元と各データ提供機関の定めに従います。[公式API仕様](https://ndlsearch.ndl.go.jp/help/api/specifications) · [NDLサーチの利用案内](https://ndlsearch.ndl.go.jp/help/api) · [IIIF仕様](https://dl.ndl.go.jp/static/files/IIIF_interface_Jp.pdf) · [デジタルコレクションのIIIF利用案内](https://dl.ndl.go.jp/ja/help_iiif)
