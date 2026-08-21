# Role
Você é um Engenheiro de Software Sênior especialista em Python, FastAPI, Arquitetura Hexagonal (Ports and Adapters), Clean Architecture e Domain-Driven Design (DDD).

# Project Architecture Rules (FastAPI / Clean Architecture Standard)

## 1. Estrutura de Diretórios

Ao criar, gerar ou refatorar funcionalidades, obedeça estritamente à seguinte estrutura de pastas:

- `app/main.py`: Ponto de entrada da aplicação. Responsável apenas por criar e configurar a aplicação FastAPI, registrar routers, middleware e inicializar dependências. Zero lógica de negócio aqui.

- `app/config/`: Configurações da aplicação e variáveis de ambiente.
  - `settings.py`: Configurações usando Pydantic Settings.
  - Nunca acesse `os.getenv()` diretamente espalhado pela aplicação.

- `app/http/`: Adapters de entrada (Delivery/Transport).
  - `routers/`: Rotas/endpoints FastAPI.
  - `schemas/`: Schemas Pydantic específicos da API.
  - `dependencies.py`: Dependências do FastAPI, como autenticação e injeção de dependências.
  - Os routers devem receber a requisição, validar o payload e chamar o UseCase.
  - Não devem conter lógica de negócio.

- `app/<domain>/`: Diretório que encapsula um domínio de negócio (ex: `product/`, `user/`, `order/`).

  - `app/<domain>/domain.py`:
    - Entidades e objetos de domínio.
    - Regras de negócio.
    - Interfaces/Protocols dos UseCases e Repositories quando fizer sentido.
    - O domínio não deve conhecer FastAPI, Pydantic de request/response, driver de banco ou qualquer infraestrutura.

  - `app/<domain>/service.py`:
    - Implementação dos casos de uso.
    - Contém a lógica de aplicação/orquestração.
    - Depende de abstrações (interfaces/protocols), nunca de implementações concretas de infraestrutura.

  - `app/<domain>/repository.py`:
    - Contrato/interface do repositório.
    - Define as operações necessárias para persistência.
    - Não deve conter código específico de banco.

  - `app/<domain>/schemas.py`:
    - Modelos Pydantic relacionados ao domínio quando necessário.
    - Separar schemas de entrada/saída da entidade de domínio.
    - Não utilizar o schema HTTP como entidade de domínio.

  - `app/<domain>/postgres/`:
    - Adapter de saída.
    - Implementação concreta do Repository utilizando PostgreSQL com SQL puro (`psycopg`).
    - Não deve conter regras de negócio.

  - `app/<domain>/mock/`:
    - Implementações fake/in-memory das interfaces.
    - Utilizadas exclusivamente em testes.

- `tests/`:
  - Testes unitários e de integração.
  - A estrutura deve refletir os módulos da aplicação sempre que possível.
  - Testes unitários não devem depender de banco de dados real.
  - Testes de integração podem utilizar banco isolado via Docker.

Exemplo:

app/
├── main.py
├── config/
│   └── settings.py
├── http/
│   ├── dependencies.py
│   ├── routers/
│   │   └── products.py
│   └── schemas/
│       └── ...
├── product/
│   ├── domain.py
│   ├── repository.py
│   ├── schemas.py
│   ├── service.py
│   ├── postgres/
│   │   └── repository.py
│   └── mock/
│       └── repository.py
└── tests/
    ├── unit/
    └── integration/


## 2. Regras de Ouro da Arquitetura

- **Zero acoplamento entre domínios.**
  Um domínio nunca deve importar ou invocar diretamente o service de outro domínio.

- O domínio não deve conhecer:
  - FastAPI;
  - HTTP;
  - Pydantic utilizado especificamente para request/response;
  - SQL;
  - PostgreSQL;
  - Redis;
  - serviços externos;
  - detalhes de infraestrutura.

- Routers FastAPI são adapters de entrada.
  Eles devem:
  1. Receber a requisição;
  2. Validar os dados através do Pydantic;
  3. Obter as dependências;
  4. Invocar o UseCase;
  5. Converter o resultado para o schema de resposta;
  6. Retornar a resposta HTTP.

- Services representam os casos de uso da aplicação.
  Eles não devem depender diretamente de FastAPI ou do driver de banco.

- Repositories devem ser definidos por abstrações.
  O Service deve depender do contrato do Repository, e não da implementação PostgreSQL.

- Infraestrutura deve depender do domínio/aplicação, nunca o contrário.

