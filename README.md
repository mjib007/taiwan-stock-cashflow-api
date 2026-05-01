# 📊 Taiwan Stock Cashflow API (台股現金流自動化分析 API)

![Profile views](https://komarev.com/ghpvc/?username=mjib007&label=Profile%20views&color=4c8eda&style=flat)

這是一個基於 Python 與 Flask 打造的自動化台股現金流量分析工具。本專案旨在解決傳統財務分析中累積型數據不易判讀的問題，並將原始財報數據轉化為可操作的量化分析摘要。

## 🚀 專案亮點與核心功能
* **自動化資料處理：** 串接 [FinMind](https://github.com/FinMind/FinMind) API，自動抓取台灣股市過去 5 年的現金流量與稅前淨利數據。
* **智慧年化邏輯：** 自動轉換季度累計與全年數據，解決財報資料不一致的痛點。
* **六大現金流檢驗法則：**
  1. 營運現金流年增率評估
  2. 投資現金流紀律檢視
  3. 投資效益評估
  4. 融資活動合理性
  5. 現金流品質（A > D）
  6. 現金餘額穩定度

## 🏗️ 技術架構與部署說明
本專案採用現代化的 Web 開發與自動化部署流程：

* **後端開發 (Backend):** 使用 **Python / Flask** 輕量化框架開發 RESTful API。
* **數據處理 (Data Processing):** 運用 **Pandas** 進行財務時間序列數據的清理、年化轉換與邏輯運算。
* **雲端部署 (Deployment):** * 專案託管於 **GitHub** 進行版本管理。
  * 串接 **Zeabur** 雲端平台實現 **CI/CD 自動化部署**（代碼推送即自動更新服務）。
  * 具備跨來源資源共享 (**CORS**) 支援，可供不同前端介面串接呼叫。

## 📄 開源授權
本專案採用 **MIT License** 開源，歡迎學術交流與技術參考。

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!  
Feel free to open an issue or submit a Pull Request. Let's build the future of LegalTech together!

---
*“The future of law is written in code.”*
