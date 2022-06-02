# 開発環境
Python: 3.8.6

# 必要事項
- requirement.txtに記載のライブラリをpip installする
- 環境変数PYTHONPATHにlibディレクトリを追加する
- resourceディレクトリのtmp.ymlと、tasksディレクトリの試験ファイルを参考に試験用パラメータを作成する

# 実行方法
1. コマンドプロンプトを起動
2. cd {本ディレクトリ}でカレントディレクトリを移動
3. robot -X -V resource/{リソースファイル名(.yml)} tasks/{実施試験のファイル(.robot)}で試験を実行
4. プロンプトが返ってくるまで待機
5. log.htmlで試験結果を確認

# 開発者向け
- libdoc.html: 本ツール用に開発した、Robotファイルで使用可能なKeywordのドキュメント
- SshDriver.py: 本ツール用に開発した、Keywordの定義ファイル