# 📊 Taiwan Stock Cashflow API (台股現金流自動化分析 API)

這是一個基於 Python 與 Flask 打造的自動化台股現金流量分析工具。本專案旨在解決傳統財務分析中累積型數據不易判讀的問題，並將原始財報數據轉化為可操作的量化分析摘要。

---

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

---

## 🏗️ 系統架構說明

本專案採用輕量化的服務架構，主要由以下核心組件構成：
FinMind API  ---->  CashFlowAnalyzer  ---->  Flask API  
                                               │
                                               ├─> 資料清洗與年化分析
                                               └─> Zeabur CI/CD 雲端部署
1. **資料層 (Data Layer)：**
   透過 RESTful 請求從 FinMind 開放金融數據源獲取上市櫃公司的原始現金流量表。

2. **核心分析引擎 (Core Analysis Engine)：**
   * **`_convert_to_annual()`**：將原始資料中混雜的季度與單季累積資料，統一清洗轉換為近 5 年的年度數據。
   * **`_apply_rules()`**：封裝財務分析邏輯，自動執行六大現金流評分公式，將數字轉化為品質標籤（GOOD/AVERAGE/POOR）。
   * **`_generate_summary()`**：整合評分結果，生成直觀的中文財務分析報告與投資建議。

3. **應用層 (Application Layer)：**
   使用 Flask 框架封裝為 Web API，支援 CORS 跨來源資源共享。當程式碼推送到 GitHub 時，會自動觸發 Zeabur 的 CI/CD 流程完成雲端部署。

---

## 📄 開源授權

本專案採用 MIT License 開源。
