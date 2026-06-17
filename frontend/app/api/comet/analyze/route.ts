import { NextResponse } from "next/server";
import type { DecisionRequest } from "@/lib/comet";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(requisicao: Request) {
  try {
    const corpo = (await requisicao.json()) as DecisionRequest;

    const resposta = await fetch(`${BACKEND_URL}/api/v1/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });

    const dados = await resposta.json();

    if (!resposta.ok) {
      return NextResponse.json(
        { erro: dados?.detail ?? "Erro no backend COMET." },
        { status: resposta.status }
      );
    }

    return NextResponse.json(dados);
  } catch (erro) {
    const mensagem = erro instanceof Error ? erro.message : "Nao foi possivel executar a analise COMET.";
    return NextResponse.json({ erro: mensagem }, { status: 500 });
  }
}
