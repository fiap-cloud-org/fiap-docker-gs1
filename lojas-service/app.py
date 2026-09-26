from flask import Flask, jsonify, request, render_template
import pymysql
import os
from datetime import datetime

app = Flask(__name__)

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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/lojas', methods=['GET', 'POST'])
def lojas_route():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        endereco = request.form.get('endereco')
        contato = request.form.get('contato')
        
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
            })
        else:
            return jsonify({"error": "Erro ao cadastrar loja"}), 500
    
    # GET - Buscar todas as lojas
    lojas = execute_query("SELECT * FROM lojas ORDER BY id", fetch=True)
    return jsonify({"lojas": lojas or []})

@app.route('/produtos_lojas', methods=['POST'])
def produtos_lojas_route():
    loja_id = request.form.get('loja_id')
    produto_id = request.form.get('produto_id')
    
    # Inserir associação produto-loja no banco de dados (com valores padrão)
    query = """
    INSERT INTO produtos_lojas (loja_id, produto_id, quantidade_estoque, preco_loja) 
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
    quantidade_estoque = VALUES(quantidade_estoque),
    preco_loja = VALUES(preco_loja)
    """
    
    # Usar valores padrão quando os campos não são fornecidos
    quantidade_estoque = 0  # Valor padrão
    preco_loja = None  # Valor padrão (NULL no banco)
    
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
    
    return jsonify({
        "status": "ok",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/vendas', methods=['POST'])
def registrar_venda():
    """Registrar uma nova venda"""
    loja_id = request.form.get('loja_id')
    produto_id = request.form.get('produto_id')
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
               DATE_FORMAT(vl.data_venda, '%d/%m/%Y %H:%i') as data_formatada
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
