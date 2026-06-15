//código placeholder de COMET feito por IA

export type DirecaoCriterio = "beneficio" | "custo";

export type Criterio = {
  id: string;
  nome: string;
  direcao: DirecaoCriterio;
  peso: number;
  niveis: number[];
};

export type Alternativa = {
  id: string;
  nome: string;
  valores: Record<string, number>;
};

export type RequisicaoComet = {
  criterios: Criterio[];
  alternativas: Alternativa[];
};

export type ObjetoCaracteristico = {
  id: string;
  valores: Record<string, number>;
  pontuacao: number;
};

export type ResultadoAlternativa = {
  id: string;
  nome: string;
  pontuacao: number;
  posicao: number;
  valoresNormalizados: Record<string, number>;
  contribuicoes: Record<string, number>;
};

export type RespostaComet = {
  criterios: Criterio[];
  objetosCaracteristicos: ObjetoCaracteristico[];
  ranking: ResultadoAlternativa[];
};

const MAXIMO_OBJETOS_CARACTERISTICOS = 1000;

export function analisarComet(entrada: RequisicaoComet): RespostaComet {
  const criterios = normalizarCriterios(entrada.criterios);
  const alternativas = normalizarAlternativas(entrada.alternativas, criterios);
  const objetosCaracteristicos = montarObjetosCaracteristicos(criterios);

  const ranking = alternativas
    .map((alternativa) => pontuarAlternativa(alternativa, criterios))
    .sort((a, b) => b.pontuacao - a.pontuacao)
    .map((resultado, indice) => ({ ...resultado, posicao: indice + 1 }));

  return {
    criterios,
    objetosCaracteristicos,
    ranking
  };
}

function normalizarCriterios(criterios: Criterio[]): Criterio[] {
  if (!Array.isArray(criterios) || criterios.length === 0) {
    throw new Error("Informe ao menos um criterio.");
  }

  const somaPesos = criterios.reduce((soma, criterio) => soma + Number(criterio.peso || 0), 0);
  if (somaPesos <= 0) {
    throw new Error("A soma dos pesos dos criterios deve ser maior que zero.");
  }

  const criteriosNormalizados: Criterio[] = criterios.map((criterio, indice) => {
    const id = limparId(criterio.id || `c${indice + 1}`);
    const niveisUnicos = Array.from(new Set((criterio.niveis || []).map(Number)))
      .filter(Number.isFinite)
      .sort((a, b) => a - b);

    if (niveisUnicos.length < 2) {
      throw new Error(`O criterio "${criterio.nome || id}" precisa de pelo menos dois niveis caracteristicos.`);
    }

    return {
      id,
      nome: criterio.nome?.trim() || id,
      direcao: criterio.direcao === "custo" ? "custo" : "beneficio",
      peso: Number(criterio.peso) / somaPesos,
      niveis: niveisUnicos
    };
  });

  const quantidadeObjetos = criteriosNormalizados.reduce(
    (quantidade, criterio) => quantidade * criterio.niveis.length,
    1
  );

  if (quantidadeObjetos > MAXIMO_OBJETOS_CARACTERISTICOS) {
    throw new Error(
      `A combinacao dos niveis gera ${quantidadeObjetos} objetos caracteristicos. Reduza os niveis para no maximo ${MAXIMO_OBJETOS_CARACTERISTICOS}.`
    );
  }

  return criteriosNormalizados;
}

function normalizarAlternativas(alternativas: Alternativa[], criterios: Criterio[]): Alternativa[] {
  if (!Array.isArray(alternativas) || alternativas.length === 0) {
    throw new Error("Informe ao menos uma alternativa.");
  }

  return alternativas.map((alternativa, indice) => {
    const valores: Record<string, number> = {};

    for (const criterio of criterios) {
      const valor = Number(alternativa.valores?.[criterio.id]);
      if (!Number.isFinite(valor)) {
        throw new Error(`A alternativa "${alternativa.nome || indice + 1}" nao possui valor numerico para "${criterio.nome}".`);
      }
      valores[criterio.id] = valor;
    }

    return {
      id: limparId(alternativa.id || `a${indice + 1}`),
      nome: alternativa.nome?.trim() || `Alternativa ${indice + 1}`,
      valores
    };
  });
}

function montarObjetosCaracteristicos(criterios: Criterio[]): ObjetoCaracteristico[] {
  const objetos: ObjetoCaracteristico[] = [];

  function percorrer(posicao: number, valores: Record<string, number>) {
    if (posicao === criterios.length) {
      const id = `co-${objetos.length + 1}`;
      const pontuacao = criterios.reduce((soma, criterio) => {
        return soma + normalizarValor(valores[criterio.id], criterio) * criterio.peso;
      }, 0);
      objetos.push({ id, valores: { ...valores }, pontuacao: arredondar(pontuacao) });
      return;
    }

    const criterio = criterios[posicao];
    for (const nivel of criterio.niveis) {
      valores[criterio.id] = nivel;
      percorrer(posicao + 1, valores);
    }
  }

  percorrer(0, {});
  return objetos.sort((a, b) => b.pontuacao - a.pontuacao);
}

function pontuarAlternativa(alternativa: Alternativa, criterios: Criterio[]): ResultadoAlternativa {
  const valoresNormalizados: Record<string, number> = {};
  const contribuicoes: Record<string, number> = {};

  const pontuacao = criterios.reduce((soma, criterio) => {
    const valorNormalizado = normalizarValor(alternativa.valores[criterio.id], criterio);
    const contribuicao = valorNormalizado * criterio.peso;
    valoresNormalizados[criterio.id] = arredondar(valorNormalizado);
    contribuicoes[criterio.id] = arredondar(contribuicao);
    return soma + contribuicao;
  }, 0);

  return {
    id: alternativa.id,
    nome: alternativa.nome,
    pontuacao: arredondar(pontuacao),
    posicao: 0,
    valoresNormalizados,
    contribuicoes
  };
}

function normalizarValor(valor: number, criterio: Criterio): number {
  const minimo = criterio.niveis[0];
  const maximo = criterio.niveis[criterio.niveis.length - 1];
  if (maximo === minimo) {
    return 1;
  }

  const valorLimitado = Math.min(maximo, Math.max(minimo, valor));
  const normalizado = (valorLimitado - minimo) / (maximo - minimo);
  return criterio.direcao === "custo" ? 1 - normalizado : normalizado;
}

function limparId(valor: string): string {
  return valor
    .toString()
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function arredondar(valor: number): number {
  return Math.round(valor * 10000) / 10000;
}
