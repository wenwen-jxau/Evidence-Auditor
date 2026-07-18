import json
from pathlib import Path
import streamlit as st
from agent_core import CFG, analyze
st.set_page_config(page_title=CFG["name"],page_icon="🧪",layout="wide")
st.markdown("""<style>.block-container{padding-top:4.6rem;max-width:1200px}.hero{padding:24px;border-radius:14px;background:linear-gradient(135deg,#12334d,#0f766e);color:white;margin-bottom:18px;box-shadow:0 12px 28px rgba(15,50,75,.18)}.card{background:white;border:1px solid #dce4e7;border-radius:10px;padding:14px}.visual-frame img{border-radius:14px;border:1px solid #dce4e7;box-shadow:0 8px 24px rgba(20,45,65,.12)}@media(max-width:760px){.block-container{padding-top:5rem}}</style>""",unsafe_allow_html=True)
st.markdown(f'<div class="hero"><h1>{CFG["name"]}</h1><p>{CFG["subtitle"]}</p><b>{CFG["feature"]}</b></div>',unsafe_allow_html=True)
with st.sidebar:
    if Path(CFG["hero_image"]).exists(): st.image(CFG["hero_image"],use_container_width=True)
    st.header("教学任务入口"); role=st.selectbox("角色",["student","teacher","admin"]); unit=st.selectbox("课程单元",CFG["units"]); st.caption("所有法规结论须核对标准原文；不确定时明确标注，不补造条款。")
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
        st.success(result["summary"]); st.json(result,expanded=False)
        st.download_button("下载JSON学习记录",json.dumps(result,ensure_ascii=False,indent=2).encode("utf-8"),file_name=f'{CFG["key"]}_learning_trace.json',mime="application/json")
    else: st.info("提交任务后，这里显示分析步骤、证据、不确定项、追问和下一步修订任务。")
