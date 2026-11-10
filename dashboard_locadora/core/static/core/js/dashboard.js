const D = JSON.parse(document.getElementById("diarias").textContent);
const sc = document.getElementById("sc"), sh = document.getElementById("sh"), sr = document.getElementById("sr");
const brl = n => n.toLocaleString("pt-BR", {style:"currency", currency:"BRL"});
function multa(d, h){
  if (h <= 1) return 0;
  if (h <= 3) return d * 0.1 * h;
  return d * 1.1 * Math.ceil(h / 24);
}
function sim(){ sr.textContent = brl(multa(D[sc.value] || 0, parseFloat(sh.value) || 0)); }
sc.onchange = sim; sh.oninput = sim; sim();
