# CH552ファームウェア計画

## 初期試作

`ch552_keyboard_prototype/ch552_keyboard_prototype.ino` はUSBキーボードのみの試作ソース。

1. Arduino IDEにCH55xDuino **0.0.26** を導入する。
2. ボードはCH552 Board、USB SettingsはUSER CODEにする。
3. CH55xDuinoのHidKeyboardサンプルに付属する `src/userUsbHidKeyboard` 以下のすべてのC/Hファイルをスケッチフォルダー `src/userUsbHidKeyboard` へコピーする（コアと同バージョンを使用）。
4. ソース上部の `KEY_...` 文字定義を変更する。英数字1文字が当面の検証対象。特殊キー・修飾キーはこの試作段階で未実装。
5. CH552のP3.6/BOOTを押しながらUSBを接続して書き込む（メーカー実装のブート操作は実機照合）。
6. WindowsのテキストエディターまたはHIDキーイベントテスターで **無線機を接続せず** に操作検証。

## 次の統合段階（まだ未実装）

- Keyboard + Gamepad のUSB Composite HID（HIDレポートディスクリプタと各インターフェース）
- ダイヤルとF1/F2/PTTの任意キーコード／修飾キーの設定
- ゲームパッドボタンとキーボードキーへの出力モード切替
- WebTRXの実際の入力仕様（公式ショートカット、ブラウザ側イベント処理）との照合
- PTT解除のフェイルセーフ（Webアプリ側の通信タイムアウト・フォーカス喪失時処理）

## 状態

ビルド未実施、USB認識未検証、実機テスト未実施。
