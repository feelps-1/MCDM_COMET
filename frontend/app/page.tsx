"use client";

import { ChevronLeft, ChevronRight, CirclePlus, Medal, Play, RotateCcw, Trash2, Trophy } from "lucide-react";
import { useMemo, useState } from "react";
import type { Alternativa, Criterio, DirecaoCriterio, RespostaComet } from "@/lib/comet";

type CriterioRascunho = Omit<Criterio, "niveis" | "peso"> & {
  peso: string;
  niveisTexto: string;
};

type AlternativaRascunho = {
  id: string;
  nome: string;
  valores: Record<string, string>;
};

const criteriosIniciais: CriterioRascunho[] = [
  { id: "custo", nome: "Custo", direcao: "custo", peso: "0.30", niveisTexto: "80000, 120000, 180000" },
  { id: "retorno", nome: "Retorno", direcao: "beneficio", peso: "0.35", niveisTexto: "6, 12, 20" },
  { id: "risco", nome: "Risco", direcao: "custo", peso: "0.20", niveisTexto: "1, 3, 5" },
  { id: "impacto", nome: "Impacto", direcao: "beneficio", peso: "0.15", niveisTexto: "1, 3, 5" }
];

const alternativasIniciais: AlternativaRascunho[] = [
  { id: "a1", nome: "Competidor 1", valores: { custo: "110000", retorno: "16", risco: "3", impacto: "5" } },
  { id: "a2", nome: "Competidor 2", valores: { custo: "150000", retorno: "18", risco: "4", impacto: "4" } },
  { id: "a3", nome: "Competidor 3", valores: { custo: "90000", retorno: "10", risco: "2", impacto: "3" } }
];

const missoes = ["Criterios", "Alternativas", "Resultado"];

