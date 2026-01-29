from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError, field_validator
import json
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.json.ensure_ascii = False



try:
    with open("products.json", "r", encoding="utf-8") as f:
        products = json.load(f)
        print(f"加载{len(products)}个产品")

except Exception as e:
    print(f"加载产品数据失败: {str(e)}")
    products = []

#sqlite数据库配置
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "SQLALCHEMY_DATABASE_URI",
    "sqlite:///app.db"  # 本地启动时的默认路径
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Submission表
class Submission(db.Model):
    __tablename__ = 'submission'
    id = db.Column(db.Integer, primary_key=True)
    answers = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    def __repr__(self):
        return f"<Submission {self.id}>"

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    report_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    def __repr__(self):
        return f"<Report {self.id}>"

with app.app_context():
    db.create_all()
    print("数据库表已创建")



#1. 评分函数，未进行修改
def calculate_scores(answers: dict) -> dict:
    annual_invoice = float(answers.get("annual_invoice", 0))
    annual_flow = float(answers.get("annual_flow", 0))
    has_mortgage = bool(answers.get("has_mortgage", False))
    overdue_level = answers.get("overdue_level", "none")
    scores = {}
    scores["tax"] = min(100, int(annual_invoice / 500 * 100))
    scores["flow"] = min(100, int(annual_flow / 1000 * 100))
    scores["mortgage"] = 80 if has_mortgage else 0
    credit_map = {"none": 100, "M1": 60, "M3+": 0}
    scores["credit"] = credit_map.get(overdue_level, 50)
    print("分数情况：", scores)
    return scores


#2.产品匹配函数（Top3）,未进行修改
def match_products(scores: dict, products: list) -> list:
    matched = []
    for p in products:
        req = p.get("requirements", {})
        if all([
            scores.get("tax", 0) >= req.get("min_tax_score", 0),
            scores.get("credit", 0) >= req.get("min_credit_score", 0),
            scores.get("mortgage", 0) >= req.get("min_mortgage_score", 0)
        ]):
            matched.append(p)
    matched.sort(key=lambda x: x.get("max_amount", 0), reverse=True)
    print("匹配的产品：", [p['name'] for p in matched[:3]])
    return matched[:3]

"""
3. 可贷区间，进行简单逻辑修改:根据分数决定可贷区间
可贷区间最终应当与products.json中的产品匹配，但目前先用简单逻辑代替
"""
def calc_loan_range(scores: dict):
    score_values = list(scores.values())
    avg_score = sum(score_values) / len(score_values)

    if avg_score >= 80:
        max_amount = 500
    elif avg_score >= 60:
        max_amount = 350
    elif avg_score >= 40:
        max_amount = 200
    else:
        max_amount = 100

    return {"min": 50, "max": max_amount}

"""
4. 改造方案 A/B/C:
a.给出三个方案为固定方案
b.根据最低分维度，给出推荐的对应方案
tax分最低→优先A方案
flow最低→优先B方案
mortgage最低→优先C方案
c.后续可以添加查看更多方案的功能

"""
def get_reform_plans(scores: dict = None):

    base_plans = [
        {"plan": "A", "name": "开票提升术", "cost": {"min": 8, "max": 15}, "duration": {"min": 4, "max": 7},
         "roi": 900},
        {"plan": "B", "name": "纳税提升术", "cost": {"min": 5, "max": 10}, "duration": {"min": 3, "max": 6},
         "roi": 600},
        {"plan": "C", "name": "资质认定术", "cost": {"min": 10, "max": 20}, "duration": {"min": 6, "max": 12},
         "roi": 1200}
    ]

    # 找到分数最低的维度
    min_score_key = min(scores, key=scores.get)

    # 按最低分维度调整方案顺序
    if min_score_key == "tax":
        return [base_plans[0]]
    elif min_score_key == "flow":
        return [base_plans[1]]
    else:
        return [base_plans[2]]
# 5. 使用Pydantic定义请求参数校验模型
class AnswersModel(BaseModel):

    # 1. 定义字段 + 类型
    annual_invoice: float | int
    annual_flow: float | int
    has_mortgage: bool
    overdue_level: str

    # 2. 自定义字段校验器：校验非负
    @field_validator('annual_invoice', 'annual_flow')
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError(f"值必须是非负数，当前值：{v}")
        return v

    # 3. 自定义字段校验器：校验overdue_level的合法取值
    @field_validator('overdue_level')
    def validate_overdue_level(cls, v):
        valid_values = ["none", "M1", "M3+"]
        if v not in valid_values:
            raise ValueError(f"必须是{valid_values}中的一个，当前值：{v}")
        return v

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

