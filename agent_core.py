from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
import json, re, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/"data"/"agent_config.json").read_text(encoding="utf-8"))

def citation(title="待核验标准",version="待确认",clause="待定位",quote="未找到可定位原文",doc_id="pending"):
    return {"document_id":doc_id,"title":title,"version":version,"page_or_clause":clause,"quoted_text":quote,"retrieved_at":datetime.now(timezone.utc).isoformat(),"status":"待确认"}

def base_output(task,summary):
    return {"agent_name":CFG["name"],"task_type":task,"summary":summary,"analysis_steps":[],"evidence_items":[],"citations":[],"uncertainties":[],"risk_flags":[],"questions_for_student":[],"recommended_actions":[],"student_deliverable_template":CFG["deliverable"],"confidence":0.55,"session_id":str(uuid.uuid4())}

def split_ingredients(text):
    text=re.sub(r"配料[:：]", "", text or "")
    parts=re.split(r"[，,、;；](?![^（(]*[）)])",text)
    return [p.strip() for p in parts if p.strip()]

def normalize_unit(value,unit):
    factors={"kg":1,"g":1e-3,"mg":1e-6,"μg":1e-9,"ug":1e-9,"L":1,"mL":1e-3}
    if unit not in factors: raise ValueError("不支持的单位")
    return float(value)*factors[unit]

def edi(concentration_mgkg,intake_gday,weight_kg):
    if weight_kg<=0 or intake_gday<0 or concentration_mgkg<0: raise ValueError("输入必须为合理非负值，体重必须大于0")
    return concentration_mgkg*(intake_gday/1000)/weight_kg

def standard_search(additive,food):
    path=ROOT/"data"/"gb2760_catalog.json"
    if not path.exists(): return []
    raw=json.loads(path.read_text(encoding="utf-8")); rows=raw.get("records",raw) if isinstance(raw,dict) else raw
    hits=[]
    for row in rows:
        blob=json.dumps(row,ensure_ascii=False)
        if additive and additive.lower() not in blob.lower(): continue
        if food and food.lower() not in blob.lower(): continue
        hits.append(row)
        if len(hits)>=8: break
    return hits

def classify_ingredient(name):
    maps={"防腐剂":["苯甲酸","山梨酸","脱氢乙酸"],"甜味剂":["赤藓糖醇","三氯蔗糖","甜菊"],"增稠剂":["卡拉胶","黄原胶","果胶"],"着色剂":["柠檬黄","日落黄","胭脂红"],"营养强化剂":["维生素","乳酸钙","葡萄糖酸锌"],"食品原料":["水","糖","面粉","牛奶","果汁","食盐"]}
    for cat,words in maps.items():
        if any(w in name for w in words): return cat,0.9
    if "复配" in name:return "复配食品添加剂（需展开子配料）",0.75
    return "待确认",0.35

