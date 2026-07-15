<h1 align="center">Dungeon Stats Display (Minescript)</h1>

<p align="center">
  一個 Minecraft Hypixel Skyblock Dungeon 腳本。
  <br>
  你可以使用自己的 API Key 來查看玩家數據!
  <br>
  基於 Minescript
</p>

<div align="center">

 ![Stars](https://img.shields.io/github/stars/NotKeKe/dungeon-stats-display?style=social)

 [![Docs](https://img.shields.io/badge/Docs-English-blue.svg)](../README.md)
 [![Docs](https://img.shields.io/badge/Docs-繁體中文-blue.svg)](readme-tw.md) <br>
 [![License](https://img.shields.io/badge/license-Apache%20License%202.0-yellow)](../LICENSE) <br>

</div>

## Why this?
- 最近，Odin mod 偶爾會顯示 429 或 500 相關的錯誤代碼，導致我們常常無法快速判斷玩家的裝備、Secrets 等是否符合我們的需求。
- 因此，我製作了這個**不到一千行**的腳本，讓使用者可以**自行申請 API Key 來發送請求**。
- 此外，所有從 Hypixel 回傳的資料都在本機處理，**你的 API Key 絕不會被上傳到 Hypixel 以外的任何地方！**

## Demo
輸出格式參考了 Odin 的設計——**向 Odin 致敬！**
![DEMO](./image.png)

## 如何使用？
- 從 Modrinth [下載 Minescript](https://modrinth.com/mod/minescript)
- **下載** `dungeon_stats_display.py` 檔案。
- 將 `dungeon_stats_display.py` 放入 minescript 資料夾。（通常位於 `.minecraft/minescript`，視你使用的啟動器而定）
- **別忘了在 [Hypixel developer](https://developer.hypixel.net/dashboard) 產生你的 API Key**。
- 進入 Minecraft 後，在聊天室輸入 `\dungeon_stats_display`。（啟動腳本）
- 輸入 `!dsd key YOUR_API_KEY`（將 YOUR_API_KEY 替換為你的實際 Key）
  - 你也可以輸入 `!dsd key` 來檢查 Key 是否設定正確。
- 現在你可以加入任何 Party Finder！你將會看到加入的玩家數據！

## TODO
- 懸停顯示功能目前還無法使用，所以暫時無法看到玩家實際穿戴的裝備。

## 授權
[Apache-2.0](LICENSE)
