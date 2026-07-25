# Dungeon Stats Display (Minecraft Hypixel Skyblock)
簡稱 DSD

## 規則
- 你絕對不能修改任何 `system/` 裡面的東西
- 在編寫完一個 python 檔案時，執行 `uvx ty check`，確保沒有語法錯誤。

## 依賴規定
- 有關檔案路徑，一律使用 pathlib，而不是 sys
- 有關網路請求，一律使用 requests

## 專案結構
開發時，程式碼位於 `src/core,stats_display,user_block` 中，使用正常的 Python package 結構。
`main.py` 是進入點。

部署前，執行 `python scripts/bundle.py` 來使用 stickytape 將所有程式碼打包成單一檔案 `dungeon_stats_display.py`。
最終只有 `dungeon_stats_display.py` 會被進到正式環境。

## dungeon stats display 流程
注意以下除非特別提及，否則 **輸出** ，一律指透過 minescript 進行輸出 (如 echo)

1. **持續** 抓取聊天室留言，格式如下:
    - Party Finder > {USER_NAME} joined the dungeon group! ({CLASS} Level {LEVEL})
    - 範例: Party Finder > keke joined the dungeon group! (Healer Level 30)

2. 利用第一階段的 user_name，去取得使用者的 **uuid**
    - 調用 `https://api.mojang.com/users/profiles/minecraft/{USER_NAME}`，取得回傳 json 中的 ['id'] 項 (即 UUID)
    - 注意判斷 status_code 是否為 200，如果不是，則輸出 `DSD: Cannot find user `{USER_NAME}` `

3. 利用 UUID 去取得使用者的 profiles 訊息並輸出
    - 調用 `https://api.hypixel.net/v2/skyblock/profiles?key={API_KEY}&uuid={UUID}`
    - 一樣判斷 status_code，不是 200
        - 試試能不能 parse 成 json，可以的話就 .get('cause')
        - 輸出 `DSD: Hypixel API error: `{status_code}` `，如果有取得 cause，就在輸出後面加上 cause
    - 是 200
        - 調用一系列 package 裡面的東西 (注意如果有緩存，要先用緩存)
        - 輸出格式如下:
        ```text
        ---------- {USER_NAME} ----------
        Cata: {CATACOMBS_LEVEL} | Secrets: {SECRETS} (AVG_SECRET)
        Classes: {ARCHER_levelWithProgress}/{BERS}/{HEALER}/{MAGE}/{TANK} (Avg: {CLASS_AVG})
        Floors: Normal | Master | MP: {MAGICAL_POWER}
        Armor: ⛑ | 🛡 | 👖 | 👢
        Missing: ✖ Wither Blade | ✖ GDrag | ✖ EDrag |
        --------------------
        ```
        - 說明:
        ```text
        Floors: Normal | Master | MP: {MAGICAL_POWER}   <---- 這裡的 normal 跟 master，要在觸發 hover 的時候，去顯示文字，如1
        Armor: ⛑ | 🛡 | 👖 | 👢    < ---- 這裡的每個 emoji，都要顯示使用者的裝備名稱
        Missing: ✖ Wither Blade | ✖ GDrag | ✖ EDrag | <---- 這裡要寫一個 dict 對照表，例如 GYROKINETIC_WAND -> Gyro
        ```
        1. 範例:
            normal:
            ```text
            Floor | S | S+
            F1: 1m34s | 1m35s
            F2: 10m1s | 2m355
            ...(省略)
            F7: 5m6s | 4m59s
            ```
            master:
            ```text
            Floor | S | S+
            M1: 2m1s | 2m1s
            M2: 4m45s | 4m45s
            M3: 1m00s | 1m01s
            ...
            M7: 10m5s | 9m5s
            ```
        - 範例:
        ```text
        ---------- ImSomeOne ----------
        Cata: 32.98 | Secrets: 2860 (8.8)
        Classes: 27.70/27.86/30.93/28.03/26.16 (Avg: 28.1)
        Floors: Normal | Master | MP: 657
        Armor: ⛑ | 🛡 | 👖 | 👢
        Missing: ✖ Wither Blade | ✖ GDrag | ✖ EDrag
        ----------
        ```

        - 透過 sqlite 直接做結果緩存 (每個 function 的輸出結果，這樣下次可以直接拿出來用)
