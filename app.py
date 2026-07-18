import json
from pathlib import Path
import streamlit as st
from agent_core import CFG, analyze
CN_KEYS={"agent_name":"智能体名称","task_type":"任务类型","summary":"结果摘要","analysis_steps":"分析步骤","evidence_items":"学习证据","citations":"引用依据","uncertainties":"不确定项","risk_flags":"风险提示","questions_for_student":"给学生的追问","recommended_actions":"建议行动","student_deliverable_template":"学生成果模板","confidence":"置信度","session_id":"会话编号","type":"类型","learning_trace":"学习轨迹","student_original":"学生原始判断","agent_prompt":"智能体提示","student_revision":"学生修订","final_conclusion":"最终结论","food_category_candidates":"食品分类候选","category":"类别","support":"支持理由","against":"反对理由","standard_hits":"标准检索结果","ingredient_items":"配料项目","original_name":"原始名称","normalized_name":"规范名称","category_label":"类别标注","functional_role":"技术作用","basis":"判断依据","claim_risks":"宣传表述风险","claim":"主张","risk":"风险","risk_calculation":"风险计算","formula":"计算公式","inputs":"输入参数","candidate_options":"候选方案","option":"方案","scores":"各项得分","weighted_score":"加权得分","regulatory_status":"法规状态","validation_plan":"验证计划","decision_matrix":"决策矩阵","weights":"指标权重","ranking":"排序","claims":"审计主张","claim_type":"主张类型","citation_quality":"引用质量","logic_check":"逻辑检查","severity":"严重程度","required_revision":"必须修改项","overall_audit_grade":"总体审计等级","dimension_scores":"分维度得分","dimension":"评价维度","weight":"权重","score":"得分","weighted":"加权分","evidence_quote":"证据片段","overall_level":"总体水平","priority_revisions":"优先修改项","resubmission_checklist":"再次提交清单","document_id":"文档编号","title":"标题","version":"版本","page_or_clause":"页码或条款","quoted_text":"引用原文","retrieved_at":"检索时间","status":"状态","student":"学生","teacher":"教师","admin":"管理员","pending":"待核验"}
def localize(value):
    if isinstance(value,dict): return {CN_KEYS.get(k,k):localize(v) for k,v in value.items()}
    if isinstance(value,list): return [localize(v) for v in value]
    if isinstance(value,str): return CN_KEYS.get(value,value)
    return value
st.set_page_config(page_title=CFG["name"],page_icon="🧪",layout="wide")
st.markdown("""<style>.block-container{padding-top:4.6rem;max-width:1200px}.hero{padding:24px;border-radius:14px;background:linear-gradient(135deg,#12334d,#0f766e);color:white;margin-bottom:18px;box-shadow:0 12px 28px rgba(15,50,75,.18)}.card{background:white;border:1px solid #dce4e7;border-radius:10px;padding:14px}.visual-frame img{border-radius:14px;border:1px solid #dce4e7;box-shadow:0 8px 24px rgba(20,45,65,.12)}@media(max-width:760px){.block-container{padding-top:5rem}}</style>""",unsafe_allow_html=True)
st.markdown(f'<div class="hero"><h1>{CFG["name"]}</h1><p>{CFG["subtitle"]}</p><b>{CFG["feature"]}</b></div>',unsafe_allow_html=True)
with st.sidebar:
    if Path(CFG["hero_image"]).exists(): st.image(CFG["hero_image"],use_container_width=True)
    st.header("教学任务入口"); role=st.selectbox("角色",["学生","教师","管理员"]); unit=st.selectbox("课程单元",CFG["units"]); st.caption("所有法规结论须核对标准原文；不确定时明确标注，不补造条款。")
intro_left,intro_right=st.columns([1.15,1])
with intro_left:
    if Path(CFG["module_image"]).exists(): st.image(CFG["module_image"],use_container_width=True)
with intro_right:
    st.subheader("本智能体能做什么")
    for item in CFG["visual_points"]: st.markdown(f"- {item}")
    st.info("教学原则：先补全信息、再检索或计算、随后核验证据，最后由学生完成结论与反思。")
left,right=st.columns([1,1])
with left:
    st.subheader("输入与信息补全")
    question=st.text_area("问题、配料表、报告或作品",height=180,placeholder=CFG["placeholder"])
    product=st.text_input("产品名称/食品类别（可选）")
    additive=st.text_input("添加剂名称（可选）")
    params={}
    if CFG["key"]=="risk":
        a,b,c,d=st.columns(4); params={"concentration_mgkg":a.number_input("浓度 mg/kg",0.0),"food_intake_gday":b.number_input("摄入量 g/d",0.0),"body_weight_kg":c.number_input("体重 kg",0.0),"adi_mgkg_bw_day":d.number_input("ADI",0.0)}
    if st.button("开始分析",type="primary",use_container_width=True):
        st.session_state.result=analyze({"role":role,"course_unit":unit,"task_type":CFG["key"],"question":question,"ingredient_list":question,"product_info":{"name":product,"food_category":product,"additive":additive},"additive":additive,"parameters":params})
with right:
    st.subheader("结构化结果与学习证据")
    result=st.session_state.get("result")
    if result:
        st.success(result["summary"]); st.json(localize(result),expanded=False)
        st.download_button("下载结构化学习记录",json.dumps(localize(result),ensure_ascii=False,indent=2).encode("utf-8"),file_name=f'{CFG["name"]}_学习记录.json',mime="application/json")
    else: st.info("提交任务后，这里显示分析步骤、证据、不确定项、追问和下一步修订任务。")