export default function Home() {
  const [fase, definirFase] = useState(0);
  const [criterios, definirCriterios] = useState<CriterioRascunho[]>(criteriosIniciais);
  const [alternativas, definirAlternativas] = useState<AlternativaRascunho[]>(alternativasIniciais);
  const [resultado, definirResultado] = useState<RespostaComet | null>(null);
  const [erro, definirErro] = useState("");
  const [carregando, definirCarregando] = useState(false);

  const somaPesos = useMemo(
    () => criterios.reduce((soma, criterio) => soma + Number(criterio.peso || 0), 0),
    [criterios]
  );
  const progresso = ((fase + 1) / missoes.length) * 100;
  const vencedor = resultado?.ranking[0];

  async function executarAnalise() {
    definirCarregando(true);
    definirErro("");

    try {
      const conteudo = montarConteudo(criterios, alternativas);
      const resposta = await fetch("/api/comet/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(conteudo)
      });
      const corpo = await resposta.json();

      if (!resposta.ok) {
        throw new Error(corpo.erro || "Nao foi possivel calcular o ranking.");
      }

      definirResultado(corpo);
      definirFase(2);
    } catch (erroAnalise) {
      definirResultado(null);
      definirErro(erroAnalise instanceof Error ? erroAnalise.message : "Erro inesperado.");
    } finally {
      definirCarregando(false);
    }
  }

  function atualizarCriterio(indice: number, alteracao: Partial<CriterioRascunho>) {
    definirCriterios((atuais) => {
      const proximos = [...atuais];
      const idAnterior = proximos[indice].id;
      proximos[indice] = { ...proximos[indice], ...alteracao };

      if (alteracao.id && alteracao.id !== idAnterior) {
        definirAlternativas((itens) =>
          itens.map((alternativa) => {
            const valores = { ...alternativa.valores, [alteracao.id as string]: alternativa.valores[idAnterior] || "" };
            delete valores[idAnterior];
            return { ...alternativa, valores };
          })
        );
      }

      return proximos;
    });
    definirResultado(null);
  }

  function adicionarCriterio() {
    const id = `criterio-${criterios.length + 1}`;
    definirCriterios((atuais) => [
      ...atuais,
      { id, nome: `Criterio ${atuais.length + 1}`, direcao: "beneficio", peso: "0.10", niveisTexto: "1, 3, 5" }
    ]);
    definirAlternativas((atuais) =>
      atuais.map((alternativa) => ({ ...alternativa, valores: { ...alternativa.valores, [id]: "3" } }))
    );
    definirResultado(null);
  }

  function removerCriterio(indice: number) {
    if (criterios.length <= 1) {
      return;
    }

    const idRemovido = criterios[indice].id;
    definirCriterios((atuais) => atuais.filter((_, indiceItem) => indiceItem !== indice));
    definirAlternativas((atuais) =>
      atuais.map((alternativa) => {
        const valores = { ...alternativa.valores };
        delete valores[idRemovido];
        return { ...alternativa, valores };
      })
    );
    definirResultado(null);
  }

  function adicionarAlternativa() {
    const valores = Object.fromEntries(criterios.map((criterio) => [criterio.id, ""]));
    definirAlternativas((atuais) => [
      ...atuais,
      { id: `a${atuais.length + 1}`, nome: `Alternativa ${atuais.length + 1}`, valores }
    ]);
    definirResultado(null);
  }

  function atualizarAlternativa(indice: number, alteracao: Partial<AlternativaRascunho>) {
    definirAlternativas((atuais) => {
      const proximas = [...atuais];
      proximas[indice] = { ...proximas[indice], ...alteracao };
      return proximas;
    });
    definirResultado(null);
  }

  function atualizarValorAlternativa(indice: number, idCriterio: string, valor: string) {
    definirAlternativas((atuais) => {
      const proximas = [...atuais];
      proximas[indice] = {
        ...proximas[indice],
        valores: { ...proximas[indice].valores, [idCriterio]: valor }
      };
      return proximas;
    });
    definirResultado(null);
  }

  function restaurarExemplo() {
    definirCriterios(criteriosIniciais);
    definirAlternativas(alternativasIniciais);
    definirResultado(null);
    definirErro("");
    definirFase(0);
  }

  return (
    <main>
      <section className="hero">
        <div>
          <p className="eyebrow">COMET quest</p>
          <h1>Escolha a melhor alternativa</h1>
          <p>Complete 3 fases: pesos, candidatos e pódio final.</p>
        </div>
        <button className="ghost" onClick={restaurarExemplo} title="Restaurar exemplo">
          <RotateCcw size={18} />
          Exemplo
        </button>
      </section>

      <section className="quest">
        <div className="progress-head">
          <strong>Fase {fase + 1} de 3</strong>
          <span>{missoes[fase]}</span>
        </div>
        <div className="progress-track">
          <div style={{ width: `${progresso}%` }} />
        </div>
        <div className="mission-map">
          {missoes.map((missao, indice) => (
            <button
              className={indice === fase ? "mission active" : indice < fase ? "mission done" : "mission"}
              key={missao}
              onClick={() => definirFase(indice)}
            >
              <span>{indice + 1}</span>
              {missao}
            </button>
          ))}
        </div>
      </section>

      {erro ? <p className="error">{erro}</p> : null}

      {fase === 0 ? (
        <section className="panel">
          <div className="panel-title">
            <div>
              <p className="eyebrow">Fase 1</p>
              <h2>Defina o que vale pontos</h2>
            </div>
            <button className="icon-button" onClick={adicionarCriterio} title="Adicionar criterio">
              <CirclePlus size={18} />
            </button>
          </div>

          <div className="mini-stats">
            <div>
              <strong>{criterios.length}</strong>
              <span>criterios</span>
            </div>
            <div>
              <strong>{somaPesos.toFixed(2)}</strong>
              <span>peso total</span>
            </div>
          </div>

          <div className="criteria-list">
            {criterios.map((criterio, indice) => (
              <article className="criterion-card" key={criterio.id}>
                <input
                  aria-label="Nome do criterio"
                  value={criterio.nome}
                  onChange={(evento) => atualizarCriterio(indice, { nome: evento.target.value })}
                />
                <select
                  aria-label="Direcao do criterio"
                  value={criterio.direcao}
                  onChange={(evento) =>
                    atualizarCriterio(indice, { direcao: evento.target.value as DirecaoCriterio })
                  }
                >
                  <option value="beneficio">Maior e melhor</option>
                  <option value="custo">Menor e melhor</option>
                </select>
                <input
                  aria-label="Peso"
                  type="number"
                  step="0.01"
                  value={criterio.peso}
                  onChange={(evento) => atualizarCriterio(indice, { peso: evento.target.value })}
                />
                <input
                  aria-label="Niveis caracteristicos"
                  value={criterio.niveisTexto}
                  onChange={(evento) => atualizarCriterio(indice, { niveisTexto: evento.target.value })}
                />
                <button className="icon-button danger" onClick={() => removerCriterio(indice)} title="Remover criterio">
                  <Trash2 size={17} />
                </button>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {fase === 1 ? (
        <section className="panel">
          <div className="panel-title">
            <div>
              <p className="eyebrow">Fase 2</p>
              <h2>Cadastre os competidores</h2>
            </div>
            <button className="icon-button" onClick={adicionarAlternativa} title="Adicionar alternativa">
              <CirclePlus size={18} />
            </button>
          </div>

          <div className="alternative-grid">
            {alternativas.map((alternativa, indice) => (
              <article className="candidate-card" key={alternativa.id}>
                <div className="candidate-head">
                  <input
                    aria-label="Nome da alternativa"
                    value={alternativa.nome}
                    onChange={(evento) => atualizarAlternativa(indice, { nome: evento.target.value })}
                  />
                  <button
                    className="icon-button danger"
                    onClick={() => definirAlternativas((atuais) => atuais.filter((_, indiceItem) => indiceItem !== indice))}
                    title="Remover alternativa"
                  >
                    <Trash2 size={17} />
                  </button>
                </div>
                <div className="score-fields">
                  {criterios.map((criterio) => (
                    <label key={criterio.id}>
                      <span>{criterio.nome}</span>
                      <input
                        aria-label={`Valor de ${criterio.nome}`}
                        type="number"
                        value={alternativa.valores[criterio.id] ?? ""}
                        onChange={(evento) => atualizarValorAlternativa(indice, criterio.id, evento.target.value)}
                      />
                    </label>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {fase === 2 ? (
        <section className="results">
          <div className="winner-panel">
            <p className="eyebrow">Fase 3</p>
            <Trophy size={46} />
            <h2>{vencedor ? vencedor.nome : "Pronto para revelar o vencedor"}</h2>
            <strong>{vencedor ? `${(vencedor.pontuacao * 100).toFixed(1)}%` : "?"}</strong>
          </div>

          <div className="panel">
            <div className="panel-title">
              <div>
                <p className="eyebrow">Podio</p>
                <h2>Ranking COMET</h2>
              </div>
              <Medal size={24} />
            </div>

            {resultado ? (
              <div className="ranking-list">
                {resultado.ranking.map((item) => (
                  <article className="ranking-item" key={item.id}>
                    <div className="rank-badge">{item.posicao}</div>
                    <div>
                      <h3>{item.nome}</h3>
                      <progress max={1} value={item.pontuacao} />
                    </div>
                    <strong>{(item.pontuacao * 100).toFixed(1)}%</strong>
                  </article>
                ))}
              </div>
            ) : (
              <p className="empty">Clique em calcular para gerar o ranking.</p>
            )}
          </div>
        </section>
      ) : null}

      <nav className="bottom-actions">
        <button className="ghost" onClick={() => definirFase((atual) => Math.max(0, atual - 1))} disabled={fase === 0}>
          <ChevronLeft size={18} />
          Voltar
        </button>
        {fase < 1 ? (
          <button className="primary" onClick={() => definirFase(1)}>
            Avancar
            <ChevronRight size={18} />
          </button>
        ) : (
          <button className="primary" onClick={executarAnalise} disabled={carregando}>
            <Play size={18} />
            {carregando ? "Calculando" : "Calcular COMET"}
          </button>
        )}
      </nav>
    </main>
  );
}

function montarConteudo(criterios: CriterioRascunho[], alternativas: AlternativaRascunho[]) {
  const criteriosFormatados: Criterio[] = criterios.map((criterio) => ({
    id: criterio.id.trim(),
    nome: criterio.nome.trim(),
    direcao: criterio.direcao,
    peso: Number(criterio.peso),
    niveis: criterio.niveisTexto
      .split(",")
      .map((valor) => Number(valor.trim()))
      .filter(Number.isFinite)
  }));

  const alternativasFormatadas: Alternativa[] = alternativas.map((alternativa, indice) => ({
    id: alternativa.id || `a${indice + 1}`,
    nome: alternativa.nome,
    valores: Object.fromEntries(
      criteriosFormatados.map((criterio) => [criterio.id, Number(alternativa.valores[criterio.id])])
    )
  }));

  return { criterios: criteriosFormatados, alternativas: alternativasFormatadas };
}
