CREATE TABLE IF NOT EXISTS clientes (
    id        INTEGER PRIMARY KEY,
    nome      TEXT    NOT NULL,
    cidade    TEXT    NOT NULL,
    estado    TEXT    NOT NULL,
    segmento  TEXT    NOT NULL,
    ativo     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS produtos (
    id              INTEGER PRIMARY KEY,
    descricao       TEXT    NOT NULL,
    categoria       TEXT    NOT NULL,
    preco_unitario  REAL    NOT NULL,
    estoque_atual   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pedidos (
    id           INTEGER PRIMARY KEY,
    cliente_id   INTEGER NOT NULL REFERENCES clientes(id),
    produto_id   INTEGER NOT NULL REFERENCES produtos(id),
    quantidade   INTEGER NOT NULL,
    valor_total  REAL    NOT NULL,
    status       TEXT    NOT NULL,
    data_pedido  TEXT    NOT NULL
);

INSERT OR IGNORE INTO clientes VALUES
  (1, 'Mercado Central Ltda',   'São Paulo',   'SP', 'Varejo',      1),
  (2, 'Distribuidora Norte SA', 'Manaus',       'AM', 'Atacado',     1),
  (3, 'Farmácia Saúde Boa',     'Curitiba',     'PR', 'Saúde',       1),
  (4, 'Tech Soluções ME',       'Florianópolis','SC', 'Tecnologia',  1),
  (5, 'Construtora Horizonte',  'Belo Horizonte','MG','Construção',  0);

INSERT OR IGNORE INTO produtos VALUES
  (1, 'ERP Módulo Financeiro',   'Software',   3500.00, 50),
  (2, 'ERP Módulo Estoque',      'Software',   2800.00, 50),
  (3, 'Suporte Técnico Mensal',  'Serviço',     450.00, 999),
  (4, 'Licença Adicional Usuário','Software',   800.00, 200),
  (5, 'Consultoria de Implantação','Serviço',  5000.00, 999);

INSERT OR IGNORE INTO pedidos VALUES
  (1, 1, 1, 1, 3500.00, 'aprovado',  '2025-01-10'),
  (2, 1, 3, 1,  450.00, 'aprovado',  '2025-01-15'),
  (3, 2, 2, 1, 2800.00, 'aprovado',  '2025-02-01'),
  (4, 2, 4, 3, 2400.00, 'pendente',  '2025-02-14'),
  (5, 3, 5, 1, 5000.00, 'aprovado',  '2025-02-20'),
  (6, 3, 3, 1,  450.00, 'aprovado',  '2025-03-01'),
  (7, 4, 1, 1, 3500.00, 'pendente',  '2025-03-05'),
  (8, 4, 2, 1, 2800.00, 'cancelado', '2025-03-10'),
  (9, 5, 3, 2,  900.00, 'aprovado',  '2025-03-12'),
 (10, 1, 4, 2, 1600.00, 'aprovado',  '2025-03-20');
