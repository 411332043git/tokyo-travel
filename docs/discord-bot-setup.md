# Discord Bot 設定步驟

目標：在 Discord Developer Portal 建立 Agent 的 bot 帳號、打開需要的權限、拿到 bot token，並把 bot 邀進你自己的伺服器。

> 先完成 `docs/discord-server-setup.md`（要先有你自己的伺服器）。

> **名詞**
> - **Developer Portal（開發者後台）**：Discord 給開發者管理機器人的網站。
> - **Application（應用程式）**：你在後台建立的「專案」，bot 是裡面的一部分。
> - **Bot**：看起來像一個普通成員的機器人帳號，由我們的 Agent 程式在背後控制。
> - **Token**：bot 的「密碼」。拿到 token 的人可以完全控制你的 bot。
> - **Intent**：Discord 的「資料權限開關」，沒打開，bot 就拿不到對應的資料。

> **介面文字**：按鈕先寫英文，再寫中文（括號內）。後台是網頁，Discord 偶爾改版，位置可能微調，找同名項目即可。

---

## ⚠️ 先看這一段：bot token 絕對不能外流

**Bot token 等同於 bot 的密碼。**

- ❌ **不能貼給任何人**（同學、朋友、客服都不行）。
- ❌ **不能貼進這個 Claude 對話**。對話內容會被傳送與保存，貼出去就等於外洩。
- ❌ **不能 commit 進 git**，也不能放進程式碼、README、截圖、螢幕分享。
- ✅ 只放在專案根目錄的 `.env` 檔裡。這個專案的 `.gitignore` 已經設定忽略 `.env`。
- ✅ 如果不小心外洩（貼到任何地方），**立刻回後台按 Reset Token（重設 token）**，舊的馬上失效。步驟在第三節。

有 token 的人可以：用你的 bot 發訊息、讀它看得到的所有頻道內容、在你的伺服器裡搞破壞。

---

## 一、建立 Application 和 Bot

1. 用瀏覽器打開 <https://discord.com/developers/applications>。
2. 如果要求登入，用**你平常用的 Discord 帳號**登入。
3. 點右上角藍色按鈕 **New Application**（新增應用程式）。
4. **Name**（名稱）輸入 `Tokyo Travel Agent`（會顯示成 bot 的名字，之後可改）。
5. 勾選 **I agree to the Discord Developer Terms of Service and Developer Policy**（同意條款）。
6. 點 **Create**（建立）。可能出現「我不是機器人」驗證，照做。
7. 進到應用程式頁面後，看**左邊選單**，點 **Bot**。
   > 新的應用程式通常已經自動有 bot。如果畫面是 **Add Bot** 按鈕，點它並確認 **Yes, do it!**。

### 1.1 關掉「任何人都能邀請」

1. 在 **Bot** 頁面往下捲，找到 **Public Bot**（公開機器人）。
2. 把開關**關閉**（變灰色）。
   > 關閉後只有你（擁有者）能把 bot 邀到伺服器，別人拿到邀請連結也加不了。這是為了避免陌生人把 bot 拉到別的地方消耗你的額度。
3. 如果看到 **Requires OAuth2 Code Grant**（需要 OAuth2 授權碼）：**保持關閉**。

---

## 二、打開 Message Content Intent（一定要）

### 為什麼一定要

Discord 為了保護隱私，預設**不讓 bot 看到訊息的內容**，只看得到「有訊息」這件事。

我們的 Agent 要讀你打的字（例如「從人形町到澀谷」）和判斷指令（例如「English」「匯出」），沒有這個權限，它收到的訊息會是**空白**，整個 Agent 等於聾子。

這個權限叫 **Message Content Intent**（訊息內容權限），屬於「特權權限」，要自己在後台打開。

### 步驟

