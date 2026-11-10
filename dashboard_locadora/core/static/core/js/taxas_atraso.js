const catalogo = JSON.parse(document.getElementById("catalogo-calculadora").textContent);
const parametros = JSON.parse(document.getElementById("parametros-calculadora").textContent);
const carroSelect = document.getElementById("carro-calculo");
const horasInput = document.getElementById("horas-atraso");
const diariaOutput = document.getElementById("valor-diaria");
const multaOutput = document.getElementById("valor-multa");
const detalheOutput = document.getElementById("detalhe-calculo");
const moeda = new Intl.NumberFormat("pt-BR", {style: "currency", currency: "BRL"});

function calcularMulta(diaria, horas) {
  const diariaEmCentavos = Math.round(diaria * 100);
  if (horas <= parametros.tolerancia_horas) {
    return {
      centavos: 0,
      detalhe: `Até ${parametros.tolerancia_horas} hora(s) de atraso: sem cobrança.`,
    };
  }
  if (horas <= parametros.limite_faixa_hora) {
    const centavos = Math.round(diariaEmCentavos * parametros.percentual * horas);
    const percentual = parametros.percentual * 100;
    return {centavos, detalhe: `${percentual}% da diária por hora: ${moeda.format(centavos / 100)}.`};
  }
  const diasOuFracoes = Math.ceil(horas / 24);
  const multaPorDia = Math.round(diariaEmCentavos * (1 + parametros.percentual));
  const centavos = multaPorDia * diasOuFracoes;
  const unidade = diasOuFracoes === 1 ? "diária" : "diárias";
  return {
    centavos,
    detalhe: `${diasOuFracoes} ${unidade} com adicional de 10% (dia ou fração).`,
  };
}

function atualizarCalculo() {
  const carro = catalogo.find(item => item.slug === carroSelect.value);
  const horasInformadas = Number(horasInput.value);
  const horas = Number.isFinite(horasInformadas) ? Math.min(Math.max(horasInformadas, 0), 8760) : 0;
  if (!carro) {
    diariaOutput.textContent = "—";
    multaOutput.textContent = moeda.format(0);
    detalheOutput.textContent = "Selecione um carro do catálogo.";
    return;
  }

  const resultado = calcularMulta(carro.diaria, horas);
  diariaOutput.textContent = moeda.format(carro.diaria);
  multaOutput.textContent = moeda.format(resultado.centavos / 100);
  detalheOutput.textContent = resultado.detalhe;
}

carroSelect.addEventListener("change", atualizarCalculo);
horasInput.addEventListener("input", atualizarCalculo);
atualizarCalculo();