@app.route("/api/report/preview", methods=["POST"])
def report_preview():
    # 获取请求体
    try:
        if not request.is_json:
            raise ValueError("请求体必须是JSON格式")
        answers = request.get_json()
        print(f"接收请求参数: {answers}")

        # 参数校验
        try:
            validated_answers = AnswersModel(**answers)  # 解包字典并校验
        except ValidationError as e:

            error_detail = e.errors()[0]
            error_msg = f"参数校验失败：{error_detail['loc'][0]} - {error_detail['msg']}"
            raise ValueError(error_msg)
        validated_answers_dict = validated_answers.model_dump()

        # 执行核心逻辑
        scores = calculate_scores(validated_answers_dict)
        products_matched = match_products(scores, products)
        loan_range = calc_loan_range(scores)

        plan = get_reform_plans(scores)

        products_need=[]

        for p in products_matched:
            products_need.append({
                "name":p["name"],
                "type":p["type"],
                "max_amount":p["max_amount"],
                "interest_rate":f"{p['interest_rate']['min']}%-{p['interest_rate']['max']}%"
            })


        # 构造响应
        response = {
            "scores": scores,
            "current_loan_range": loan_range,
            "recommended_products": products_need,
            "reform_plans": plan
        }

        print( response)
        response_json = json.dumps(response, ensure_ascii=False, indent=2)
        return app.response_class(response_json, content_type='application/json'), 200
    except ValueError as ve:
        print(f"参数错误: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"服务器内部错误: {str(e)}")
        return jsonify({"error": "服务器内部错误，请稍后重试"}), 500

"""
API 1：POST /api/submissions（保存answers）
入参为answers JSON，保存到Submission表，返回submission_id和结果
api 测试：curl -X POST http://localhost:5000/api/submissions -H "Content-Type: application/json" -d "{\"answers\":{\"annual_invoice\":300,\"annual_flow\":600,\"has_mortgage\":false,\"overdue_level\":\"none\"}}"
"""
@app.route('/api/submissions', methods=['POST'])
def create_submission_in():

    try:
        #字段检验
        if not request.is_json:
            raise ValueError("请求体必须是JSON格式")
        answer_json = request.get_json()

        if "answers" not in answer_json:
            raise ValueError("请求体必须包含'answers'字段")
        answers = answer_json["answers"]

        try:
            validated_answers = AnswersModel(**answers)  # 解包字典并校验
        except ValidationError as e:

            error_detail = e.errors()[0]
            error_msg = f"参数校验失败：{error_detail['loc'][0]} - {error_detail['msg']}"
            raise ValueError(error_msg)
        validated_answers_dict = validated_answers.model_dump()

        submission = Submission(answers=json.dumps(validated_answers_dict, ensure_ascii=False))

        db.session.add(submission)
        db.session.commit()
        db.session.query(Submission).all()
        print(f"保存Submission，ID: {submission.id}")
        return jsonify({"submission_id": submission.id, "message": "提交成功"}), 200

    except ValueError as ve:
        print(f"参数错误: {str(ve)}")
        return jsonify({"error": str(ve)}), 400

    except Exception as e:
        print(f"服务器内部错误: {str(e)}")
        return jsonify({"error": "服务器内部错误，请稍后重试"}), 500



"""
API 2：POST /api/reports/generate?submission_id=xxx（生成报告并保存）
入参为submission_id，读取对应Submission的answers，生成报告并保存到Report表，返回report_json
直接将原来的代码cv下来了，这段代码后续可以另写一个函数调用
api测试：curl -X POST "http://localhost:5000/api/reports/generate?submission_id=1"
"""
@app.route('/api/reports/generate', methods=['POST'])
def generate_report():
    try:
        submission_id = request.args.get('submission_id')
        #非空校验和整数校验
        if not submission_id:
            raise ValueError("缺少submission_id参数")
        try:
            submission_id = int(submission_id)
        except ValueError:
            raise ValueError("submission_id必须是整数")
        print(f"生成报告请求，submission_id: {submission_id}")

        submission = Submission.query.get(submission_id)
        if not submission:
            raise ValueError(f"未找到对应的Submission，ID: {submission_id}")

         # 以下代码直接cv test1的代码
        answers = json.loads(submission.answers)
        scores = calculate_scores(answers)
        products_matched = match_products(scores, products)
        loan_range = calc_loan_range(scores)
        plan = get_reform_plans(scores)
        products_need = []
        for p in products_matched:
            products_need.append({
                "name": p["name"],
                "type": p["type"],
                "max_amount": p["max_amount"],
                "interest_rate": f"{p['interest_rate']['min']}%-{p['interest_rate']['max']}%"
            })
        report = {
            "scores": scores,
            "current_loan_range": loan_range,
            "recommended_products": products_need,
            "reform_plans": plan
        }
        report_json = json.dumps(report, ensure_ascii=False)
        report_record = Report(submission_id=submission.id, report_json=report_json)
        db.session.add(report_record)
        db.session.commit()
        return jsonify({"report_id": report_record.id, "message": "报告生成成功"}), 200
    except ValueError as ve:
        print(f"参数错误: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"服务器内部错误: {str(e)}")
        return jsonify({"error": "服务器内部错误，请稍后重试"}), 500



"""
API 3：GET /api/reports/{id}（查询报告详情）
入参为report id，返回对应的report_json
api测试：curl -X GET http://localhost:5000/api/reports/1
"""
@app.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report(report_id):
    try:
        report = Report.query.get(report_id)
        if not report:
            return jsonify({"error": f"未找到对应的报告，ID: {report_id}"}), 404

        report_data = json.loads(report.report_json)
        response_json = json.dumps(report_data, ensure_ascii=False, indent=2)
        print(f"查询报告，ID: {report_id}")
        return app.response_class(response_json, content_type='application/json'), 200
    except Exception as e:
        print(f"服务器内部错误: {str(e)}")
        return jsonify({"error": "服务器内部错误，请稍后重试"}), 500
        return jsonify({"error": "服务器内部错误"}), 500


"""
管理接口实现：
API 4：GET /api/admin/submissions（查询所有提交记录）
API 5：GET /api/admin/reports（查询所有报告记录）
API 6：DELETE /api/admin/submissions/{id}（删除指定提交记录）
API 7：DELETE /api/admin/reports/{id}（删除指定报告记录）
api测试：
curl -X GET http://localhost:5000/api/admin/submissions
curl -X DELETE http://localhost:5000/api/admin/submissions/1
curl -X GET http://localhost:5000/api/admin/reports
curl -X DELETE http://localhost:5000/api/admin/reports/1

"""
@app.route('/api/admin/submissions', methods=['GET'])
def get_all_submissions():
    try:
        submissions = Submission.query.all()
        result = []
        for sub in submissions:
            answers_data = json.loads(sub.answers)
            print(answers_data)
            result.append({
                "id": sub.id,
                "answers": answers_data,
                "created_at": sub.created_at
            })
        return jsonify(result), 200
    except Exception as e:
        print(f"服务器内部错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500
@app.route('/api/admin/reports', methods=['GET'])
def get_all_reports():
    try:
        reports = Report.query.all()
        result = []
        for rep in reports:
            result.append({
                "id": rep.id,
                "submission_id": rep.submission_id,
                "report_json": json.loads(rep.report_json),
                "created_at": rep.created_at
            })
        return jsonify(result), 200
    except Exception as e:
        print(f"服务器内部错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500
@app.route('/api/admin/submissions/<int:submission_id>', methods=['DELETE'])
def delete_submission(submission_id):
    try:
        submission = Submission.query.get(submission_id)
        if not submission:
            return jsonify({"error": f"未找到对应的提交记录，ID: {submission_id}"}), 404
        Report.query.filter_by(submission_id=submission_id).delete()

        db.session.delete(submission)
        db.session.commit()
        return jsonify({"message": "提交记录删除成功"}), 200
    except Exception as e:
        print(f"服务器内部错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500
@app.route('/api/admin/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    try:
        report = Report.query.get(report_id)
        if not report:
            return jsonify({"error": f"未找到对应的报告记录，ID: {report_id}"}), 404
        db.session.delete(report)
        db.session.commit()
        return jsonify({"message": "报告记录删除成功"}), 200
    except Exception as e:
        print(f"服务器内部错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500




if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port,debug=False)