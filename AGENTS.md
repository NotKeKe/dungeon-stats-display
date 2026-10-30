# Dungeon Stats Display (Minecraft Hypixel Skyblock)
簡稱 DSD

## 規則
- 你絕對不能修改任何 `system/` 裡面的東西
- 在編寫完一個 python 檔案時，執行 `uvx ty check`，確保沒有語法錯誤。

## 依賴規定
- 有關檔案路徑，一律使用 pathlib，而不是 sys
- 有關網路請求，一律使用 requests

## Minescript 參考資料
- 官方網站／API 文件：https://minescript.net/ （有時會連不上，連不上時可改看 GitHub 或本機定義）
- GitHub：https://github.com/maxuser0/minescript
- 本機 API 定義（最準）：`system/lib/minescript.py`（目前 Minescript 5.0b11）

## 專案結構
開發時使用正常的 Python package 結構，原始碼位於 `src/`，`main.py` 是進入點。
部署前執行 `python scripts/bundle.py`，會用 stickytape 將 `main.py` + `src/` 打包成單一檔案 `dungeon_stats_display.py`；最終只有這個檔案會被放進正式環境（`dungeon_stats_display.py` 是 build output，已被 `.gitignore` 忽略）。

```text
main.py                    進入點：init_core → 註冊 hook／指令 → 啟動 log 迴圈與 event 迴圈
src/
├── core/                  共用基礎設施
│   ├── setup.py           init_core()：初始化路徑常數、logger、sqlite cache
│   ├── constants.py       DSDCategory、dsd_prefix()、CHAT_PATTERN／LEAP_PATTERN
│   ├── dispatcher.py      聊天室 hook 與 !dsd 指令的註冊／分派
│   └── api.py             get_uuid()（Mojang API + sqlite 快取）
├── stats_display/         主功能：顯示 party finder 加入者的 stats
│   ├── handler.py         on_chat／!dsd search 入口，整理資料後交給 Display
│   ├── api.py             API key（.env）、Hypixel profiles 請求與快取
│   ├── cache.py           sqlite 快取（TTL 180 秒）
│   ├── constants.py       XP 表、floor、missing items、顏色等常數
│   ├── utils.py           NBT 解析、等級換算、PB 整理、背包／衣櫃掃描
│   └── display.py         產生 text component 並用 echo_json 輸出（含 hover）
├── user_block/            自動踢人
│   ├── handler.py         block list 命中時 /pc + /party kick
│   ├── database.py        blocked_users 資料表
│   └── constants.py       預設踢人理由
├── leap_notify/           leap 通知
│   ├── handler.py         偵測 leap 後依模板發送 /pc
│   └── database.py        leap_settings 資料表
└── auto_fill/             自動補充：偵測到指定句子時用 /gfs 補物品
    ├── handler.py         觸發判斷、背包計數、!dsd autofill
    └── database.py        auto_fill_rules 資料表
scripts/bundle.py          stickytape 打包腳本
docs/                      各語言 README 與 demo 圖片
system/                    Minescript 執行環境（禁止修改、已被 gitignore 忽略）
dungeon_stats_display.py   打包產物（build output，不進版控）
```

**模組關係**
- `src/core/dispatcher.py` 是所有訊息的入口：聊天室訊息依 `pattern_id` 分派給註冊的 hook（目前 `party_finder` → `user_block`、`stats_display`；`leap` → `leap_notify`），`!dsd` 開頭的訊息依前綴分派給各模組的指令函式。
- 同一個 pattern 的 hook 依註冊順序全部執行；hook 沒有回傳值、不會互相打斷（`user_block` 踢人後仍會顯示 stats）。
- `add_chat_listener()` 註冊的 listener 不受 pattern 限制，會收到每一則訊息；`auto_fill` 用它比對使用者自訂的觸發句。
- `src/stats_display/constants.py` 會從 `src/core/constants.py` re-export 路徑、logger、cache，因此 **`init_core()` 必須在 import 任何 handler 之前呼叫**，否則會拿到 `None`。

