/* 盈亏平衡模型的浏览器端实现，与 src/business_case.py 同一套算式。
   所有参数均为假设值，非真实业务数据。 */
function biz(){
  const g=id=>+document.getElementById(id).value;
  const exposure=g("bexp"), conv=g("bconv")/100, drop=g("bdrop")/100, prin=g("bprin"),
        cr=g("bcr")/100, cc=g("bcc"), dr=g("bdr")/100, dc=g("bdc");
  const orders=exposure*conv, feePer=prin*0.006*12, lost=orders*drop,
        loss=lost*feePer, rem=orders-lost, cBase=rem*cr*cc, dBase=rem*dr*dc;
  const needC=cBase?loss/cBase:null, needD=dBase?loss/dBase:null;
  const f=x=>Math.round(x).toLocaleString("en-US");
  const pc=x=>x===null?"—":(x*100).toFixed(0)+"%";
  const cls=x=>x===null?"":x>1?"bad":x>0.35?"warn":"good";
  document.getElementById("bout").innerHTML=
    '<div class="kpi"><div class="n bad">'+f(loss)+'</div><div class="l">月手续费收入损失</div>'+
      '<div class="d">流失 '+f(lost)+' 笔 × 单笔 '+f(feePer)+'</div></div>'+
    '<div class="kpi"><div class="n">'+f(cBase+dBase)+'</div>'+
      '<div class="l">可被抵消的成本总基数</div>'+
      '<div class="d">投诉 '+f(cBase)+' ＋ 逾期 '+f(dBase)+'</div></div>'+
    '<div class="kpi"><div class="n '+cls(needC)+'">'+pc(needC)+'</div>'+
      '<div class="l">仅靠投诉率下降需降</div></div>'+
    '<div class="kpi"><div class="n '+cls(needD)+'">'+pc(needD)+'</div>'+
      '<div class="l">仅靠首期逾期率下降需降</div></div>';
  const v=document.getElementById("bverdict");
  if(needC>1&&needD>1){
    v.innerHTML="<strong>抵不平，而且差得很远。</strong>收入损失超过投诉成本与逾期损失的"+
      "<strong>全部基数之和</strong>——即使把两者降到零也补不上缺口。<br><br>"+
      "正确的结论不是「这个功能不值得做」（披露是义务），而是："+
      "<strong>不要用收入口径为合规功能辩护。</strong>"+
      "应按合规成本口径立项，把转化损失作为已知代价申报，并在实验中把它测准——"+
      "而不是假装它不存在，或用编造的收益去掩盖它。";
  } else if(Math.min(needC,needD)<0.20){
    v.innerHTML="抵消所需的降幅在 20% 以内，属于<strong>可能达成</strong>的范围——"+
      "但必须在实验中同时测量投诉率与逾期率，否则这仍然只是一个假设。";
  } else {
    v.innerHTML="抵消所需的降幅偏大，落在「需要证据才敢主张」的区间。"+
      "建议先做小流量实验测出真实的转化降幅，再重算这张表。";
  }
}
["bexp","bconv","bdrop","bprin","bcr","bcc","bdr","bdc"].forEach(
  id=>document.getElementById(id).addEventListener("input",biz));
biz();
