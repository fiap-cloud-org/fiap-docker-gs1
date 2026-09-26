from flask import Flask, jsonify, request, render_template
import pymysql
import os
from datetime import datetime

app = Flask(__name__)
app.json.ensure_ascii = False  # acentos legíveis nas respostas JSON

# Configuração do banco de dados
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql-db'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'ecommerce_db'),
    'charset': 'utf8mb4',
    'autocommit': True
}

def get_db_connection():
    """Criar conexão com o banco de dados MySQL"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def execute_query(query, params=None, fetch=False):
    """Executar query no banco de dados"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, params)
            if fetch:
                if 'SELECT' in query.upper():
                    return cursor.fetchall()
                else:
                    return cursor.fetchone()
            return cursor.lastrowid
    except Exception as e:
        print(f"Erro ao executar query: {e}")
        return None
    finally:
        connection.close()

CAMPOS_LOJA = ('nome', 'descricao', 'endereco', 'contato')
LIMITES_LOJA = {'nome': 100, 'descricao': 1000, 'endereco': 255, 'contato': 50}

def dados_requisicao():
    """Aceita tanto JSON quanto formulário (o front e o curl -d usam formulário)"""
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form

def validar_loja(dados):
    """Valida os campos da loja e devolve (loja, erro)"""
    loja = {c: str(dados.get(c) or '').strip() for c in CAMPOS_LOJA}
    if not loja['nome']:
        return None, "O campo 'nome' é obrigatório"
    for campo, limite in LIMITES_LOJA.items():
        if len(loja[campo]) > limite:
            return None, f"O campo '{campo}' aceita no máximo {limite} caracteres"
    return loja, None

def execute_write(query, params=None):
    """Executa UPDATE/DELETE e devolve as linhas afetadas (None em caso de erro)"""
    connection = get_db_connection()
    if not connection:
        return None
    try:
        with connection.cursor() as cursor:
            return cursor.execute(query, params)
    except Exception as e:
        print(f"Erro ao executar query: {e}")
        return None
    finally:
        connection.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/lojas', methods=['GET', 'POST'])
def lojas_route():
    if request.method == 'POST':
        loja, erro = validar_loja(dados_requisicao())
        if erro:
            return jsonify({"error": erro}), 400
        nome, descricao, endereco, contato = (loja[c] for c in CAMPOS_LOJA)

        # Inserir loja no banco de dados
        query = """
        INSERT INTO lojas (nome, descricao, endereco, contato) 
        VALUES (%s, %s, %s, %s)
        """
        loja_id = execute_query(query, (nome, descricao, endereco, contato))
        
        if loja_id:
            # Buscar todas as lojas para retornar
            lojas = execute_query("SELECT * FROM lojas ORDER BY id", fetch=True)
            return jsonify({
                "message": "Loja cadastrada com sucesso",
                "loja_id": loja_id,
                "lojas": lojas or []
            }), 201
        else:
            return jsonify({"error": "Erro ao cadastrar loja"}), 500
    
    # GET - Buscar todas as lojas
    lojas = execute_query("SELECT * FROM lojas ORDER BY id", fetch=True)
    return jsonify({"lojas": lojas or []})

@app.route('/lojas/<int:loja_id>', methods=['GET', 'PUT', 'DELETE'])
def loja_route(loja_id):
    if request.method == 'GET':
        loja = execute_query("SELECT * FROM lojas WHERE id = %s", (loja_id,), fetch=True)
        if loja is None:
            return jsonify({"error": "Erro ao consultar loja"}), 500
        if not loja:
            return jsonify({"error": "Loja não encontrada"}), 404
        return jsonify({"loja": loja[0]})

    if request.method == 'PUT':
        loja, erro = validar_loja(dados_requisicao())
        if erro:
            return jsonify({"error": erro}), 400
        existe = execute_query("SELECT id FROM lojas WHERE id = %s", (loja_id,), fetch=True)
        if not existe:
            return jsonify({"error": "Loja não encontrada"}), 404
        afetadas = execute_write(
            "UPDATE lojas SET nome = %s, descricao = %s, endereco = %s, contato = %s WHERE id = %s",
            (*(loja[c] for c in CAMPOS_LOJA), loja_id),
        )
        if afetadas is None:
            return jsonify({"error": "Erro ao atualizar loja"}), 500
        atualizada = execute_query("SELECT * FROM lojas WHERE id = %s", (loja_id,), fetch=True)
        return jsonify({"message": "Loja atualizada com sucesso", "loja": atualizada[0]})

    # DELETE: produtos_lojas e vendas_lojas caem junto (ON DELETE CASCADE)
    afetadas = execute_write("DELETE FROM lojas WHERE id = %s", (loja_id,))
    if afetadas is None:
        return jsonify({"error": "Erro ao remover loja"}), 500
    if afetadas == 0:
        return jsonify({"error": "Loja não encontrada"}), 404
    return jsonify({"message": "Loja removida com sucesso", "loja_id": loja_id})