def analyze(payload):
    kind=CFG["key"]; question=str(payload.get("question","")).strip(); product=payload.get("product_info") or {}; ingredients=payload.get("ingredient_list") or question
    out=base_output(payload.get("task_type",kind),"")
    if kind=="standard":
        additive=payload.get("additive") or product.get("additive") or ""; food=product.get("food_category") or product.get("name") or ""
        missing=[x for x,v in [("产品/食品类别",food),("添加剂名称",additive)] if not v]
        hits=standard_search(additive,food)
        out.update(summary="已完成结构化标准检索；最终结论须由学生定位条款并由教师复核。",analysis_steps=["检查输入完整性","生成食品分类候选","检索结构化目录","核验版本与引用"],uncertainties=missing,questions_for_student=[f"请补充{x}" for x in missing],confidence=0.8 if hits else 0.35)
        out["food_category_candidates"]=[{"category":food or "待确认","support":"依据产品名称形成初始候选","against":"尚缺加工方式和主要原料"}]
        out["standard_hits"]=hits; out["citations"]=[citation("GB 2760", "2024/以目录版本为准", "目录命中记录", json.dumps(h,ensure_ascii=False)[:220],str(i+1)) for i,h in enumerate(hits)]
    elif kind=="ingredient":
        items=[]
        for x in split_ingredients(str(ingredients)):
            cat,conf=classify_ingredient(x); items.append({"original_name":x,"normalized_name":x,"category_label":cat,"functional_role":"需结合产品和标准核验","basis":"词典初判，不作为违法结论","confidence":conf,"student_revision":""})
        claims=[w for w in ["零添加","纯天然","无防腐剂","不含化学成分"] if w in question]
        out.update(summary=f"已拆分{len(items)}个成分；不确定项需学生核对标签和标准。",analysis_steps=["文本清洗","括号感知切分","实体归一","身份初判","宣传风险检查"],confidence=0.75 if items else 0.2)
        out["ingredient_items"]=items; out["claim_risks"]=[{"claim":x,"risk":"绝对化表达，需结合完整标签与法规核验"} for x in claims]; out["questions_for_student"]=["哪些成分属于复配配料并需要展开子配料？","哪些判断必须转交食添标准通核验？"]
    elif kind=="risk":
        vals=payload.get("parameters") or {}; required=["concentration_mgkg","food_intake_gday","body_weight_kg"]
        missing=[x for x in required if vals.get(x) in (None,"")]
        out.update(summary="课堂简化暴露计算，不等同正式监管风险评估。",analysis_steps=["核对参数与单位","确定性计算EDI","与ADI比较","说明假设与局限"],uncertainties=missing)
        if not missing:
            result=edi(float(vals["concentration_mgkg"]),float(vals["food_intake_gday"]),float(vals["body_weight_kg"])); adi_val=vals.get("adi_mgkg_bw_day")
            out["risk_calculation"]={"formula":"EDI=浓度×每日摄入量/体重","edi_mgkg_bw_day":round(result,6),"edi_adi_ratio":None if not adi_val else round(result/float(adi_val),4),"inputs":vals}; out["confidence"]=0.9
        out["questions_for_student"]=["这些输入是实测数据、文献数据还是教学假设？","一次摄入和长期平均摄入有何区别？"]
    elif kind=="formulation":
        weights=(payload.get("parameters") or {}).get("weights",{"effect":0.3,"compliance":0.25,"cost":0.15,"process":0.15,"sensory":0.15})
        options=[("单一添加剂路径",{"effect":75,"compliance":80,"cost":85,"process":80,"sensory":75}),("复配添加剂路径",{"effect":88,"compliance":72,"cost":65,"process":76,"sensory":85}),("添加剂+工艺+包装路径",{"effect":92,"compliance":90,"cost":58,"process":68,"sensory":88})]
        ranked=[]
        for name,scores in options: ranked.append({"option":name,"scores":scores,"weighted_score":round(sum(scores.get(k,0)*float(v) for k,v in weights.items()),2),"regulatory_status":"待食添标准通核验","validation_plan":"开展小试、感官、稳定性与货架期验证"})
        ranked.sort(key=lambda x:x["weighted_score"],reverse=True)
        out.update(summary="已生成3条候选路径；排序用于课堂决策，不是唯一配方。",analysis_steps=["澄清设计目标","生成候选","法规硬约束预留","加权评分","形成验证计划"],confidence=0.7)
        out["candidate_options"]=ranked; out["decision_matrix"]={"weights":weights,"ranking":ranked}; out["questions_for_student"]=["改变合规或成本权重后排序是否变化？","你准备如何用最小实验区分前三个方案？"]
    elif kind=="evidence":
        report=question; claims=[x.strip() for x in re.split(r"[。！？\n]",report) if x.strip()]
        findings=[]
        for c in claims:
            flags=[]
            if any(w in c for w in ["一定安全","绝对安全","检出即超标","天然一定"]): flags.append("绝对化或逻辑跳跃")
            if any(w in c for w in ["标准规定","最大使用量","限量"]) and not re.search(r"GB\s*\d+|条|表",c): flags.append("法规主张缺可定位引用")
            findings.append({"claim":c,"claim_type":"法规/科学/建议待分类","citation_quality":"不足" if flags else "待核验","logic_check":flags,"severity":"D" if flags else "X","required_revision":"补充可定位证据并限定结论范围"})
        out.update(summary=f"已拆分并审计{len(findings)}条主张。",analysis_steps=["原子化主张","主张分类","引用匹配","逻辑与幻觉检查","生成修订任务"],confidence=0.75)
        out["claims"]=findings; out["overall_audit_grade"]="D" if any(x["severity"]=="D" for x in findings) else "X"; out["risk_flags"]=[f for x in findings for f in x["logic_check"]]
    else:
        work=question; task=payload.get("assignment_type","合规判定报告"); rubrics=CFG["rubrics"].get(task,CFG["rubrics"]["default"]); scores=[]
        for dim,w in rubrics.items():
            evidence=20 if any(k in work for k in ["GB","证据","因为","依据","版本","修订"]) else 12
            score=min(100,45+evidence+min(len(work)//20,25)); scores.append({"dimension":dim,"weight":w,"score":score,"weighted":round(score*w,2),"evidence_quote":work[:80] or "未提交可评价文本"})
        total=round(sum(x["weighted"] for x in scores),2)
        out.update(summary=f"形成性评价完成，当前加权得分{total}；最终成绩由教师确认。",analysis_steps=["识别任务与版本","加载专用量规","提取证据片段","形成修订清单"],confidence=0.7)
        out["dimension_scores"]=scores; out["overall_level"]="良好" if total>=75 else "待修订"; out["priority_revisions"]=["补充可定位标准或科学证据","说明AI使用、人工核验和版本修订过程"]; out["resubmission_checklist"]=["逐条回应反馈","标注新增证据","保留前后版本"]
    out["evidence_items"]=[{"type":"learning_trace","student_original":question,"agent_prompt":"依据不足处已转为追问","student_revision":"待学生填写","final_conclusion":"待教师复核"}]
    return out
