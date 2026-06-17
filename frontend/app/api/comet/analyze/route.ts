import { NextResponse } from "next/server";
import type { DecisionRequest } from "@/lib/comet";

// In production on Vercel, the backend service is reachable at /_/backend
// (routePrefix defined in vercel.json). VERCEL_URL is set automatically by Vercel.
// In local development, fall back to localhost:8000.
function backendUrl(): string {
  if (process.env.BACKEND_URL) return process.env.BACKEND_URL;
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}/_/backend`;
  return "http://localhost:8000";
}

export async function POST(requisicao: Request) {
  try {
    const corpo = (await requisicao.json()) as DecisionRequest;

    const resposta = await fetch(`${backendUrl()}/api/v1/decision`, {
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
