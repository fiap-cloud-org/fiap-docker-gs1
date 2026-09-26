-- O cliente do entrypoint do MySQL usa latin1 por padrão; sem isso os acentos viram mojibake
SET NAMES utf8mb4;

-- Criando o banco de dados (caso use um único banco)
CREATE DATABASE IF NOT EXISTS ecommerce_db;
USE ecommerce_db;

-- Tabela Clientes
CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);

-- Tabela Usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL
);

-- Tabela Permissões
CREATE TABLE IF NOT EXISTS permissoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) UNIQUE NOT NULL
);

-- Tabela Categorias (deve vir antes de produtos)
CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL
);

-- Tabela Produtos
CREATE TABLE IF NOT EXISTS produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    preco DECIMAL(10,2) NOT NULL,
    categoria_id INT,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

-- Tabela Estoque
CREATE TABLE IF NOT EXISTS estoque (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    quantidade INT NOT NULL,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

-- Tabela Orçamentos
CREATE TABLE IF NOT EXISTS orcamento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    status ENUM('Pendente', 'Aprovado', 'Rejeitado') NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- Tabela Fornecedores
CREATE TABLE IF NOT EXISTS fornecedores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    contato VARCHAR(100)
);

-- Tabela Lojas
CREATE TABLE IF NOT EXISTS lojas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    endereco VARCHAR(255),
    contato VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela Formas de Pagamento
CREATE TABLE IF NOT EXISTS pagamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metodo VARCHAR(50) NOT NULL
);

-- Tabela Pedidos
CREATE TABLE IF NOT EXISTS pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Pendente', 'Pago', 'Enviado', 'Entregue') NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- Tabela Itens do Pedido
CREATE TABLE IF NOT EXISTS items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade INT NOT NULL,
    preco DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

-- Tabela Avaliações
CREATE TABLE IF NOT EXISTS avaliacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    cliente_id INT NOT NULL,
    nota INT NOT NULL CHECK(nota BETWEEN 1 AND 5),
    comentario TEXT,
    FOREIGN KEY (produto_id) REFERENCES produtos(id),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- Tabela Frete
CREATE TABLE IF NOT EXISTS frete (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    prazo INT NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
);

-- Inserir dados iniciais para permitir funcionamento do microserviço

-- Inserir categorias de exemplo
INSERT IGNORE INTO categorias (id, nome) VALUES 
(1, 'Eletrônicos'),
(2, 'Roupas'),
(3, 'Casa e Jardim'),
(4, 'Livros'),
(5, 'Esportes');

-- Inserir clientes de exemplo
INSERT IGNORE INTO clientes (id, nome, email) VALUES 
(1, 'Ana Silva', 'ana.silva@email.com'),
(2, 'Carlos Santos', 'carlos.santos@email.com'),
(3, 'Maria Oliveira', 'maria.oliveira@email.com'),
(4, 'João Ferreira', 'joao.ferreira@email.com'),
(5, 'Lucia Costa', 'lucia.costa@email.com');

-- Inserir produtos de exemplo
INSERT IGNORE INTO produtos (id, nome, descricao, preco, categoria_id) VALUES 
(1, 'Smartphone Samsung Galaxy', 'Smartphone com tela de 6.5 polegadas, 128GB de armazenamento', 899.99, 1),
(2, 'Notebook Dell Inspiron', 'Notebook com processador Intel i5, 8GB RAM, 256GB SSD', 2499.99, 1),
(3, 'Camiseta Polo', 'Camiseta polo masculina 100% algodão, diversas cores', 59.90, 2),
(4, 'Jeans Feminino', 'Calça jeans feminina skinny, diversos tamanhos', 89.90, 2),
(5, 'Cafeteira Elétrica', 'Cafeteira elétrica programável para 12 xícaras', 129.90, 3),
(6, 'Aspirador de Pó', 'Aspirador de pó com filtro HEPA, 1400W', 299.99, 3),
(7, 'O Alquimista', 'Livro "O Alquimista" de Paulo Coelho', 24.90, 4),
(8, 'Sapiens', 'Livro "Sapiens: Uma Breve História da Humanidade"', 39.90, 4),
(9, 'Tênis Running', 'Tênis para corrida com amortecimento avançado', 199.99, 5),
(10, 'Bicicleta Mountain Bike', 'Bicicleta mountain bike aro 29, 21 marchas', 899.99, 5);

-- Inserir estoque para os produtos
INSERT IGNORE INTO estoque (produto_id, quantidade) VALUES 
(1, 25),
(2, 15),
(3, 50),
(4, 30),
(5, 20),
(6, 12),
(7, 100),
(8, 75),
(9, 40),
(10, 8);

-- Inserir lojas de exemplo
INSERT IGNORE INTO lojas (id, nome, descricao, endereco, contato) VALUES 
(1, 'Empório Vila Nova', 'Bebidas e mercearia', 'Rua dos Pinheiros, 450', '11940028922'),
(2, 'Loja Centro', 'Eletrônicos e acessórios', 'Rua das Flores, 123', '11987654321'),
(3, 'Mega Store', 'Variedades em geral', 'Av. Paulista, 1000', '11123456789');

-- Tabela para associar produtos às lojas
CREATE TABLE IF NOT EXISTS produtos_lojas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loja_id INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade_estoque INT DEFAULT 0,
    preco_loja DECIMAL(10,2),
    FOREIGN KEY (loja_id) REFERENCES lojas(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE,
    UNIQUE KEY unique_loja_produto (loja_id, produto_id)
);

-- Tabela para histórico de vendas por loja
CREATE TABLE IF NOT EXISTS vendas_lojas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loja_id INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade INT NOT NULL,
    valor_total DECIMAL(10,2) NOT NULL,
    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loja_id) REFERENCES lojas(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
);

-- Inserir associações de produtos às lojas
INSERT IGNORE INTO produtos_lojas (loja_id, produto_id, quantidade_estoque, preco_loja) VALUES 
(1, 1, 10, 899.99),
(1, 5, 15, 129.90),
(2, 1, 8, 879.99),
(2, 2, 5, 2399.99),
(3, 3, 25, 55.90),
(3, 4, 20, 85.90);

-- Inserir vendas de exemplo
INSERT IGNORE INTO vendas_lojas (loja_id, produto_id, quantidade, valor_total) VALUES 
(1, 1, 2, 1799.98),
(1, 5, 1, 129.90),
(2, 2, 1, 2399.99),
(3, 3, 5, 279.50);

-- Inserir um pedido de exemplo
INSERT IGNORE INTO pedidos (id, cliente_id, status) VALUES (1, 1, 'Pendente');

-- Inserir itens do pedido de exemplo
INSERT IGNORE INTO items (pedido_id, produto_id, quantidade, preco) VALUES 
(1, 1, 1, 899.99),
(1, 3, 2, 59.90);

-- Índices para otimização
CREATE INDEX idx_produtos_categoria ON produtos(categoria_id);
CREATE INDEX idx_items_pedido ON items(pedido_id);
CREATE INDEX idx_items_produto ON items(produto_id);
CREATE INDEX idx_estoque_produto ON estoque(produto_id);
