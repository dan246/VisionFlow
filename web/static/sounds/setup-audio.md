# 音效文件設置指南

## 🔊 快速設置音效文件

### 方法一：使用免費音效資源

**推薦網站：**
- [Freesound.org](https://freesound.org) - 免費音效資源
- [Zapsplat](https://www.zapsplat.com) - 高質量音效庫
- [BBC Sound Effects](https://sound-effects.bbcrewind.co.uk) - BBC 音效資料庫

**搜索關鍵字：**
- critical-alert: "alarm", "emergency", "urgent"
- high-alert: "notification", "bell", "chime"
- medium-alert: "soft bell", "ding", "gentle"
- success: "success", "complete", "positive"
- info: "pop", "click", "subtle"

### 方法二：使用文字轉語音 (TTS) 創建

```bash
# 使用 macOS 內建 TTS
say "Critical Alert" -o critical-alert.aiff
afconvert critical-alert.aiff critical-alert.mp3

say "High Priority" -o high-alert.aiff
afconvert high-alert.aiff high-alert.mp3

say "Medium Priority" -o medium-alert.aiff
afconvert medium-alert.aiff medium-alert.mp3

say "Success" -o success.aiff
afconvert success.aiff success.mp3

say "Information" -o info.aiff
afconvert info.aiff info.mp3
```

### 方法三：使用在線音效生成器

**在線工具：**
- [BFXR](https://www.bfxr.net) - 遊戲音效生成器
- [Audacity](https://www.audacityteam.org) - 免費音頻編輯軟體
- [Online Tone Generator](https://onlinetonegenerator.com) - 音調生成器

### 方法四：系統音效複製

```bash
# macOS 系統音效位置
cp /System/Library/Sounds/Glass.aiff ./
afconvert Glass.aiff critical-alert.mp3

cp /System/Library/Sounds/Ping.aiff ./
afconvert Ping.aiff high-alert.mp3

cp /System/Library/Sounds/Pop.aiff ./
afconvert Pop.aiff medium-alert.mp3

cp /System/Library/Sounds/Bottle.aiff ./
afconvert Bottle.aiff success.mp3

cp /System/Library/Sounds/Tink.aiff ./
afconvert Tink.aiff info.mp3
```

### 音效文件規格

- **格式**: MP3
- **長度**: 1-3 秒
- **大小**: < 100KB
- **採樣率**: 44.1kHz
- **位元率**: 128kbps

### 完成後

將下載或創建的音效文件重命名並放置在此目錄：

```
/static/sounds/
├── critical-alert.mp3
├── high-alert.mp3
├── medium-alert.mp3
├── success.mp3
└── info.mp3
```

### 測試音效

在瀏覽器開發者工具中執行：

```javascript
// 測試音效播放
const audio = new Audio('/static/sounds/critical-alert.mp3');
audio.play();
```

### 注意事項

- 確保音效文件版權清楚
- 測試音效在不同設備的相容性
- 考慮用戶體驗，避免音效過響或過長
- 在安靜時間應自動禁用音效
