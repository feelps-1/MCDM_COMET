import { NextResponse } from "next/server";
import { analisarComet, type RequisicaoComet } from "@/lib/comet";

export async function POST(requisicao: Request) {
  try {
    const corpo = (await requisicao.json()) as RequisicaoComet;
    const resultado = analisarComet(corpo);
    return NextResponse.json(resultado);
  } catch (erro) {
    const mensagem = erro instanceof Error ? erro.message : "Nao foi possivel executar a analise COMET.";
    return NextResponse.json({ erro: mensagem }, { status: 400 });
  }
}
