# Galaxy Invaders — Python + SWAPI REST (projeto acadêmico)

Duas versões do mesmo jogo estão nesta pasta:

- **`galaxy_invaders_swapi.py`**: jogo desktop Python/Tkinter **com consulta real à SWAPI**.
- **`index.html`**: jogo JavaScript/HTML com SWAPI, publicável no GitHub Pages.

## API pública utilizada

- Documentação: https://swapi.info/documentation
- URL: `https://swapi.info/api/starships`
- Método HTTP: **GET**
- Resposta: **JSON**, sem chave de API.

Na versão Python, a variável `API_URL` está no início do arquivo, após os imports. A função `consultar_api_em_background()` usa a biblioteca padrão `urllib.request` para baixar o JSON. A função `normalizar_naves()` extrai `name`, `starship_class` e `MGLT`.

Uma **thread** separada evita congelar o Tkinter durante a solicitação. A **fila** (`queue.Queue`) entrega os resultados à interface com segurança. Os inimigos usam a **classe** para influenciar o desenho e **MGLT** para definir um bônus limitado de velocidade. Caso a API esteja offline, o jogo continua em modo procedural local, e mostra esse estado de forma transparente.

**Atenção:** a SWAPI oferece **dados sobre espaçonaves, não imagens geradas por IA**. Os sprites são criados proceduralmente.

## Executar a versão Python no Windows

1. Instale o Python 3 em https://www.python.org/downloads/ (com suporte a Tkinter).
2. Clique duas vezes em `INICIAR_JOGO_WINDOWS.bat`, ou abra o terminal nesta pasta e execute `py -3 galaxy_invaders_swapi.py`.
3. É necessária internet apenas para receber os dados da API. Sem internet, o jogo continua funcionando.
4. Controles: **WASD/setas** (mover), **Espaço** (atirar), **R** (reiniciar após Game Over), **C** (consultar API novamente).

Nenhum pacote externo precisa ser instalado via pip.

## Como demonstrar a API ao professor

1. Abra o jogo Python **com o terminal visível**.
2. No terminal aparecem `GET https://swapi.info/api/starships`, o status HTTP e a quantidade de naves recebidas.
3. No rodapé do jogo deverá aparecer **SWAPI: CONECTADA (N naves)** caso a consulta tenha sucesso.
4. Veja a nave selecionada e o valor MGLT logo abaixo do título do jogo. O atributo MGLT afeta a velocidade.
5. Aperte **C** para refazer a requisição e mostrar novo GET em tempo real.
6. Se estiver sem internet, aparecerá **SWAPI: OFFLINE**. Isso não demonstra uma consulta bem-sucedida; conecte-se e aperte C para repetir.

## Publicar no GitHub

Envie os arquivos para o repositório. Para hospedar o jogo no navegador, ative **GitHub Pages** apontando para a branch `main` e a pasta `/(root)`: ele serve o **`index.html`**. O arquivo Python continua disponível no repositório, mas **não é executado pelo GitHub Pages**.

O jogo não é afiliado aos titulares da franquia Star Wars.
