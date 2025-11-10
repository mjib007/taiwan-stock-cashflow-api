# app.py - Zeabur Flask API (Modified Version - Support Annual Data)
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import json

warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

class CashFlowAnalyzer:
    def __init__(self):
        """Cash Flow Analyzer - Zeabur API Version"""
        self.base_url = "https://api.finmindtrade.com/api/v4/data"
    
    def analyze_stock(self, stock_code):
        """Analyze cash flow for specified stock"""
        try:
            # Fetch data
            cashflow_data = self._fetch_cashflow_data(stock_code)
            
            if not cashflow_data:
                return {"success": False, "error": "Unable to fetch cash flow data"}
            
            # Perform analysis
            analysis_result = self._analyze_data(cashflow_data, stock_code)
            
            return {
                "success": True,
                "stock_code": stock_code,
                "analysis": analysis_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _fetch_cashflow_data(self, stock_code):
        """Fetch cash flow data for past 5 years"""
        start_date = (datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d")
        
        params = {
            "dataset": "TaiwanStockCashFlowsStatement",
            "data_id": stock_code,
            "start_date": start_date
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 200 and data.get("data"):
                    return data["data"]
            
            return None
            
        except Exception as e:
            print(f"API Error: {str(e)}")
            return None
    
    def _convert_to_annual(self, df):
        """Convert cumulative data to annual data - 5 years total"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # 確保 date 是 datetime 類型，但不重複設置 year 和 quarter
        if 'date' not in df.columns:
            return df
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        current_year = datetime.now().year
        result_data = []
        
        # 處理過去5年的資料
        for year in range(current_year - 4, current_year + 1):
            # 使用 date 欄位來篩選年份，避免使用可能的 datetime quarter 屬性
            year_mask = df['date'].dt.year == year
            year_data = df[year_mask].copy()
            
            if year_data.empty:
                print(f"Warning: No data for year {year}")
                continue
            
            # 添加臨時的 quarter 欄位
            year_data.loc[:, 'temp_quarter'] = year_data['date'].dt.quarter
            
            # 對於今年：使用到目前季度的最新累計資料
            if year == current_year:
                available_quarters = sorted(year_data['temp_quarter'].unique())
                if available_quarters:
                    latest_quarter = max(available_quarters)
                    latest_data = year_data[year_data['temp_quarter'] == latest_quarter].iloc[-1]
                    
                    new_record = {
                        'date': latest_data['date'],
                        'year': year,
                        'quarter': f"累計至Q{latest_quarter}",  # 字串格式
                        'stock_code': latest_data.get('stock_code', ''),
                        'A': latest_data.get('A'),
                        'B': latest_data.get('B'), 
                        'C': latest_data.get('C'),
                        'D': latest_data.get('D'),
                        'E': latest_data.get('E')
                    }
                    
                    if any(pd.notna(new_record.get(c)) for c in ['A', 'B', 'C', 'D']):
                        print(f"Processing current year {year}: Using cumulative data up to Q{latest_quarter}")
                        result_data.append(new_record)
                        
            else:
                # 對於過去年份：使用Q4的全年累計資料
                q4_data = year_data[year_data['temp_quarter'] == 4]
                if not q4_data.empty:
                    q4_record = q4_data.iloc[-1]
                    
                    new_record = {
                        'date': q4_record['date'],
                        'year': year,
                        'quarter': "全年累計",  # 字串格式
                        'stock_code': q4_record.get('stock_code', ''),
                        'A': q4_record.get('A'),
                        'B': q4_record.get('B'),
                        'C': q4_record.get('C'), 
                        'D': q4_record.get('D'),
                        'E': q4_record.get('E')
                    }
                    
                    if any(pd.notna(new_record.get(c)) for c in ['A', 'B', 'C', 'D']):
                        print(f"Processing past year {year}: Using Q4 annual cumulative data")
                        result_data.append(new_record)
                else:
                    # 如果沒有Q4資料，嘗試使用最高季度的累計資料
                    available_quarters = sorted(year_data['temp_quarter'].unique())
                    if available_quarters:
                        latest_quarter = max(available_quarters)
                        latest_record = year_data[year_data['temp_quarter'] == latest_quarter].iloc[-1]
                        
                        new_record = {
                            'date': latest_record['date'],
                            'year': year,
                            'quarter': f"累計至Q{latest_quarter}",  # 字串格式
                            'stock_code': latest_record.get('stock_code', ''),
                            'A': latest_record.get('A'),
                            'B': latest_record.get('B'),
                            'C': latest_record.get('C'),
                            'D': latest_record.get('D'), 
                            'E': latest_record.get('E')
                        }
                        
                        if any(pd.notna(new_record.get(c)) for c in ['A', 'B', 'C', 'D']):
                            print(f"Processing past year {year}: Using cumulative data up to Q{latest_quarter} (Q4 not available)")
                            result_data.append(new_record)
        
        result_df = pd.DataFrame(result_data)
        if not result_df.empty:
            result_df = result_df.sort_values('date')
        
        print(f"Final result: {len(result_df)} annual records processed")
        return result_df

    def _analyze_data(self, raw_data, stock_code):
        """Analyze cash flow data"""
        df = pd.DataFrame(raw_data)
        
        # Corrected field mapping - using correct FinMind column names
        mapping = {
            'A': [
                'CashFlowsFromOperatingActivities', 
                'NetCashInflowFromOperatingActivities',
                'Operating Activities Cash Flow'
            ],
            'B': [
                'CashProvidedByInvestingActivities',  # Correct column name
                'CashFlowsFromInvestingActivities',   # Backup
                'Investment Activities Cash Flow'
            ],
            'C': [
                'CashFlowsProvidedFromFinancingActivities',  # Correct column name
                'CashFlowsFromFinancingActivities',          # Backup
                'Financing Activities Cash Flow'
            ],
            'D': [
                'NetIncomeBeforeTax',
                'IncomeBeforeIncomeTaxFromContinuingOperations',
                'Pre-tax Net Income'
            ],
            'E': [
                'CashBalancesEndOfPeriod',
                'CashAndEquivalents',
                'Cash and Cash Equivalents'
            ]
        }
        
        # Convert to analysis format
        processed_data = []
        for date, group in df.groupby('date'):
            date_obj = pd.to_datetime(date)  # 確保是 datetime 對象
            record = {
                'date': date_obj, 
                'stock_code': stock_code,
                'year': date_obj.year,  # 添加年份
                'quarter': date_obj.quarter  # 添加季度
            }
            
            for field, names in mapping.items():
                value = None
                for name in names:
                    matches = group[group['type'].str.contains(name, na=False, case=False)]
                    if not matches.empty:
                        value = matches['value'].iloc[0]
                        break
                record[field] = value
            
            processed_data.append(record)
        
        # Apply 6 analysis rules
        analysis_df = pd.DataFrame(processed_data)
        # date, year, quarter 已經在 processed_data 中正確設置
        analysis_df = analysis_df.sort_values('date')
        
        # Key: Convert to annual data
        analysis_df = self._convert_to_annual(analysis_df)
        
        rules_result = self._apply_rules(analysis_df)
        summary = self._generate_summary(analysis_df, rules_result)
        
        return {
            "rules_analysis": rules_result,
            "summary": summary,
            "data_points": len(analysis_df),
            "latest_date": analysis_df['date'].max().strftime('%Y-%m-%d') if not analysis_df.empty else None,
            "note": "已轉換為年度累計資料（過去5年）"
        }
    
    def _apply_rules(self, df):
        """Apply 6 analysis rules based on original specifications"""
        results = {}
        
        if df.empty:
            return {"error": "No data available for analysis"}
        
        # Rule 1: A是否逐年增加 (Operating cash flow year-over-year growth)
        valid_a = df[df['A'].notna()].sort_values('date')['A']
        if len(valid_a) >= 2:
            increases = sum(valid_a.iloc[i] > valid_a.iloc[i-1] for i in range(1, len(valid_a)))
            total_periods = len(valid_a) - 1
            growth_ratio = increases / total_periods if total_periods > 0 else 0
            
            if growth_ratio >= 0.7:
                results['operating_growth'] = {
                    'status': 'GOOD', 'score': 3,
                    'description': f'營運現金流成長良好 ({growth_ratio:.1%} 期間成長)'
                }
            elif growth_ratio >= 0.4:
                results['operating_growth'] = {
                    'status': 'AVERAGE', 'score': 2,
                    'description': f'營運現金流成長不穩定 ({growth_ratio:.1%} 期間成長)'
                }
            else:
                results['operating_growth'] = {
                    'status': 'POOR', 'score': 1,
                    'description': f'營運現金流呈下降趨勢 ({growth_ratio:.1%} 期間成長)'
                }
        
        # Rule 2: B以負值為優，且B的絕對值小於A比較好
        valid_ab = df[(df['A'].notna()) & (df['B'].notna())]
        if not valid_ab.empty:
            negative_ratio = (valid_ab['B'] < 0).mean()  # 負值比例
            reasonable_ratio = (valid_ab['B'].abs() <= valid_ab['A']).mean()  # |B| <= A 的比例
            positive_count = (valid_ab['B'] > 0).sum()  # 正值次數
            
            if negative_ratio >= 0.8 and reasonable_ratio >= 0.7:
                results['investment_discipline'] = {
                    'status': 'GOOD', 'score': 3,
                    'description': f'投資紀律良好 (負值比例: {negative_ratio:.1%}, 合理投資比例: {reasonable_ratio:.1%})'
                }
            elif negative_ratio >= 0.6 and positive_count <= 2:
                results['investment_discipline'] = {
                    'status': 'AVERAGE', 'score': 2,
                    'description': f'投資紀律尚可 (負值比例: {negative_ratio:.1%}, {positive_count}次正值)'
                }
            else:
                results['investment_discipline'] = {
                    'status': 'POOR', 'score': 1,
                    'description': f'投資紀律需改善 (負值比例: {negative_ratio:.1%}, {positive_count}次正值)'
                }
        
        # Rule 3: B如果為負值，則A是否也會增加 (Investment effectiveness)
        valid_ab_sorted = df[(df['A'].notna()) & (df['B'].notna())].sort_values('date')
        if len(valid_ab_sorted) >= 2:
            investment_effectiveness_count = 0
            total_investment_periods = 0
            
            for i in range(1, len(valid_ab_sorted)):
                current_b = valid_ab_sorted.iloc[i]['B']
                current_a = valid_ab_sorted.iloc[i]['A']
                prev_a = valid_ab_sorted.iloc[i-1]['A']
                
                # 如果當期B為負值（有投資），檢查下期A是否增加
                if current_b < 0:
                    total_investment_periods += 1
                    if current_a > prev_a:
                        investment_effectiveness_count += 1
            
            if total_investment_periods > 0:
                effectiveness_ratio = investment_effectiveness_count / total_investment_periods
                
                if effectiveness_ratio >= 0.7:
                    results['investment_effectiveness'] = {
                        'status': 'GOOD', 'score': 3,
                        'description': f'投資效益良好 ({effectiveness_ratio:.1%} 投資期間帶動營運現金流成長)'
                    }
                elif effectiveness_ratio >= 0.4:
                    results['investment_effectiveness'] = {
                        'status': 'AVERAGE', 'score': 2,
                        'description': f'投資效益普通 ({effectiveness_ratio:.1%} 投資期間帶動營運現金流成長)'
                    }
                else:
                    results['investment_effectiveness'] = {
                        'status': 'POOR', 'score': 1,
                        'description': f'投資效益不佳 ({effectiveness_ratio:.1%} 投資期間帶動營運現金流成長)'
                    }
        
        # Rule 4: 檢查C的合理性，特別關注B負值且大時C為正值的情況
        valid_bc = df[(df['B'].notna()) & (df['C'].notna())]
        if not valid_bc.empty:
            c_negative_ratio = (valid_bc['C'] < 0).mean()  # C負值比例（正常）
            
            # 檢查風險情況：B負值且絕對值大，同時C正值（可能借錢投資）
            risky_periods = 0
            for _, row in valid_bc.iterrows():
                b_val = row['B']
                c_val = row['C']
                # B負值且絕對值大（超過100億），C正值
                if b_val < -1e10 and c_val > 0:
                    risky_periods += 1
            
            risk_ratio = risky_periods / len(valid_bc)
            
            if c_negative_ratio >= 0.6 and risk_ratio <= 0.2:
                results['financing_reasonableness'] = {
                    'status': 'GOOD', 'score': 3,
                    'description': f'融資活動合理 (C負值比例: {c_negative_ratio:.1%}, 風險期間: {risk_ratio:.1%})'
                }
            elif c_negative_ratio >= 0.4 and risk_ratio <= 0.4:
                results['financing_reasonableness'] = {
                    'status': 'AVERAGE', 'score': 2,
                    'description': f'融資活動尚可 (C負值比例: {c_negative_ratio:.1%}, 風險期間: {risk_ratio:.1%})'
                }
            else:
                results['financing_reasonableness'] = {
                    'status': 'POOR', 'score': 1,
                    'description': f'融資活動需注意 (C負值比例: {c_negative_ratio:.1%}, 可能借錢投資: {risk_ratio:.1%})'
                }
        
        # Rule 5: 原則上，A>D較為佳 (Cash flow quality)
        valid_ad = df[(df['A'].notna()) & (df['D'].notna())]
        if not valid_ad.empty:
            better_ratio = (valid_ad['A'] > valid_ad['D']).mean()
            
            if better_ratio >= 0.8:
                results['cashflow_quality'] = {
                    'status': 'GOOD', 'score': 3,
                    'description': f'現金流品質優秀 ({better_ratio:.1%} 期間A>D)'
                }
            elif better_ratio >= 0.5:
                results['cashflow_quality'] = {
                    'status': 'AVERAGE', 'score': 2,
                    'description': f'現金流品質一般 ({better_ratio:.1%} 期間A>D)'
                }
            else:
                results['cashflow_quality'] = {
                    'status': 'POOR', 'score': 1,
                    'description': f'現金流品質不佳 ({better_ratio:.1%} 期間A>D)'
                }
        
        # Rule 6: 期末餘額增加或穩定
        valid_e = df[df['E'].notna()].sort_values('date')['E']
        if len(valid_e) >= 2:
            # 計算期末餘額變化趨勢
            increases = sum(valid_e.iloc[i] >= valid_e.iloc[i-1] for i in range(1, len(valid_e)))
            stability_ratio = increases / (len(valid_e) - 1)
            
            # 計算總體成長率
            total_growth = (valid_e.iloc[-1] - valid_e.iloc[0]) / valid_e.iloc[0] if valid_e.iloc[0] != 0 else 0
            
            if stability_ratio >= 0.7 and total_growth >= 0:
                results['cash_stability'] = {
                    'status': 'GOOD', 'score': 3,
                    'description': f'現金餘額穩定成長 (穩定比例: {stability_ratio:.1%}, 總成長: {total_growth:.1%})'
                }
            elif stability_ratio >= 0.5 and total_growth >= -0.2:
                results['cash_stability'] = {
                    'status': 'AVERAGE', 'score': 2,
                    'description': f'現金餘額基本穩定 (穩定比例: {stability_ratio:.1%}, 總成長: {total_growth:.1%})'
                }
            else:
                results['cash_stability'] = {
                    'status': 'POOR', 'score': 1,
                    'description': f'現金餘額不穩定 (穩定比例: {stability_ratio:.1%}, 總成長: {total_growth:.1%})'
                }
        
        return results
    
    def _generate_summary(self, df, rules):
        """Generate analysis summary"""
        if df.empty:
            return "無法生成分析摘要"
        
        latest = df.iloc[-1]
        total_score = sum(r.get('score', 0) for r in rules.values())
        max_score = len(rules) * 3
        
        summary = f"""
現金流分析報告 - {latest.get('stock_code', 'N/A')} (年度累計)

整體評分: {total_score}/{max_score} ({total_score/max_score*100:.1f}%)

最新資料 (億台幣):
• 營運現金流: {(latest.get('A') or 0)/1e8:.1f}
• 投資現金流: {(latest.get('B') or 0)/1e8:.1f}
• 融資現金流: {(latest.get('C') or 0)/1e8:.1f}
• 稅前淨利: {(latest.get('D') or 0)/1e8:.1f}
• 現金餘額: {(latest.get('E') or 0)/1e8:.1f}

分析結果:
"""
        for key, result in rules.items():
            summary += f"• {result['status']}: {result['description']}\n"
        
        # Investment recommendation
        if total_score >= max_score * 0.8:
            summary += "\n投資建議: 現金流狀況優秀，值得關注"
        elif total_score >= max_score * 0.6:
            summary += "\n投資建議: 現金流狀況一般，需持續觀察"
        else:
            summary += "\n投資建議: 現金流狀況不佳，需謹慎評估"
        
        return summary

# Create analyzer instance
analyzer = CashFlowAnalyzer()

@app.route('/')
def home():
    """API Homepage"""
    return jsonify({
        "message": "現金流分析 API (支持年度累計資料)",
        "version": "1.2",
        "usage": "/analyze/<stock_code>"
    })

@app.route('/analyze/<stock_code>')
def analyze_stock(stock_code):
    """Analyze cash flow for specified stock"""
    if not stock_code or len(stock_code) < 4:
        return jsonify({"success": False, "error": "無效的股票代碼"}), 400
    
    result = analyzer.analyze_stock(stock_code)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/raw-data/<stock_code>')
def get_raw_data(stock_code):
    """Get raw data for AI analysis (Annual Cumulative Data)"""
    if not stock_code or len(stock_code) < 4:
        return jsonify({"success": False, "error": "無效的股票代碼"}), 400
    
    try:
        print(f"開始取得 {stock_code} 的原始資料...")
        
        # Use existing method to fetch data
        raw_data = analyzer._fetch_cashflow_data(stock_code)
        
        if not raw_data:
            return jsonify({"success": False, "error": "無法取得現金流資料"}), 500
        
        # Process into simple understandable format
        df = pd.DataFrame(raw_data)
        
        # Corrected 5 field mapping - using correct FinMind column names
        target_fields = {
            'CashFlowsFromOperatingActivities': '營運活動現金流',
            'CashProvidedByInvestingActivities': '投資活動現金流',
            'CashFlowsProvidedFromFinancingActivities': '融資活動現金流',
            'NetIncomeBeforeTax': '稅前淨利',
            'CashBalancesEndOfPeriod': '期末現金餘額'
        }
        
        # Convert to analysis format
        processed_data = []
        for date, group in df.groupby('date'):
            record = {
                'date': date,
                'year': pd.to_datetime(date).year,
                'quarter': f"Q{pd.to_datetime(date).quarter}",
                'stock_code': stock_code
            }
            
            # Find value for each item
            for eng_name, chi_name in target_fields.items():
                value = None
                # First find English name
                exact_match = group[group['type'] == eng_name]
                if not exact_match.empty:
                    value = exact_match['value'].iloc[0]
                else:
                    # Then find containing keywords
                    fuzzy_match = group[group['type'].str.contains(eng_name, na=False, case=False)]
                    if not fuzzy_match.empty:
                        value = fuzzy_match['value'].iloc[0]
                
                record[eng_name] = value
                record[f"{eng_name}_display"] = f"{value/1e8:.1f}億" if value else "無資料"
            
            processed_data.append(record)
        
        # Convert to DataFrame and process annual data
        temp_df = pd.DataFrame(processed_data)
        temp_df['date'] = pd.to_datetime(temp_df['date'])
        temp_df = temp_df.sort_values('date')
        
        # Rename columns
        temp_df = temp_df.rename(columns={
            'CashFlowsFromOperatingActivities': 'A',
            'CashProvidedByInvestingActivities': 'B', 
            'CashFlowsProvidedFromFinancingActivities': 'C',
            'NetIncomeBeforeTax': 'D',
            'CashBalancesEndOfPeriod': 'E'
        })
        
        # Convert to annual data
        annual_df = analyzer._convert_to_annual(temp_df)
        
        # Convert back to output format
        simple_data = []
        for _, row in annual_df.iterrows():
            # 確保 quarter 是字串格式
            quarter_value = row['quarter']
            if hasattr(quarter_value, 'quarter'):  # 如果是 datetime 對象
                quarter_str = f"Q{quarter_value.quarter}"
            else:
                quarter_str = str(quarter_value)  # 直接轉為字串
                
            record = {
                'date': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date']),
                'year': int(row['year']) if pd.notna(row['year']) else None,
                'quarter': quarter_str,
                'CashFlowsFromOperatingActivities': row['A'],
                'CashProvidedByInvestingActivities': row['B'],
                'CashFlowsProvidedFromFinancingActivities': row['C'],
                'NetIncomeBeforeTax': row['D'],
                'CashBalancesEndOfPeriod': row['E']
            }
            
            # Add display format
            for field in ['CashFlowsFromOperatingActivities', 'CashProvidedByInvestingActivities', 
                         'CashFlowsProvidedFromFinancingActivities', 'NetIncomeBeforeTax', 
                         'CashBalancesEndOfPeriod']:
                value = record[field]
                record[f"{field}_display"] = f"{value/1e8:.1f}億" if pd.notna(value) else "無資料"
            
            simple_data.append(record)
        
        return jsonify({
            "success": True,
            "stock_code": stock_code,
            "data_points": len(simple_data),
            "time_range": f"{simple_data[0]['date']} 到 {simple_data[-1]['date']}" if simple_data else "無資料",
            "financial_data": simple_data,
            "fields_explanation": {
                "CashFlowsFromOperatingActivities": "A-營運現金流: 日常經營產生的現金 (年度累計)",
                "CashProvidedByInvestingActivities": "B-投資現金流: 買賣設備投資的現金流 (年度累計)", 
                "CashFlowsProvidedFromFinancingActivities": "C-融資現金流: 借貸還債發股利的現金流 (年度累計)",
                "NetIncomeBeforeTax": "D-稅前淨利: 公司賺了多少錢 (年度累計)",
                "CashBalancesEndOfPeriod": "E-期末現金餘額: 期末的現金存量"
            },
            "note": "已轉換為年度累計資料（過去5年）",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/explore-data/<stock_code>')
def explore_data_structure(stock_code):
    """探索原始資料結構，確認是否有累計資料"""
    if not stock_code or len(stock_code) < 4:
        return jsonify({"success": False, "error": "無效的股票代碼"}), 400
    
    try:
        raw_data = analyzer._fetch_cashflow_data(stock_code)
        
        if not raw_data:
            return jsonify({"success": False, "error": "無法取得資料"}), 500
        
        df = pd.DataFrame(raw_data)
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df['quarter'] = df['date'].dt.quarter
        
        # 分析最近一年的資料
        recent_year = int(df['year'].max())  # 轉換為Python int
        recent_data = df[df['year'] == recent_year]
        
        analysis = {"year": recent_year, "quarters": {}}
        operating_cf_values = []
        
        for quarter in sorted(recent_data['quarter'].unique()):
            q_data = recent_data[recent_data['quarter'] == quarter]
            
            # 找營運現金流
            operating_cf = None
            for _, row in q_data.iterrows():
                if 'CashFlowsFromOperatingActivities' in row['type']:
                    operating_cf = row['value']
                    break
            
            # 確保數值可以JSON序列化
            operating_cf_display = f"{operating_cf/1e8:.1f}" if operating_cf else "無資料"
            
            analysis["quarters"][f"Q{int(quarter)}"] = {  # 轉換為Python int
                "date": q_data['date'].iloc[0].strftime('%Y-%m-%d'),
                "operating_cf": float(operating_cf) if operating_cf is not None else None,  # 轉換為Python float
                "operating_cf_億": operating_cf_display
            }
            
            if operating_cf is not None:
                operating_cf_values.append(float(operating_cf))  # 轉換為Python float
        
        # 判斷資料性質
        if len(operating_cf_values) >= 2:
            is_increasing = all(operating_cf_values[i] >= operating_cf_values[i-1] for i in range(1, len(operating_cf_values)))
            analysis["data_assessment"] = {
                "appears_cumulative": bool(is_increasing),  # 轉換為Python bool
                "conclusion": "累計資料" if is_increasing else "季度差額資料",
                "recommendation": "可以直接使用累計邏輯" if is_increasing else "需要將季度資料累加",
                "value_trend": "遞增趨勢" if is_increasing else "波動趨勢"
            }
        else:
            analysis["data_assessment"] = {
                "appears_cumulative": None,
                "conclusion": "資料不足以判斷",
                "recommendation": "需要更多季度資料來分析",
                "value_trend": "資料不足"
            }
        
        # 顯示可用欄位（限制數量避免回應過大）
        analysis["available_types_sample"] = sorted(df['type'].unique().tolist())[:10]
        analysis["total_types_count"] = int(len(df['type'].unique()))  # 轉換為Python int
        
        return jsonify({
            "success": True,
            "stock_code": stock_code,
            "total_data_points": int(len(df)),  # 轉換為Python int
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/data-range/<stock_code>')
def check_data_range(stock_code):
    """Check data range for specified stock"""
    if not stock_code or len(stock_code) < 4:
        return jsonify({"success": False, "error": "無效的股票代碼"}), 400
    
    try:
        # Fetch raw data
        raw_data = analyzer._fetch_cashflow_data(stock_code)
        
        if not raw_data:
            return jsonify({"success": False, "error": "無法取得現金流資料"}), 500
        
        df = pd.DataFrame(raw_data)
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df['quarter'] = df['date'].dt.quarter
        
        # Analyze data range for annual processing
        date_range = df.groupby(['year', 'quarter']).first()['date'].reset_index()
        date_range = date_range.sort_values(['year', 'quarter'])
        
        current_year = datetime.now().year
        annual_analysis = []
        usable_years = []
        
        # 檢查過去5年的資料可用性
        for year in range(current_year - 4, current_year + 1):
            year_data = df[df['year'] == year]
            if not year_data.empty:
                available_quarters = sorted(year_data['quarter'].unique())
                
                if year == current_year:
                    # 今年使用最新可用的累計資料
                    latest_quarter = max(available_quarters)
                    status = f"可用 - 累計至Q{latest_quarter}"
                    usable_years.append({
                        'year': year,
                        'type': f"累計至Q{latest_quarter}",
                        'quarters_available': available_quarters,
                        'can_use': True
                    })
                else:
                    # 過去年份優先使用Q4，沒有則用最新季度
                    if 4 in available_quarters:
                        status = "可用 - 全年累計(Q4)"
                        quarter_type = "全年累計"
                    else:
                        latest_quarter = max(available_quarters)
                        status = f"可用 - 累計至Q{latest_quarter}"
                        quarter_type = f"累計至Q{latest_quarter}"
                    
                    usable_years.append({
                        'year': year,
                        'type': quarter_type,
                        'quarters_available': available_quarters,
                        'can_use': True
                    })
                
                annual_analysis.append({
                    'year': year,
                    'available_quarters': available_quarters,
                    'status': status,
                    'can_use': True
                })
            else:
                annual_analysis.append({
                    'year': year,
                    'available_quarters': [],
                    'status': "無資料",
                    'can_use': False
                })
        
        return jsonify({
            "success": True,
            "stock_code": stock_code,
            "processing_method": "年度累計資料（過去5年）",
            "raw_data_points": len(date_range),
            "usable_years": len(usable_years),
            "year_breakdown": annual_analysis,
            "usable_year_list": [y['year'] for y in usable_years],
            "data_range": {
                "start_year": current_year - 4,
                "end_year": current_year,
                "total_years": 5
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    # Zeabur will automatically set PORT environment variable
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)