"use client";

import { ChevronLeft, ChevronRight, CirclePlus, Medal, Play, RotateCcw, Trash2, Trophy } from "lucide-react";
import { useState } from "react";
import type { DecisionRequest, DecisionResponse } from "@/lib/comet";

type ConfigCircuito = {
  psu_voltage: string;
  led_voltage: string;
  led_current: string;
  max_current: string;
};

type AlternativaRascunho = {
  id: string;
  nome: string;
  ddp: string;
  corrente: string;
};

const configInicial: ConfigCircuito = {
  psu_voltage: "32",
  led_voltage: "2",
  led_current: "1",
  max_current: "4",
};

const alternativasIniciais: AlternativaRascunho[] = [
  { id: "a1",  nome: "A1",  ddp: "5",  corrente: "0.125" },
  { id: "a2",  nome: "A2",  ddp: "10", corrente: "0.125" },
  { id: "a3",  nome: "A3",  ddp: "20", corrente: "0.125" },
  { id: "a4",  nome: "A4",  ddp: "30", corrente: "0.125" },
  { id: "a5",  nome: "A5",  ddp: "5",  corrente: "1" },
  { id: "a6",  nome: "A6",  ddp: "10", corrente: "1" },
  { id: "a7",  nome: "A7",  ddp: "20", corrente: "1" },
  { id: "a8",  nome: "A8",  ddp: "30", corrente: "1" },
  { id: "a9",  nome: "A9",  ddp: "5",  corrente: "4" },
  { id: "a10", nome: "A10", ddp: "10", corrente: "4" },
  { id: "a11", nome: "A11", ddp: "20", corrente: "4" },
  { id: "a12", nome: "A12", ddp: "30", corrente: "4" },
];

const missoes = ["Configuracao", "Alternativas", "Resultado"];

function calcularR(ddp: string, corrente: string): string {
  const u = Number(ddp);
  const i = Number(corrente);
  if (!u || !i) return "—";
  return (u / i).toFixed(4).replace(/\.?0+$/, "") + " Ω";
}

