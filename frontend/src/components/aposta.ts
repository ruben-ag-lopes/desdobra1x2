// "3 4 6 7 8 + 1" from the number boxes: the first `numeros` boxes are the numbers, the rest the extra ones.
export function montarAposta(valores: string[], numeros: number): string {
  return `${valores.slice(0, numeros).join(" ")} + ${valores.slice(numeros).join(" ")}`;
}
