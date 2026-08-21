# ERP

API FastAPI de produtos, com PostgreSQL e SQL puro via `psycopg`.

## Requisitos

- [uv](https://docs.astral.sh/uv/)
- Python 3.14+
- Docker (opcional, para subir API + banco juntos)

Os comandos abaixo devem ser executados a partir desta pasta (`erp/`).

## Execução com Docker

Sobe PostgreSQL e a API, aplica as migrations e expõe o serviço na porta 8000:

```bash
make docker-up
```

Equivalente a `docker compose up --build`.

A API fica em `http://localhost:8000`. Documentação interativa:

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Para parar:

```bash
make docker-down
```

## Execução local

1. Instale as dependências:

```bash
make install
```

2. Copie o arquivo de ambiente (já existe um `.env.example`):

```bash
cp .env.example .env
```

O valor padrão espera o banco em `localhost:5432`:

```
DATABASE_URL=postgresql://erp:erp@localhost:5432/erp
CORS_ORIGINS=["http://localhost:8000"]
```

3. Suba só o PostgreSQL (se ainda não estiver rodando):

```bash
docker compose up -d postgres
```

4. Aplique as migrations:

```bash
make migrate
```

5. Inicie a API com reload:

```bash
make run
```

A API sobe em `http://localhost:8000`.

## API de produtos

Todas as rotas de escrita exigem o header `X-Actor-Id` (inteiro que identifica quem criou/alterou/removeu o registro).

| Método   | Caminho            | Descrição                          |
|----------|--------------------|------------------------------------|
| `POST`   | `/products`        | Cria produto                       |
| `GET`    | `/products`        | Lista produtos (`offset`, `limit`) |
| `GET`    | `/products/{id}`   | Busca produto por id               |
| `PUT`    | `/products/{id}`   | Atualiza produto                   |
| `DELETE` | `/products/{id}`   | Soft delete                        |

Exemplo de criação:

```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -H "X-Actor-Id: 1" \
  -d '{"name": "Teclado", "price": "199.90", "stock_quantity": 10}'
```

## Testes e qualidade

```bash
make test
make lint
make format
```

Os testes unitários usam repositório em memória e não precisam do PostgreSQL.

## Migrations

Os arquivos SQL ficam em `migrations/` e são aplicados pelo runner `python -m app.config.migrations` (`make migrate`). No Docker, as migrations rodam automaticamente antes do uvicorn.

## Uso de IA

Toda a implementação deste projeto — código, testes, Docker, migrations, README e ajustes de arquitetura — foi feita por IA.

A geração seguiu a skill de arquitetura em [`.agents/skills/fastapi-architecture-skill.md`](.agents/skills/fastapi-architecture-skill.md), que define a organização por domínio, a separação entre HTTP, casos de uso e persistência, e as regras de Clean Architecture / Ports and Adapters usadas no código.

---

## Questões teóricas

### Parte 1: Arquitetura e Organização

#### 1. Microsserviços, comunicação, persistência e observabilidade

Eu organizaria a arquitetura utilizando microsserviços com responsabilidades bem definidas. O módulo de Pedidos seria separado do módulo de Estoque, além dos serviços já existentes de Clientes e Financeiro. Cada serviço seria responsável pelos seus próprios dados e não acessaria diretamente o banco de dados de outro serviço.

O Pedido Service seria responsável pela criação e gerenciamento do ciclo de vida dos pedidos. O Estoque Service seria responsável pela disponibilidade, reserva, liberação e confirmação da venda dos produtos. O Cliente Service continuaria responsável pelos dados e validações dos clientes, enquanto o Financeiro Service seria responsável pelo processamento dos pagamentos.

A comunicação seria híbrida, utilizando REST para operações que precisam de uma resposta imediata e comunicação assíncrona por meio de filas para processos que podem ser executados posteriormente.

Por exemplo, ao criar um pedido, o Pedido Service poderia realizar uma chamada REST ao Cliente Service para verificar se o cliente existe e está apto a realizar o pedido. Depois disso, o pedido seria criado com o status `AGUARDANDO_ESTOQUE` e seria publicado um evento `PedidoCriado` em uma fila.

O Estoque Service consumiria esse evento e verificaria a disponibilidade dos produtos. Caso exista estoque, faria uma reserva e publicaria um evento `EstoqueReservado`. Caso não exista, poderia publicar um evento informando a indisponibilidade e o Pedido Service cancelaria o pedido.

Após a reserva do estoque, o Pedido Service poderia publicar um evento `PagamentoSolicitado`, consumido pelo Financeiro Service. O Financeiro processaria o pagamento e publicaria um evento informando se o pagamento foi aprovado ou recusado.

Caso o pagamento seja aprovado, o Pedido Service publicaria um evento para o Estoque Service confirmando a venda. Caso seja recusado, seria publicado um evento para liberar a reserva do estoque e o pedido seria cancelado.

Para persistência, utilizaria PostgreSQL. Cada microsserviço teria seu próprio banco ou, no mínimo, seu próprio schema e seria responsável exclusivamente pelos seus dados. Isso evita acoplamento direto entre os serviços e permite que cada serviço evolua de maneira independente.

O Redis poderia ser utilizado para cache de informações que são consultadas com frequência, como dados de produtos ou clientes, reduzindo a quantidade de consultas ao PostgreSQL. Também poderia ser utilizado em situações que exigissem locks distribuídos ou armazenamento temporário. Para o processamento das mensagens, eu utilizaria uma solução específica de mensageria, como RabbitMQ.

O API Gateway, como o Kong, ficaria como ponto de entrada das requisições externas. Ele seria responsável por roteamento, autenticação e autorização, rate limiting, TLS e outras preocupações transversais. Dessa forma, os clientes não precisariam conhecer diretamente a localização dos microsserviços.

Para observabilidade, utilizaria logs, métricas e tracing distribuído. Prometheus e Grafana poderiam ser utilizados para métricas e dashboards, enquanto OpenTelemetry poderia ser utilizado para tracing. Os logs deveriam ser estruturados e possuir um `trace_id` ou `correlation_id` para permitir acompanhar uma operação entre diferentes microsserviços.

Em um ERP, eu priorizaria o monitoramento de disponibilidade dos serviços, erros, latência das APIs, quantidade e tempo de processamento das mensagens nas filas, falhas de pagamento, problemas de reserva de estoque, indisponibilidade de banco de dados e indicadores relacionados aos principais processos de negócio, como pedidos criados, aprovados e cancelados.

#### 2. Organização de um serviço FastAPI de médio/grande porte

Para um serviço FastAPI de médio ou grande porte, eu utilizaria uma arquitetura inspirada principalmente em Clean Architecture e Arquitetura Hexagonal (Ports and Adapters), com alguns conceitos de DDD para organizar os domínios de negócio.

Eu evitaria organizar todo o projeto apenas por tipo técnico, como `routers/`, `services/`, `repositories/` e `models/` contendo todos os domínios juntos. Em projetos maiores, prefiro organizar primeiro por domínio e, dentro de cada domínio, separar as responsabilidades.

Uma possível estrutura seria:

```text
app/
├── main.py
├── core/
│   ├── config.py
│   ├── database.py
│   └── security.py
│
├── http/
│   ├── dependencies.py
│   └── middleware.py
│
├── orders/
│   ├── domain.py
│   ├── service.py
│   ├── schemas.py
│   ├── router.py
│   ├── repository.py
│   ├── postgres/
│   │   └── repository.py
│   └── mock/
│       └── repository.py
│
├── products/
│   ├── domain.py
│   ├── service.py
│   ├── schemas.py
│   ├── router.py
│   ├── repository.py
│   ├── postgres/
│   │   └── repository.py
│   └── mock/
│       └── repository.py
│
└── tests/
    ├── orders/
    └── products/
```

O `main.py` seria o ponto de entrada da aplicação. Ele teria apenas responsabilidades de inicialização, como criar a aplicação FastAPI, registrar middlewares, configurar dependências e incluir os routers. A regra seria não colocar lógica de negócio nessa camada.

A pasta `core` concentraria configurações e componentes compartilhados relacionados à infraestrutura da aplicação, como variáveis de ambiente, configuração do banco, segurança e autenticação. Ela não deveria conter regras específicas de um domínio de negócio.

A camada `http` seria responsável por preocupações relacionadas ao transporte HTTP que são compartilhadas pela aplicação, como middlewares e dependências do FastAPI.

Dentro de cada domínio, eu manteria a separação das responsabilidades.

O `router.py` seria o adapter de entrada. Ele receberia a requisição HTTP, validaria/interpretaria os dados através dos schemas do Pydantic e chamaria o serviço ou caso de uso. O router não deveria conter regra de negócio.

O `schemas.py` conteria os modelos de entrada e saída da API utilizando Pydantic. Por exemplo, `CreateOrderRequest` e `OrderResponse`. Esses schemas representam o contrato da API e, por isso, não deveriam ser utilizados como entidades de domínio.

O `domain.py` conteria as entidades e contratos relacionados ao domínio, além das interfaces necessárias, como a interface do Repository ou de um UseCase. A ideia é que essa camada não conheça FastAPI, Pydantic, PostgreSQL ou qualquer detalhe de infraestrutura.

O `service.py` seria responsável pelos casos de uso e regras de negócio. Por exemplo, ao criar um pedido, poderia verificar regras de negócio, consultar o repositório e coordenar as operações necessárias. Essa camada dependeria de abstrações, e não diretamente de uma implementação específica do PostgreSQL.

O `repository.py` definiria a porta de saída para persistência. Ele poderia possuir uma interface como `OrderRepository`, que seria utilizada pelo serviço.

A pasta `postgres/` conteria o adapter de saída, ou seja, a implementação concreta do repository utilizando PostgreSQL. Dessa forma, o serviço não precisaria saber se os dados estão sendo armazenados em PostgreSQL, SQLite ou outro banco.

A pasta `mock/` conteria implementações utilizadas nos testes. Isso permite testar o serviço isoladamente sem precisar subir um banco de dados real.

Isso permite substituir o PostgreSQL sem alterar a regra de negócio.

Essa estrutura também facilita bastante a testabilidade. Por exemplo, para testar a criação de um pedido, eu não precisaria subir o FastAPI nem o PostgreSQL. Poderia criar um mock do `OrderRepository` e testar apenas o `OrderService`, verificando se as regras de negócio estão funcionando corretamente.

Também separaria testes por responsabilidade:

```text
tests/
├── orders/
│   ├── test_service.py
│   ├── test_router.py
│   └── test_repository.py
└── products/
    ├── test_service.py
    ├── test_router.py
    └── test_repository.py
```

Os testes do service seriam principalmente testes unitários, utilizando mocks para as dependências. Os testes do router poderiam verificar o comportamento da API e os códigos HTTP. Já os testes do repository poderiam ser testes de integração utilizando um banco de dados de teste.

Os principais princípios utilizados seriam:

- **Clean Architecture:** para separar regras de negócio de frameworks e infraestrutura.
- **Arquitetura Hexagonal:** para tratar HTTP e PostgreSQL como adapters externos e manter o domínio dependente de abstrações (ports).
- **SOLID:** principalmente o Single Responsibility Principle, Dependency Inversion Principle e Open/Closed Principle. Por exemplo, o service não dependeria diretamente de uma implementação do PostgreSQL, mas de uma abstração de repository.
- **DDD:** utilizaria a separação por domínio e conceitos como entidades.

Um princípio importante seria manter o baixo acoplamento entre domínios. Por exemplo, o domínio de pedidos não deveria importar diretamente a implementação do domínio de estoque. Quando fosse necessário integrar os dois, utilizaria uma abstração ou, dependendo do contexto, eventos/mensageria.

Com essa organização, uma mudança no framework HTTP ou no banco de dados teria impacto principalmente nos adapters, enquanto as regras de negócio permaneceriam isoladas. Isso facilita manutenção, evolução e principalmente testes, pois cada camada pode ser testada de maneira independente.

### Parte 2: Assíncrono e Concorrência

#### 3. asyncio, threading e multiprocessing

O `asyncio` é uma biblioteca padrão do Python para escrever código concorrente, utilizando um modelo assíncrono baseado em um event loop. Usando o exemplo da documentação do FastAPI, podemos imaginar uma função `get_burgers()`: você faz o pedido, recebe uma comanda e, enquanto espera o pedido ficar pronto, pode seguir para outra tarefa. Quando o pedido estiver pronto, o programa pode voltar para essa tarefa.

Nesse caso, estamos falando de concorrência, e não necessariamente de várias threads. O `asyncio` normalmente executa as coroutines em uma única thread, alternando entre elas principalmente durante operações de I/O, como requisições HTTP, acesso a banco ou leitura de arquivos.

Em um ERP, eu usaria `asyncio`, por exemplo, para chamar 3 APIs externas ao mesmo tempo. Em vez de esperar a primeira API responder para depois chamar a segunda e a terceira, poderia fazer as três requisições de forma concorrente, reduzindo o tempo total de espera.

O `threading` também permite executar tarefas de forma concorrente utilizando threads. É uma alternativa interessante principalmente para tarefas que ficam muito tempo esperando I/O. Diferente do `asyncio`, nesse caso temos múltiplas threads dentro do mesmo processo.

Por exemplo, em um ERP, poderia utilizar threads para executar várias operações de I/O que precisam bloquear, como chamadas para APIs externas ou bibliotecas que não possuem suporte assíncrono.

Já o `multiprocessing` utiliza múltiplos processos. Nesse caso, podemos ter diferentes processos executando tarefas em paralelo e, quando houver múltiplos núcleos disponíveis, essas tarefas podem ser executadas simultaneamente em diferentes núcleos da CPU.

Usando uma analogia, se fosse necessário limpar uma casa grande, poderíamos ter vários workers, cada um responsável por limpar um cômodo. Diferentemente do `threading`, cada worker estaria em um processo separado.

O `multiprocessing` é mais indicado para tarefas CPU-bound, ou seja, tarefas que exigem bastante processamento da CPU.

Em um ERP, um exemplo seria processar um arquivo CSV muito grande realizando cálculos complexos em milhares ou milhões de registros. Outro exemplo seria gerar um relatório pesado em PDF que exige bastante processamento. Nesses casos, poderíamos dividir o processamento entre múltiplos processos para aproveitar os núcleos da CPU.

Resumindo:

- **asyncio:** concorrência em uma thread, ideal principalmente para operações de I/O assíncronas.
- **threading:** múltiplas threads dentro do mesmo processo, útil principalmente para tarefas de I/O bloqueante.
- **multiprocessing:** múltiplos processos, indicado principalmente para tarefas que exigem bastante CPU.

### Parte 6: Pergunta de Perfil

#### 10. Go para um serviço de alta concorrência

Eu consideraria uma responsabilidade grande, mas aceitaria o desafio, pois acredito que é uma decisão que pode trazer grandes resultados para a empresa e também bastante crescimento pessoal e profissional na minha carreira.

Acho que o Go é uma escolha razoável para esse cenário, principalmente por ser uma linguagem que possui um bom suporte para concorrência através das goroutines, que são muito leves e gerenciadas pelo runtime do Go. Isso permite trabalhar com uma grande quantidade de tarefas concorrentes sem o mesmo overhead de criar uma thread tradicional para cada tarefa.

Além disso, Go possui um runtime relativamente simples, garbage collector eficiente e gera um binário compilado que pode ser executado diretamente. Isso também facilita o deploy. Dependendo da estratégia utilizada para criar a imagem Docker, é possível ter imagens bastante pequenas, o que ajuda quando precisamos criar várias instâncias do serviço e pode reduzir custos de infraestrutura.

Por essas características, considero Go uma boa escolha para um serviço que precisa trabalhar com alta concorrência, baixa latência e alto throughput, principalmente para uma frente específica do produto que tenha esse perfil de necessidade.

Caso eu discordasse da escolha, primeiro tentaria entender quais são os requisitos técnicos que levaram à decisão, como volume de eventos, latência esperada, throughput e consumo de recursos. A partir desses requisitos, compararia outras alternativas, como continuar utilizando Python com soluções assíncronas, utilizar outra linguagem ou até utilizar uma solução baseada em filas e processamento distribuído. A decisão deveria ser baseada nos requisitos e nos resultados de benchmarks, e não apenas na preferência por uma linguagem.

Caso concordasse com a escolha, mas não tivesse experiência prévia com Go, começaria estudando a documentação oficial para entender a sintaxe e os principais conceitos da linguagem. Também leria uma parte do livro *A Linguagem de Programação Go* para entender melhor a linguagem e seus principais recursos.

Depois, estudaria principalmente o capítulo de concorrência para entender como funcionam as goroutines, channels e o modelo de concorrência do Go. Para aprofundar esse conhecimento, estudaria também o livro *Concurrency in Go*, principalmente os conceitos relacionados à construção de sistemas concorrentes.

Para conseguir entregar o serviço com qualidade, não ficaria apenas no estudo teórico. Eu começaria implementando pequenas partes do serviço e utilizando testes para entender o comportamento da aplicação. Também buscaria entender os padrões e práticas já utilizados pela equipe, fazendo code reviews e buscando feedback de outros desenvolvedores.

Dessa forma, conseguiria aprender a linguagem ao mesmo tempo em que desenvolveria a solução de maneira incremental, validando performance e qualidade durante o desenvolvimento, em vez de tentar aprender toda a linguagem antes de começar a entregar.

### Parte 7: Portfólio

#### 11. GitHub

GitHub: https://github.com/fernandojunqueira

Atualmente, não tenho um projeto pessoal relevante para representar meu nível técnico.
