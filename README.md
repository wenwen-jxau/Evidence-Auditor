# 证据链审计官

AI答案、学生结论与合规报告证据核验智能体

## 功能

主张拆分、引用匹配、计算复核与幻觉标记。采用“任务识别→信息补全→检索/计算→初步结果→证据核验→教学追问→结构化输出”流程。默认不替学生生成可直接提交的终稿。

## 启动界面

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 启动API

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

## 测试

```bash
python -m unittest discover -s tests -v
```

## 数据与合规边界

演示数据不含真实学生身份。法规、限量、分类和安全结论必须回到现行标准原文或权威资料复核；无命中或信息不足时输出“不确定”。
