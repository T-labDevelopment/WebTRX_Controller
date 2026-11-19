# WebTRX連携設計案 — 1クリック=1 VFO カウント

現在のWebTRX実装に統合済みという意味ではない。ブラウザ側にGamepad API入力対応が必要。

## 判定方法

- Joystick X: 正転が +127、逆転が -127、中立0。ブラウザGamepad APIでは概ね+1.0/-1.0/0.0。
- `ready` 状態でX>=0.8ならVFO+1、X<=-0.8ならVFO-1。その後 `ready=false` とする。
- `ready=false` の間は無視し、abs(X)<=0.15の中立を確認したら `ready=true` に戻す。
- 連続CW 2クリックは `+1, 中立, +1, 中立`、CCWは `-1, 中立, -1, 中立`。
- Gamepad APIは状態ポーリングでありイベントを過去へ遡って復元できないため、ページが非アクティブまたはFPS低下した場合はクリックを見落とす可能性がある。ウェブ側でのカウント保証は未検証。

## 最小限の変換ロジック例

```javascript
// Read axes[0] from the selected gamepad on each animation frame.
// This is an example, not a patch to the WebTRX source.
let axisReady = true;
function consumeDialAxis(x, changeVfoOneStep) {
  if (axisReady) {
    if (x >= 0.8) {
      changeVfoOneStep(+1);
      axisReady = false;
    } else if (x <= -0.8) {
      changeVfoOneStep(-1);
      axisReady = false;
    }
  } else if (Math.abs(x) <= 0.15) {
    axisReady = true;
  }
}
```

関連資料：
- https://developer.mozilla.org/ja/docs/Web/API/Gamepad/axes
- https://developer.mozilla.org/ja/docs/Web/API/Gamepad_API/Using_the_Gamepad_API
