import { NextResponse } from "next/server";
import type { DecisionRequest } from "@/lib/comet";

function backendUrl(): string {
  if (process.env.BACKEND_URL) return process.env.BACKEND_URL;
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}/_/backend`;
  return "http://localhost:8000";
}

export async function POST(requisicao: Request) {
  const url = `${backendUrl()}/api/v1/decision`;
  console.log("[analyze] BACKEND_URL env:", process.env.BACKEND_URL ?? "(not set)");
  console.log("[analyze] VERCEL_URL env: ", process.env.VERCEL_URL ?? "(not set)");
  console.log("[analyze] Calling backend:", url);

  try {
    const corpo = (await requisicao.json()) as DecisionRequest;
    console.log("[analyze] Payload:", JSON.stringify(corpo));

    const resposta = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });

    const rawText = await resposta.text();
    console.log("[analyze] Backend status:", resposta.status);
    console.log("[analyze] Backend body:  ", rawText.slice(0, 500));

    let dados: unknown;
    try {
      dados = JSON.parse(rawText);
    } catch {
      return NextResponse.json(
        { erro: `Backend returned non-JSON (status ${resposta.status}): ${rawText.slice(0, 200)}` },
        { status: 502 }
      );
    }

    if (!resposta.ok) {
      const detail = (dados as Record<string, unknown>)?.detail ?? (dados as Record<string, unknown>)?.erro ?? rawText;
      return NextResponse.json(
        { erro: String(detail) },
        { status: resposta.status }
      );
    }

    return NextResponse.json(dados);
  } catch (erro) {
    const mensagem = erro instanceof Error ? erro.message : "Nao foi possivel executar a analise COMET.";
    console.error("[analyze] Unexpected error:", mensagem);
    return NextResponse.json({ erro: mensagem }, { status: 500 });
  }
}
