# desdobra1X2

Ferramenta de **análise e geração de apostas** para os jogos da Santa Casa: Totobola, Totoloto, Euromilhões e EuroDreams, mais previsões de jogos de futebol de mais de 20 ligas.

> **Aviso:** as previsões do Totobola e do Futebol são meramente estatísticas e os números das lotarias são gerados aleatoriamente. **Não há qualquer garantia de acerto.** A ferramenta não submete apostas: copias o resultado e preenches tu no site oficial. Joga com responsabilidade, maiores de 18 anos.

## O que faz
- **Totobola e Totobola Extra:** carrega os 13 jogos do concurso, calcula as probabilidades de 1, X e 2, deixa-te fixar resultados ou fazer duplas e gera o desdobramento das apostas.
- **Futebol:** próximos jogos de mais de 20 ligas, com as nossas probabilidades, as das casas de apostas como referência, golos esperados e um boletim.
- **Critérios editáveis:** vês o que pesa em cada previsão e podes dar mais ou menos importância a cada critério. Os predefinidos ficam sempre à mão.
- **Totoloto, Euromilhões e EuroDreams:** chaves geradas ao acaso dentro das regras de cada jogo.

## Documentação
- [Tutorial](docs/tutorial.md): como usar, passo a passo.
- [Como calculamos as previsões](docs/criterios.md): dados, fórmulas, validação e limitações.
- [Desenvolvimento](docs/desenvolvimento.md): correr, testar e configurar.
- [Roteiro](docs/README.md): o que está feito e o que falta.

## Correr localmente
Precisas de Python 3.12 e Node. Em dois terminais:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173. Mais detalhes em [docs/desenvolvimento.md](docs/desenvolvimento.md).