1. 在左邊選單點 **Bot**，往下捲到 **Privileged Gateway Intents**（特權閘道權限）。
2. 只把 **Message Content Intent** 的開關**打開**（變成藍色／綠色）。
3. **Presence Intent** 和 **Server Members Intent** 保持**關閉**（我們用不到，開越少越安全）。
4. 頁面下方會出現一個提示條，點 **Save Changes**（儲存變更）。
   > 沒按儲存，設定不會生效。

> 提醒：bot 加入的伺服器少於 100 個時，這個權限可以自己打開，不用 Discord 審核。我們只加你自己的伺服器，沒問題。

---

## 三、取得 Bot Token

1. 還在左邊選單 **Bot** 頁面，往上看到 **Token** 區塊。
2. 點 **Reset Token**（重設 token）。
   > 新建立的應用程式，這個按鈕可能就是第一次產生 token。
3. 跳出確認視窗，點 **Yes, do it!**（是的，執行）。
4. 如果要求輸入密碼或兩步驟驗證碼，照做。
5. 畫面會顯示一串很長的字（像 `MTIz...abc.Gxyz.xxxx`），旁邊有 **Copy**（複製）按鈕。點它。
6. 打開專案資料夾 `C:\Users\馨縵\tokyo-travel`，建立（或編輯）一個叫 **`.env`** 的檔案，貼上：

   ```
   DISCORD_TOKEN=貼上剛剛複製的那串字
   CHANNEL_ID=（你在上一份文件拿到的頻道 ID）
   OWNER_ID=（你自己的使用者 ID）
   CLAUDE_MODEL=（等程式階段再決定）
   DATA_DIR=C:\TokyoTravelData
   ```
   > `=` 前後**不要有空格**，token 前後**不要加引號**。
   > `.env` 檔名前面有一個點，Windows 記事本存檔時要選「所有檔案」，否則會變成 `.env.txt`。

### ⚠️ 必看

- **Token 只會顯示這一次。** 關掉頁面就看不到了，只能再按 Reset Token 重新產生一個（舊的會失效）。
- 複製後**立刻**貼進 `.env`，不要貼到別的地方暫存（LINE、記事本、雲端筆記都不行）。
- **確認 `.env` 沒被 git 追蹤**，在專案資料夾執行：

  ```
  git status
  ```
  畫面裡**不應該**出現 `.env`。如果出現，**不要 commit**，先告訴我。

### 如果 token 外洩了

1. 立刻回到 <https://discord.com/developers/applications> → 你的 application → **Bot**。
2. 點 **Reset Token** → **Yes, do it!** → 舊的立刻失效。
3. 把新的 token 貼進 `.env` 取代舊的。
4. 如果曾經貼進這個對話或 git，要視同外洩，**一定要重設**。
   > 如果是 push 到公開的 GitHub 上，Discord 會自動偵測並重設，但別指望這個。

---

## 四、決定 bot 需要哪些權限

Discord 的權限是「最小夠用」原則：只勾需要的。

### 需要勾選的 Bot Permissions（機器人權限）

| 權限 | 中文 | 為什麼需要 |
|---|---|---|
| View Channels | 檢視頻道 | 看得到 `# tokyo-travel` 才能收訊息 |
| Send Messages | 傳送訊息 | 回覆「處理中」和結果 |
| Read Message History | 讀取訊息歷史 | 看得到使用者傳的訊息與附件；編輯自己先前的「處理中」訊息 |
| Add Reactions | 新增反應 | 收到訊息時加上 ⏳，處理完換成 ✅ 或 ❌ |

### 絕對不要勾

- ❌ **Administrator**（管理員）：等於全部權限，bot 被盜用後果最大。
- ❌ **Manage Server / Manage Channels / Manage Messages / Kick / Ban** 等管理類權限：我們用不到。
- ❌ **Mention Everyone**（提及所有人）：避免意外 `@everyone`。

### Scope（範圍）要勾

| Scope | 為什麼 |
|---|---|
| `bot` | 讓它以機器人身份加入伺服器 |
| `applications.commands` | 之後要做 `/匯出`、`/清除` 這類斜線指令 |

---