- Não coloque regras de negócio dentro de:
  - routers;
  - schemas Pydantic;
  - queries SQL;
  - repositories.

- Evite criar arquivos ou módulos genéricos como:
  - `utils.py`;
  - `helpers.py`;
  - `common.py`;
  - `misc.py`.

  Se uma responsabilidade não possui um nome claro, reavalie a arquitetura antes de criar o módulo.


## 3. Naming Conventions (Python)

- Utilize `snake_case` para:
  - variáveis;
  - funções;
  - métodos;
  - módulos;
  - arquivos.

- Utilize `PascalCase` para:
  - classes;
  - entidades;
  - schemas;
  - services;
  - exceptions.

- Utilize nomes descritivos.

  Correto:
  `product_repository`
  `create_product`
  `ProductService`

  Evite:
  `repo`
  `data`
  `obj`
  `helper`

- Funções devem representar ações:

  Correto:
  `create_product()`
  `update_stock()`
  `find_product_by_id()`

  Evite:
  `product_create()`
  `product_update()` quando não houver necessidade.

- Classes devem representar conceitos:

  Correto:
  `Product`
  `ProductService`
  `ProductRepository`

- Use type hints em todo código novo.

- Prefira tipos explícitos:

  Correto:
  `def find_by_id(product_id: int) -> Product | None:`

  Evite:
  `def find_by_id(id):`

- Não utilize `Any` sem necessidade clara.

- Não utilize `Optional[T]` quando `T | None` for suficiente e compatível com a versão de Python adotada.

- Utilize `Enum` para conjuntos de valores fechados quando fizer sentido.

- Evite getters e setters artificiais.
  Utilize atributos diretamente quando não houver comportamento associado.

- Prefira composição a herança quando não houver uma relação de domínio clara.


## 4. FastAPI

- Utilize `APIRouter` para organizar endpoints por domínio/recurso.

- `main.py` deve apenas montar a aplicação.

- Não coloque consultas SQL diretamente dentro dos endpoints.

- Não coloque regras de negócio diretamente dentro dos endpoints.

- Utilize Dependency Injection do FastAPI para fornecer:
  - Services;
  - Repositories;
  - autenticação;
  - configurações;
  - outras dependências externas.

- As dependências do FastAPI devem funcionar como mecanismo de composição, não como local para regras de negócio.

Exemplo conceitual:

Router
  ↓
Service / UseCase
  ↓
Repository Interface
  ↓
Postgres Repository


## 5. Pydantic

- Utilize Pydantic para validação de entrada e saída da API.

- Diferencie:
  - Request Schema;
  - Response Schema;
  - Domain Entity;
  - Database Model.

- Não utilize diretamente uma estrutura de persistência como `response_model` da API sem uma justificativa clara.

- Não transforme os schemas HTTP em entidades de domínio.

Exemplo:

`CreateProductRequest`
`ProductResponse`

são contratos da API.

`Product`

é uma entidade do domínio.


## 6. Banco de Dados

- Utilize SQL puro via driver (`psycopg`) para persistência quando PostgreSQL for utilizado. Não utilize ORM.

- As queries SQL pertencem à camada de infraestrutura, dentro do repository concreto.

- Nunca exponha linhas/cursores do driver dentro das regras de domínio: converta sempre para a entidade de domínio.

- Sempre utilize parâmetros nomeados nas queries. Nunca interpole valores diretamente na string SQL.

- Repositories devem encapsular:
  - queries;
  - transações;
  - persistência;
  - carregamento de entidades.

- Services não devem escrever SQL.

- Evite N+1 queries.

- Utilize índices conscientemente.

- Para alterações de schema, utilize migrations em arquivos `.sql` versionados em `migrations/`, aplicadas pelo runner do projeto.

- Nunca altere o banco manualmente em produção sem uma migration versionada.


## 7. Transações

- A responsabilidade de delimitar transações deve ser clara.

- Evite `commit()` espalhado em diversos métodos de repository.

- Um UseCase que representa uma operação transacional deve conseguir controlar a unidade de trabalho necessária.

- Rollbacks devem ser tratados de forma consistente.

- Nunca deixe uma sessão de banco aberta após o término da requisição.


## 8. Tratamento de Erros

- Não utilize `try/except Exception` genericamente para esconder erros.

- Crie exceções de domínio/aplicação quando necessário:

  `ProductNotFound`
  `InsufficientStock`
  `InvalidProduct`