**啟動流程**
1. `main.py` 先執行 `init_core(BASE_DIR)`：建立 `DATA_DIR`、`DB_PATH`、`ENV_PATH`、`CRASH_LOG_DIR`、`LOG_PATH`，並初始化 logger 與 sqlite cache（每次啟動會清空 cache）。
2. import 各模組的 handler，註冊聊天室 hook／listener 與 `!dsd key`、`!dsd block`、`!dsd leap`、`!dsd search`、`!dsd autofill`、`!dsd help` 指令（另有單獨的 `!dsd`）。
3. 背景 thread 持續 tail `BASE_DIR.parent / "logs" / "latest.log"`，把新出現的行交給 `dispatch_chat()`。
4. 主執行緒用 `minescript.EventQueue` 攔截前綴為 `!dsd` 的訊息，交給 `dispatch_command()`。
5. 兩個迴圈各自有 try/except：發生例外時寫入 `crash_logs/crash_{loop}_{timestamp}.log`，並在遊戲內輸出簡短錯誤，之後繼續運作。

**執行時資料**
資料目錄為腳本所在位置的 `dungeon-stats-display/`（部署後即 `.minecraft/minescript/dungeon-stats-display/`）：
- `dungeons.db`：sqlite。`cache` 表在啟動時建立並清空，`blocked_users`（user_block）、`leap_settings`（leap_notify）、`auto_fill_rules`（auto_fill）在第一次使用時建立。
- `.env`：Hypixel API key（`KEY=...`）
- `dsd.log`：logger 輸出（RotatingFileHandler，上限 100 KB）
- `crash_logs/`：log／event 迴圈的 crash log

## dungeon stats display 流程
注意以下除非特別提及，否則 **輸出** ，一律指透過 minescript 進行輸出 (如 echo_json)
stats_display 的錯誤訊息都會帶上 `DSD (StatsDisplay)> ` 前綴。

1. **持續** 抓取聊天室留言，格式如下:
    - Party Finder > {USER_NAME} joined the dungeon group! ({CLASS} Level {LEVEL})
    - 範例: Party Finder > keke joined the dungeon group! (Healer Level 30)

2. 利用第一階段的 user_name，去取得使用者的 **uuid**
    - 調用 `https://api.mojang.com/users/profiles/minecraft/{USER_NAME}`，取得回傳 json 中的 ['id'] 項 (即 UUID)，結果會寫入 sqlite 快取
    - 注意判斷 status_code 是否為 200，如果不是，則輸出 `DSD (StatsDisplay)> Cannot find user {USER_NAME}`

3. 利用 UUID 去取得使用者的 profiles 訊息並輸出
    - 調用 `https://api.hypixel.net/v2/skyblock/profiles?key={API_KEY}&uuid={UUID}`
    - 一樣判斷 status_code，不是 200
        - 試試能不能 parse 成 json，可以的話就 .get('cause')
        - 輸出 `DSD (StatsDisplay)> Hypixel API error: {status_code}`，如果有取得 cause，就在輸出後面加上 ` ({cause})`
    - 是 200
        - 調用一系列 package 裡面的東西 (注意如果有緩存，要先用緩存)
        - 輸出格式如下:
        ```text
        ---------- {USER_NAME} ----------
        Cata: {CATACOMBS_LEVEL} | Secrets: {SECRETS} (AVG_SECRET)
        Classes: {ARCHER_levelWithProgress}/{BERS}/{HEALER}/{MAGE}/{TANK} (Avg: {CLASS_AVG})
        Floors: Normal | Master | MP: {MAGICAL_POWER}
        Armor: ⛑ | 🛡 | 👖 | 👢
        Owned: ✔ {OWNED_COUNT}
        Missing: ✖ Claymore | ✖ Spring Boots
        --------------------
        ```
        - 說明:
        ```text
        Floors: Normal | Master | ...        <---- hover 顯示該模式各樓層的 PB 表（Floor | S | S+ | COMP），沒資料的樓層不顯示
        Armor: ⛑ | 🛡 | 👖 | 👢              <---- hover 顯示裝備名稱＋數值／附魔等 lore；空位顯示 gray 的 None、icon 也是 gray
        Owned: ✔ 3                            <---- hover 顯示實際偵測到的項目；重複持有會顯示 × N（如 Terminator × 2）
        Missing: ✖ Wither Blade | ...         <---- 只列缺少的項目（全部都有則顯示 None）；對照表如 GYROKINETIC_WAND -> Gyro，寵物排在最後
        ```
        - 檢查範圍（Owned／Missing）：背包、身上裝備、終界箱、背囊，以及衣櫃（loadout）內的套裝；寵物（Spirit／EDrag／GDrag）另外從 `pets` 資料判斷。
        - 檢查項目順序：Claymore → Gyro → Ice Spray → Spring Boots → Terminator → Wither Blade → Spirit → EDrag → GDrag。
        1. 範例:
            normal:
            ```text
            Floor | S | S+ | COMP
            F1: 1m34s | 1m35s | 1m35s
            F2: 10m01s | 2m35s | 2m36s
            ...(省略)
            F7: 5m06s | 4m59s | 4m59s
            ```
            master:
            ```text
            Floor | S | S+ | COMP
            M1: 2m01s | 2m01s | 2m01s
            M2: 4m45s | 4m45s | 4m45s
            M3: 1m00s | 1m01s | 1m01s
            ...
            M7: 10m05s | 9m05s | 9m05s
            ```
            （hover 配色：樓層名稱金色、S 白色、S+ aqua、COMP 綠色；沒有紀錄顯示 `-`，完全沒資料則顯示 `No data`）
        - 範例:
        ```text
        ---------- ImSomeOne ----------
        Cata: 32.98 | Secrets: 2,860 (8.8)
        Classes: 27.7/27.86/30.93/28.03/26.16 (Avg: 28.1)
        Floors: Normal | Master | MP: 657
        Armor: ⛑ | 🛡 | 👖 | 👢
        Owned: ✔ 3
        Missing: ✖ Claymore | ✖ Ice Spray
        --------------------
        ```

        - 透過 sqlite 直接做結果緩存 (每個 function 的輸出結果，這樣下次可以直接拿出來用；TTL 180 秒，啟動時會清空)

