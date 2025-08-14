
# HK CrowdTest‑lite Dashboard

這是「只顯示圖表與指標」的儀表板版本（無 CSV 下載）。

## 部署步驟
1. 把整個資料夾上傳到 GitHub。
2. 到 share.streamlit.io 新建 App → Main file 選 `app.py`。
3. 若頁面空白，請在右上角「Manage app → Logs」查看錯誤（通常是檔名或依賴）。

## 本地啟動
```
pip install -r requirements.txt
streamlit run app.py
```