## 五、把 Bot 邀進你自己的 Server

1. 在後台左邊選單點 **OAuth2**。
2. 往下捲到 **OAuth2 URL Generator**（網址產生器）。
3. **SCOPES**（範圍）區：勾 **`bot`** 和 **`applications.commands`**。
4. 勾選 `bot` 之後，下方會多出 **BOT PERMISSIONS**（機器人權限）區，勾這四個：
   - **View Channels**（檢視頻道）
   - **Send Messages**（傳送訊息）
   - **Read Message History**（讀取訊息歷史）
   - **Add Reactions**（新增反應）
5. 捲到最下面，**GENERATED URL**（產生的網址）會自動出現一長串。點旁邊的 **Copy**（複製）。
   > **Integration Type**（整合類型）如果有選項，選 **Guild Install**（伺服器安裝）。
6. 把網址貼到**瀏覽器網址列**，按 Enter。
7. 在 **Add to server**（加入伺服器）下拉選單選**你自己的伺服器**（例如 `東京旅遊測試`）。
   > 只有你有管理權限的伺服器才會出現在清單，所以只會看到自己建立的。
8. 點 **Continue**（繼續）。
9. 檢查畫面列出的權限是否跟上面四項一樣，沒有多出 Administrator。點 **Authorize**（授權）。
10. 完成「我不是機器人」驗證。
11. 看到「已授權」（Authorized）就成功了。

### 確認 bot 已經進來

1. 回到 Discord，打開你的伺服器，看右邊的成員清單。
2. 你應該看到 `Tokyo Travel Agent`，旁邊有一個 **BOT** 標籤。
3. 這時它的狀態是**離線**（灰色）。這是正常的：Agent 程式還沒啟動，它才是 bot 的「大腦」。程式一跑起來，它就會變成上線。

### 確認 bot 在 `# tokyo-travel` 頻道有權限

1. 對 `# tokyo-travel` 按右鍵 → **Edit Channel**（編輯頻道）。
2. 左邊選 **Permissions**（權限）。
3. 如果有看到 `Tokyo Travel Agent` 這個角色，且沒有被打叉，就沒問題。
4. 如果之後 bot 看不到頻道，最常見是這裡被擋住：把 **View Channel** 和 **Send Messages** 給它。

---

## 六、完成檢查

- [ ] Developer Portal 看得到 `Tokyo Travel Agent`。
- [ ] **Public Bot** 已關閉。
- [ ] **Message Content Intent** 已打開，且已按 Save Changes。
- [ ] Presence 與 Server Members Intent 沒開。
- [ ] Token 已複製並貼進 `.env`；沒有貼到任何其他地方，也沒有貼進任何對話。
- [ ] `git status` 沒有出現 `.env`。
- [ ] Bot 權限只有四項（含 Add Reactions），沒有 Administrator。
- [ ] 你的伺服器成員清單看得到 bot（離線是正常的）。

## 常見問題

| 狀況 | 原因與處理 |
|---|---|
| 程式啟動後出現 `PrivilegedIntentsRequired` 之類的錯誤 | Message Content Intent 沒開或沒按儲存，回第二節。 |
| 程式啟動後出現 `LoginFailure`／`Improper token` | Token 貼錯：複製不完整、前後有空格或引號、或已經被重設。回第三節重新產生。 |
| Bot 上線了，但訊息內容是空的 | 同第一項，Message Content Intent 沒生效。 |
| Bot 上線了，但不回應 | 檢查 `CHANNEL_ID` 是不是 `# tokyo-travel` 的 ID；檢查頻道權限；檢查你是否已在 Agent 的授權名單中。 |
| 第五節找不到自己的伺服器 | 你登入後台的帳號跟擁有伺服器的帳號不是同一個。 |
| 想讓別人也能邀請 bot | 不要開 Public Bot；改成請擁有者（你）自己操作。 |

下一步：回到專案，開始實作 Agent 的程式（本階段只設定 Discord，尚未啟動任何程式）。