export default function Home() {
  const [fase, definirFase] = useState(0);
  const [config, definirConfig] = useState<ConfigCircuito>(configInicial);
  const [alternativas, definirAlternativas] = useState<AlternativaRascunho[]>(alternativasIniciais);
  const [resultado, definirResultado] = useState<DecisionResponse | null>(null);
  const [erro, definirErro] = useState("");
  const [carregando, definirCarregando] = useState(false);

  const progresso = ((fase + 1) / missoes.length) * 100;
  const vencedor = resultado?.ranking[0];

  async function executarAnalise() {
    definirCarregando(true);
    definirErro("");
    try {
      const payload = montarPayload(config, alternativas);
      const resposta = await fetch("/api/comet/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const corpo = await resposta.json();
      if (!resposta.ok) {
        throw new Error(corpo.erro ?? corpo.detail ?? "Nao foi possivel calcular o ranking.");
      }
      definirResultado(corpo);
      definirFase(2);
    } catch (e) {
      definirErro(e instanceof Error ? e.message : "Erro inesperado.");
    } finally {
      definirCarregando(false);
    }
  }

  function restaurarExemplo() {
    definirConfig(configInicial);
    definirAlternativas(alternativasIniciais);
    definirResultado(null);
    definirErro("");
    definirFase(0);
  }

  function adicionarAlternativa() {
    const id = `a${Date.now()}`;
    definirAlternativas((a) => [
      ...a,
      { id, nome: `A${a.length + 1}`, ddp: "", corrente: "" },
    ]);
    definirResultado(null);
  }

  function atualizarAlternativa(indice: number, campo: Partial<AlternativaRascunho>) {
    definirAlternativas((atuais) => {
      const proximas = [...atuais];
      proximas[indice] = { ...proximas[indice], ...campo };
      return proximas;
    });
    definirResultado(null);
  }

  function atualizarConfig(campo: keyof ConfigCircuito, valor: string) {
    definirConfig((c) => ({ ...c, [campo]: valor }));
    definirResultado(null);
  }

  return (
    <main>
      <section className="hero">
        <div>
          <p className="eyebrow">COMET — Selecao de Resistores</p>
          <h1>Encontre o resistor ideal</h1>
          <p>Informe DDP e corrente de cada alternativa e receba o ranking COMET.</p>
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
              key={missao}
              className={indice === fase ? "mission active" : indice < fase ? "mission done" : "mission"}
              onClick={() => definirFase(indice)}
            >
              <span>{indice + 1}</span>
              {missao}
            </button>
          ))}
        </div>
      </section>

      {erro ? <p className="error">{erro}</p> : null}

      {/* ── FASE 1: Configuracao do circuito ─────────────────────────────── */}
      {fase === 0 && (
        <section className="panel">
          <div className="panel-title">
            <div>
              <p className="eyebrow">Fase 1</p>
              <h2>Parametros do circuito</h2>
            </div>
          </div>
          <div className="criteria-list">
            {(
              [
                { campo: "psu_voltage", rotulo: "Tensao da fonte PSU (V)", hint: "Fallback quando a alternativa nao define DDP" },
                { campo: "led_voltage", rotulo: "Tensao direta do LED  (V)", hint: "Queda de tensao tipica do LED" },
                { campo: "led_current", rotulo: "Corrente nominal do LED (A)", hint: "Corrente de operacao ideal" },
                { campo: "max_current", rotulo: "Corrente maxima (A)", hint: "Limite absoluto de corrente" },
              ] as { campo: keyof ConfigCircuito; rotulo: string; hint: string }[]
            ).map(({ campo, rotulo, hint }) => (
              <article className="criterion-card" key={campo}>
                <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span style={{ fontWeight: 600 }}>{rotulo}</span>
                  <small style={{ color: "var(--muted)" }}>{hint}</small>
                  <input
                    type="number"
                    step="any"
                    min="0"
                    value={config[campo]}
                    onChange={(e) => atualizarConfig(campo, e.target.value)}
                  />
                </label>
              </article>
            ))}
          </div>
        </section>
      )}

      {/* ── FASE 2: Alternativas ─────────────────────────────────────────── */}
      {fase === 1 && (
        <section className="panel">
          <div className="panel-title">
            <div>
              <p className="eyebrow">Fase 2</p>
              <h2>Alternativas de resistor</h2>
            </div>
            <button className="icon-button" onClick={adicionarAlternativa} title="Adicionar alternativa">
              <CirclePlus size={18} />
            </button>
          </div>
          <div className="mini-stats">
            <div>
              <strong>{alternativas.length}</strong>
              <span>alternativas</span>
            </div>
          </div>
          <div className="alternative-grid">
            {alternativas.map((alt, indice) => (
              <article className="candidate-card" key={alt.id}>
                <div className="candidate-head">
                  <input
                    aria-label="Nome"
                    placeholder="Nome"
                    value={alt.nome}
                    onChange={(e) => atualizarAlternativa(indice, { nome: e.target.value })}
                  />
                  <button
                    className="icon-button danger"
                    onClick={() => {
                      definirAlternativas((a) => a.filter((_, i) => i !== indice));
                      definirResultado(null);
                    }}
                    title="Remover alternativa"
                  >
                    <Trash2 size={17} />
                  </button>
                </div>
                <div className="score-fields">
                  <label>
                    <span>DDP / U (V)</span>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      placeholder="ex: 5"
                      value={alt.ddp}
                      onChange={(e) => atualizarAlternativa(indice, { ddp: e.target.value })}
                    />
                  </label>
                  <label>
                    <span>Corrente / I (A)</span>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      placeholder="ex: 0.125"
                      value={alt.corrente}
                      onChange={(e) => atualizarAlternativa(indice, { corrente: e.target.value })}
                    />
                  </label>
                  <label>
                    <span>R = U/I</span>
                    <input readOnly value={calcularR(alt.ddp, alt.corrente)} />
                  </label>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {/* ── FASE 3: Resultado ────────────────────────────────────────────── */}
      {fase === 2 && (
        <section className="results">
          <div className="winner-panel">
            <p className="eyebrow">Fase 3</p>
            <Trophy size={46} />
            <h2>{vencedor ? vencedor.name : "Pronto para revelar o vencedor"}</h2>
            <strong>
              {vencedor
                ? `R = ${vencedor.resistor_ohm.toFixed(4).replace(/\.?0+$/, "")} Ω`
                : "?"}
            </strong>
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
                  <article className="ranking-item" key={item.name}>
                    <div className="rank-badge">{item.rank}</div>
                    <div style={{ flex: 1 }}>
                      <h3>{item.name}</h3>
                      <small style={{ color: "var(--muted)" }}>
                        R = {item.resistor_ohm.toFixed(4).replace(/\.?0+$/, "")} Ω
                        &nbsp;|&nbsp;
                        P = {item.power_w.toFixed(4).replace(/\.?0+$/, "")} W
                      </small>
                      <progress max={1} value={item.preference} />
                    </div>
                    <strong>{(item.preference * 100).toFixed(1)}%</strong>
                  </article>
                ))}
              </div>
            ) : (
              <p className="empty">Clique em calcular para gerar o ranking.</p>
            )}
          </div>
        </section>
      )}

      <nav className="bottom-actions">
        <button className="ghost" onClick={() => definirFase((f) => Math.max(0, f - 1))} disabled={fase === 0}>
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
            {carregando ? "Calculando..." : "Calcular COMET"}
          </button>
        )}
      </nav>
    </main>
  );
}

function montarPayload(config: ConfigCircuito, alternativas: AlternativaRascunho[]): DecisionRequest {
  const led_v = Number(config.led_voltage);
  return {
    psu_voltage: Number(config.psu_voltage),
    led_voltage: led_v,
    led_current: Number(config.led_current),
    max_current: Number(config.max_current),
    alternatives: alternativas.map((alt, i) => ({
      name: alt.nome || `A${i + 1}`,
      target_current: Number(alt.corrente),
      source_voltage: alt.ddp ? led_v + Number(alt.ddp) : undefined,
    })),
  };
}

