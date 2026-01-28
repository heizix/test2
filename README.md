# 后端测试2 - 报告预览接口
## 项目说明
实现题目要求的**POST /api/report/preview**单接口，基于Flask开发，无需数据库，返回用户贷款资质报告，包含评分、可贷区间、Top3匹配产品、A/B/C单个最优改造方案。

## 本地启动步骤
### 1. 环境准备
Python 3.11
### 2.文件结构
```
[贺小鹏]-后端测试1/
│
├── app.py
├── products.json
├── README.md
└── ai_playbook.md
``` 
### 3. 启动服务
在终端窗口，进入对应目录，执行以下命令启动Flask服务：
```
python app.py
```
### 4. 测试接口(CURL 测试命令)
新建终端窗口，执行以下命令：
```
curl -X POST "http://127.0.0.1:5000/api/report/preview" -H "Content-Type: application/json" -d "{\"annual_invoice\": 300, \"annual_flow\": 600, \"has_mortgage\": false, \"overdue_level\": \"none\"}"
```
### 5. 测试结果
flask端输出如下：
```
接收请求参数: {'annual_invoice': 300, 'annual_flow': 600, 'has_mortgage': False, 'overdue_level': 'none'}
分数情况： {'tax': 60, 'flow': 60, 'mortgage': 0, 'credit': 100}
匹配的产品： ['兴业供应链贷', '交行发票贷', '农行流水贷']
{'scores': {'tax': 60, 'flow': 60, 'mortgage': 0, 'credit': 100}, 'current_loan_range': {'min': 50, 'max': 200}, 'recommended_products': [{'name': '兴业供应链贷', 'type': '供应链贷', 'max_amount': 800, 'interest_rate': '3.8%-7.5%'}, {'name': '交行发票贷', 'type': '发票贷', 'max_amount': 500, 'interest_rate': '4.0%-9.0%'}, {'name': '农行流水贷', 'type': '流水贷', 'max_amount': 400, 'interest_rate': '4.2%-8.5%'}], 'reform_plans': [{'plan': 'C', 'name': '资质认定术', 'cost': {'min': 10, 'max': 20}, 'duration': {'min': 6, 'max': 12}, 'roi': 1200}]}
127.0.0.1 - - [27/Jan/2026 15:44:35] "POST /api/report/preview HTTP/1.1" 200 -
```
测试接口输出如下：
```
{
  "scores": {
    "tax": 60,
    "flow": 60,
    "mortgage": 0,
    "credit": 100
  },
  "current_loan_range": {
    "min": 50,
    "max": 200
  },
  "recommended_products": [
    {
      "name": "兴业供应链贷",
      "type": "供应链贷",
      "max_amount": 800,
      "interest_rate": "3.8%-7.5%"
    },
    {
      "name": "交行发票贷",
      "type": "发票贷",
      "max_amount": 500,
      "interest_rate": "4.0%-9.0%"
    },
    {
      "name": "农行流水贷",
      "type": "流水贷",
      "max_amount": 400,
      "interest_rate": "4.2%-8.5%"
    }
  ],
  "reform_plans": [
    {
      "plan": "C",
      "name": "资质认定术",
      "cost": {
        "min": 10,
        "max": 20
      },
      "duration": {
        "min": 6,
        "max": 12
      },
      "roi": 1200
    }
  ]
}
```