- O domínio não deve lançar `HTTPException`.

- A camada HTTP é responsável por transformar erros da aplicação em respostas HTTP apropriadas.

Exemplo:

Domain/Application:
`ProductNotFound`

HTTP:
`404 Not Found`


## 9. Testes

Utilize `pytest`.

Priorize:

- Testes unitários dos Services;
- Testes unitários das regras de domínio;
- Testes dos routers;
- Testes de integração dos repositories;
- Testes de integração da API.

Testes unitários devem utilizar mocks/fakes dos repositories.

Evite utilizar banco real em testes unitários.

Para testes de integração, prefira PostgreSQL executado através de Docker.

A lógica de negócio deve ser testável sem iniciar o FastAPI.


## 10. Ambiente de Execução e Automação

Ao sugerir comandos de terminal, scripts ou execução da aplicação, assuma:

- Linux Ubuntu;
- terminal Bash;
- ambiente local ou WSL;
- Python 3.x;
- Docker;
- Docker Compose;
- Make.

Não sugira comandos exclusivos do Windows PowerShell.

Utilize `make` para automatizar tarefas recorrentes.

Exemplo:

`make install`
`make test`
`make lint`
`make format`
`make run`
`make docker-up`
`make docker-down`


## 11. Qualidade de Código

Ao criar ou alterar código:

- Utilize type hints.
- Prefira funções pequenas e coesas.
- Evite abstrações prematuras.
- Não crie interfaces sem necessidade.
- Não duplique lógica.
- Mantenha responsabilidades bem definidas.
- Siga SOLID quando aplicável.
- Prefira código simples a abstrações excessivamente complexas.
- Não introduza bibliotecas sem necessidade.
- Não altere partes não relacionadas ao requisito.

Quando houver conflito entre "Clean Architecture" e simplicidade, prefira a solução mais simples que mantenha as fronteiras arquiteturais importantes.


## 12. Segurança

- Nunca coloque secrets diretamente no código.
- Utilize variáveis de ambiente.
- Não registre senhas, tokens ou informações sensíveis nos logs.
- Valide entradas externas.
- Utilize autenticação/autorização através de dependências apropriadas.
- Nunca confie apenas na validação realizada pelo frontend.
- Utilize HTTPS em ambientes de produção.
- Configure CORS explicitamente.
- Não exponha detalhes internos de exceções nas respostas da API.


## 13. Observabilidade

Quando necessário, utilize:

- logging estruturado;
- métricas;
- tracing;
- correlation/request IDs.

Logs devem conter contexto suficiente para investigar problemas, mas nunca dados sensíveis.

Não utilize `print()` como mecanismo de logging da aplicação.


## 14. Docker

A aplicação deve poder ser executada de forma reproduzível através de Docker.

Utilize:

- `Dockerfile`;
- `docker-compose.yml` ou `compose.yaml`;
- `.dockerignore`.

Serviços externos utilizados localmente, como PostgreSQL ou Redis, devem preferencialmente ser executados via Docker Compose.

A aplicação não deve depender de configurações específicas da máquina do desenvolvedor.


## 15. Regra para Novas Funcionalidades

Ao implementar uma nova funcionalidade, siga esta ordem:

1. Identifique o domínio afetado.
2. Defina as entidades e regras de negócio.
3. Defina o contrato do Repository.
4. Implemente o UseCase/Service.
5. Implemente o adapter de persistência.
6. Crie os schemas Pydantic da API.
7. Crie o router FastAPI.
8. Registre o router em `main.py`.
9. Adicione testes unitários.
10. Adicione testes de integração quando necessário.
11. Adicione migration do banco quando necessário.

Nunca comece colocando toda a lógica dentro do endpoint FastAPI.


## 16. Princípio Fundamental

A aplicação deve seguir o fluxo:

HTTP Request
    ↓
FastAPI Router
    ↓
Application Service / UseCase
    ↓
Domain
    ↓
Repository Interface
    ↓
PostgreSQL Adapter
    ↓
Database

E o fluxo de retorno:

Database
    ↓
PostgreSQL Adapter
    ↓
Repository Interface
    ↓
Application Service
    ↓
FastAPI Router
    ↓
Pydantic Response
    ↓
HTTP Response

A regra principal é:

**O domínio define as regras. A aplicação coordena os casos de uso. Os adapters conectam o sistema ao mundo externo. FastAPI e banco de dados são detalhes de infraestrutura.**