@app.route('/produtos_lojas', methods=['POST'])
def produtos_lojas_route():
    dados = dados_requisicao()
    loja_id = dados.get('loja_id')
    produto_id = dados.get('produto_id')
    if not loja_id or not produto_id:
        return jsonify({"error": "Informe loja_id e produto_id"}), 400
    
    # Inserir associação produto-loja no banco de dados (com valores padrão)
    query = """
    INSERT INTO produtos_lojas (loja_id, produto_id, quantidade_estoque, preco_loja) 
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
    quantidade_estoque = VALUES(quantidade_estoque),
    preco_loja = VALUES(preco_loja)
    """
    
    # Quantidade e preço são opcionais (padrão: 0 unidades e preço NULL)
    quantidade_estoque = dados.get('quantidade_estoque') or 0
    preco_loja = dados.get('preco_loja') or None
    
    result = execute_query(query, (loja_id, produto_id, quantidade_estoque, preco_loja))
    
    if result is not None:
        # Buscar todas as associações para retornar
        produtos_lojas = execute_query("""
            SELECT pl.*, l.nome as loja_nome, p.nome as produto_nome 
            FROM produtos_lojas pl
            JOIN lojas l ON pl.loja_id = l.id
            JOIN produtos p ON pl.produto_id = p.id
            ORDER BY pl.id
        """, fetch=True)
        
        return jsonify({
            "message": f"Produto {produto_id} associado à loja {loja_id} com sucesso", 
            "produtos_lojas": produtos_lojas or []
        })
    else:
        return jsonify({"error": "Erro ao associar produto à loja"}), 500

@app.route('/dashboard/<int:loja_id>')
def dashboard(loja_id):
    # Buscar vendas da loja
    vendas_query = """
    SELECT vl.*, p.nome as produto_nome, l.nome as loja_nome
    FROM vendas_lojas vl
    JOIN produtos p ON vl.produto_id = p.id
    JOIN lojas l ON vl.loja_id = l.id
    WHERE vl.loja_id = %s
    ORDER BY vl.data_venda DESC
    """
    vendas = execute_query(vendas_query, (loja_id,), fetch=True)
    
    # Buscar estoque da loja
    estoque_query = """
    SELECT pl.*, p.nome as produto_nome, p.descricao as produto_descricao, 
           c.nome as categoria_nome
    FROM produtos_lojas pl
    JOIN produtos p ON pl.produto_id = p.id
    LEFT JOIN categorias c ON p.categoria_id = c.id
    WHERE pl.loja_id = %s
    ORDER BY p.nome
    """
    estoque = execute_query(estoque_query, (loja_id,), fetch=True)
    
    # Buscar informações da loja
    loja_query = "SELECT * FROM lojas WHERE id = %s"
    loja = execute_query(loja_query, (loja_id,), fetch=True)
    loja_info = loja[0] if loja else None
    if loja_info is None:
        return jsonify({"error": "Loja não encontrada"}), 404

    return jsonify({
        "loja": loja_info,
        "vendas": vendas or [], 
        "estoque": estoque or []
    })


@app.route('/status')
def status():
    # Testar conexão com o banco
    connection = get_db_connection()
    if connection:
        connection.close()
        db_status = "connected"
    else:
        db_status = "disconnected"
    
    # 503 quando o banco cai, para o healthcheck do container acusar o problema
    return jsonify({
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }), 200 if db_status == "connected" else 503

@app.route('/vendas', methods=['POST'])
def registrar_venda():
    """Registrar uma nova venda"""
    dados = dados_requisicao()
    loja_id = dados.get('loja_id')
    produto_id = dados.get('produto_id')
    if not loja_id or not produto_id:
        return jsonify({"error": "Informe loja_id e produto_id"}), 400
    quantidade = request.form.get('quantidade', 1)
    valor_total = request.form.get('valor_total')
    
    # Inserir venda no banco
    query = """
    INSERT INTO vendas_lojas (loja_id, produto_id, quantidade, valor_total) 
    VALUES (%s, %s, %s, %s)
    """
    
    result = execute_query(query, (loja_id, produto_id, quantidade, valor_total))
    
    if result:
        return jsonify({
            "message": "Venda registrada com sucesso",
            "venda_id": result
        })
    else:
        return jsonify({"error": "Erro ao registrar venda"}), 500

@app.route('/produtos', methods=['GET'])
def listar_produtos():
    """Listar todos os produtos disponíveis"""
    query = """
    SELECT p.*, c.nome as categoria_nome
    FROM produtos p
    LEFT JOIN categorias c ON p.categoria_id = c.id
    ORDER BY p.nome
    """
    produtos = execute_query(query, fetch=True)
    return jsonify({"produtos": produtos or []})

@app.route('/historico', methods=['GET'])
def historico():
    """Listar histórico de vendas de todas as lojas"""
    loja_id = request.args.get('loja_id')
    
    if loja_id:
        # Histórico de uma loja específica
        query = """
        SELECT vl.*, p.nome as produto_nome, l.nome as loja_nome,
               DATE_FORMAT(vl.data_venda, '%%d/%%m/%%Y %%H:%%i') as data_formatada
        FROM vendas_lojas vl
        JOIN produtos p ON vl.produto_id = p.id
        JOIN lojas l ON vl.loja_id = l.id
        WHERE vl.loja_id = %s
        ORDER BY vl.data_venda DESC
        """
        vendas = execute_query(query, (loja_id,), fetch=True)
    else:
        # Histórico de todas as lojas
        query = """
        SELECT vl.*, p.nome as produto_nome, l.nome as loja_nome,
               DATE_FORMAT(vl.data_venda, '%d/%m/%Y %H:%i') as data_formatada
        FROM vendas_lojas vl
        JOIN produtos p ON vl.produto_id = p.id
        JOIN lojas l ON vl.loja_id = l.id
        ORDER BY vl.data_venda DESC
        LIMIT 100
        """
        vendas = execute_query(query, fetch=True)
    
    return jsonify({
        "historico": vendas or [],
        "total_vendas": len(vendas) if vendas else 0
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8484, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')
