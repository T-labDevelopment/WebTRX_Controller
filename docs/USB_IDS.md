# USB識別子・割当管理（Rev.A）

| 項目 | 値 | 状態 |
|---|---|---|
| 管理型番 | `WTRX-DIAL-CH552-RA` | プロジェクト内で仮確定 |
| iManufacturer | `DIY Radio Controller` | 試作用文字列 |
| iProduct | `WebTRX Dial Controller RevA` | 試作用文字列 |
| iSerial | `WTRXRA0001` | **試作1台限定**。複数台に使い回さない |
| idVendor | `0x1209` | pid.codes所有。私的試験用に限り利用 |
| idProduct | `0x0001` | pid.codes私的試験用。**正式取得済みではない** |
| bcdDevice | `0x0100` | Rev.A 初期識別 |
| iInterface | なし | 単一HIDインターフェース、2つのTop-Level Collection |
| Report ID 1 | Keyboard (8 bytes + ID) | F1/F2/PTT任意キー用 |
| Report ID 2 | Gamepad (2 bytes + ID) | X軸・予備Button1～3 |

**注意**: pid.codesは `1209:0001` を**社内・個人の私的な試験**にのみ許可しています。
配布・販売・製造するデバイスでは利用禁止です。完成製品は自ら割り当て権限を持つVIDでPIDを割り当てるか、適法な割当手続を行います。
Open-sourceプロジェクトとして公開する場合、pid.codesの申請条件を確認してPIDを正式に申請できます。

- 私的試験ID: https://pid.codes/1209/0001/
- 正式PID申請: https://pid.codes/howto/
- USB-IF: https://www.usb.org/developers

既存のWeActボードに入っているUSBブートローダーのVID/PIDは、ユーザーファームウェアの実行時に列挙されるVID/PIDとは別です。ブートローダーの識別子は変更しません。
