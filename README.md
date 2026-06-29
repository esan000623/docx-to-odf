# DOCX / PPTX 轉 ODF 批次轉換工具

Web 介面的批次檔案格式轉換工具，將 Microsoft Office 格式轉為 ODF 開放格式。

## 支援格式

| 輸入 | 輸出 |
|------|------|
| .docx / .doc | .odt |
| .pptx / .ppt | .odp |
| .xlsx / .xls | .ods |

## 環境需求

1. **Python 3.8+**（已確認 Python 3.12 可用）
2. **LibreOffice**（轉換引擎）
   - 下載：https://www.libreoffice.org/download/download-libreoffice/
   - 安裝完成後，確認可在命令列執行 `soffice --version`

## 安裝與啟動

### 方法一：使用啟動腳本（已設定好 venv）

```
直接雙擊 start.bat
```

### 方法二：手動啟動

```bash
# 使用 venv 內的 Python（MSYS2 環境）
venv\bin\python.exe app.py
```

然後開啟瀏覽器前往 **http://localhost:5000**

## 使用方式

1. 拖曳或點擊選擇多個 .docx / .pptx / .xlsx 等檔案
2. 點擊「開始轉換」
3. 等待轉換完成後，點擊「下載轉換後的檔案」取得 ZIP 壓縮包

## LibreOffice 路徑問題（Windows）

若頁面顯示「未偵測到 LibreOffice」，請在 `app.py` 中手動指定路徑：

```python
LIBREOFFICE_PATH = r'C:\Program Files\LibreOffice\program\soffice.exe'
```

## 專案結構

```
docx-to-odf/
├── app.py              # Flask 後端
├── templates/
│   └── index.html      # 前端介面
├── venv/               # Python 虛擬環境
├── start.bat           # 快速啟動腳本
├── requirements.txt    # Python 套件清單
└── README.md
```