## auto fill 流程
偵測到指定的聊天室句子時，自動用 `/gfs` 把物品補到目標數量。可以設定多項規則，每項可獨立暫停。

- 沒有預設規則：用 `!dsd autofill <item_id> <target_count> <trigger>` 新增／更新規則（例如 `!dsd autofill ENDER_PEARL 16 Starting in 3 seconds.`）。同一個 item_id 再次設定會覆蓋該項並重新啟用；設定存在 sqlite，重啟後仍然有效。
- `src/auto_fill/handler.py` 的 `on_chat()` 透過 `add_chat_listener()` 收到每一則訊息，逐一檢查所有啟用中的規則；比對到觸發句後，用 `minescript.player_inventory()` 計算原版背包（hotbar + 主背包）中該 item 的總數量（同一個觸發句可以同時觸發多項規則）。
- 觸發句的比對方式是取出 `[CHAT]` 後面的聊天內容，與 trigger 做**完全相等**比對（不是子字串）；不是聊天行或內容不完全相同都不會觸發。
- item id 比對：先從 `ItemStack.nbt`（Minescript 用 `ItemStack.CODEC` 序列化整個 ItemStack 的 SNBT）解析 Skyblock id（`item_name` 的 `skyblock:XXX` translate key、`custom_data.id`、舊版 `ExtraAttributes.id`）；NBT 裡沒有可辨識的 id 時才 fallback 到原版 registry id（`ENDER_PEARL` → `minecraft:ender_pearl`）。若現有數量 < 目標數量，執行 `/gfs {ITEM_ID} {目標數量 - 現有數量}`，並在遊戲內輸出這次補了多少。
- 指令：
  - `!dsd autofill`：顯示 help（並提示用 `!dsd autofill list` 查看規則）
  - `!dsd autofill list`：列出所有規則（依新增順序編號 1..n）與啟用狀態
  - `!dsd autofill <item_id> <target_count> <trigger>`：新增／更新某一項
  - `!dsd autofill pause <rule_id>`／`resume <rule_id>`：暫停／恢復指定編號的規則
  - `!dsd autofill remove <rule_id>`（別名 `rm`）：刪除指定編號的規則
- 編號只是列表的顯示順序（依新增順序，刪除後會重新編號），不是存在 DB 的欄位。
- 設定存在 sqlite 的 `auto_fill_rules`（`item_id` 為 key，另有 `target_count`、`trigger`、`enabled`），第一次使用時載入並快取在記憶體，指令修改後會重新載入。
