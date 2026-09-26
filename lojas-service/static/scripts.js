// Módulo de Lojas - JavaScript Moderno
document.addEventListener('DOMContentLoaded', function() {
    loadLojas();
    atualizarHistorico();
});

// Função para mostrar loading
function showLoading(element) {
    element.innerHTML = '<div class="loading"></div> Carregando...';
}

// Função para mostrar mensagem com estilo
function showMessage(elementId, message, type = 'success') {
    const element = document.getElementById(elementId);
    element.innerHTML = message;
    element.className = `show ${type}`;
    element.style.opacity = '1';
    
    setTimeout(() => {
        element.style.opacity = '0';
        setTimeout(() => {
            element.className = '';
        }, 300);
    }, 3000);
}

// Cadastro de Lojas
document.getElementById('cadastro-loja-form').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const submitBtn = this.querySelector('button');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '⏳ Cadastrando...';
    submitBtn.disabled = true;
    
    const nome = document.getElementById('nome').value;
    const descricao = document.getElementById('descricao').value;
    const endereco = document.getElementById('endereco').value;
    const contato = document.getElementById('contato').value;

    fetch('/lojas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `nome=${encodeURIComponent(nome)}&descricao=${encodeURIComponent(descricao)}&endereco=${encodeURIComponent(endereco)}&contato=${encodeURIComponent(contato)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            showMessage('lojas-list', `✅ ${data.message}`, 'success');
            loadLojas();
            this.reset(); // Limpar formulário
        } else {
            showMessage('lojas-list', `❌ ${data.error || 'Erro ao cadastrar loja'}`, 'error');
        }
    })
    .catch(error => {
        showMessage('lojas-list', `❌ Erro de conexão: ${error.message}`, 'error');
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
});

// Associação de Produtos
document.getElementById('associar-produto-form').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const submitBtn = this.querySelector('button');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '⏳ Associando...';
    submitBtn.disabled = true;
    
    const lojaId = document.getElementById('loja-id').value;
    const produtoId = document.getElementById('produto-id').value;
    const quantidadeEstoque = document.getElementById('quantidade-estoque').value || 0;
    const precoLoja = document.getElementById('preco-loja').value || 0;

    fetch('/produtos_lojas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `loja_id=${lojaId}&produto_id=${produtoId}&quantidade_estoque=${quantidadeEstoque}&preco_loja=${precoLoja}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            showMessage('associacao-mensagem', `✅ ${data.message}`, 'success');
            this.reset();
        } else {
            showMessage('associacao-mensagem', `❌ ${data.error || 'Erro ao associar produto'}`, 'error');
        }
    })
    .catch(error => {
        showMessage('associacao-mensagem', `❌ Erro de conexão: ${error.message}`, 'error');
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
});

// Dashboard
document.getElementById('dashboard-form').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const submitBtn = this.querySelector('button');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '⏳ Carregando...';
    submitBtn.disabled = true;
    
    const lojaId = document.getElementById('dashboard-loja-id').value;
    const dashboardDiv = document.getElementById('dashboard');
    
    showLoading(dashboardDiv);

    fetch(`/dashboard/${lojaId}`)
    .then(response => response.json())
    .then(data => {
        if (data.loja) {
            dashboardDiv.innerHTML = `
                <div class="dashboard-section">
                    <h3>🏪 Informações da Loja</h3>
                    <p><strong>Nome:</strong> ${data.loja.nome}</p>
                    <p><strong>Descrição:</strong> ${data.loja.descricao}</p>
                    <p><strong>Endereço:</strong> ${data.loja.endereco}</p>
                    <p><strong>Contato:</strong> ${data.loja.contato}</p>
                </div>
                
                <div class="dashboard-section">
                    <h3>📦 Estoque (${data.estoque.length} produtos)</h3>
                    ${data.estoque.length > 0 ? 
                        data.estoque.map(item => `
                            <div class="historico-item">
                                <strong>${item.produto_nome}</strong><br>
                                Categoria: ${item.categoria_nome || 'N/A'}<br>
                                Quantidade: ${item.quantidade_estoque} unidades<br>
                                Preço: R$ ${parseFloat(item.preco_loja || 0).toFixed(2)}
                            </div>
                        `).join('') 
                        : '<p>Nenhum produto em estoque</p>'
                    }
                </div>
                
                <div class="dashboard-section">
                    <h3>💰 Vendas Recentes (${data.vendas.length})</h3>
                    ${data.vendas.length > 0 ? 
                        data.vendas.map(venda => `
                            <div class="historico-item">
                                <strong>${venda.produto_nome}</strong><br>
                                Quantidade: ${venda.quantidade}<br>
                                Valor Total: R$ ${parseFloat(venda.valor_total).toFixed(2)}<br>
                                Data: ${new Date(venda.data_venda).toLocaleDateString('pt-BR')}
                            </div>
                        `).join('') 
                        : '<p>Nenhuma venda registrada</p>'
                    }
                </div>
            `;
        } else {
            dashboardDiv.innerHTML = '<p class="error">❌ Loja não encontrada</p>';
        }
    })
    .catch(error => {
        dashboardDiv.innerHTML = `<p class="error">❌ Erro ao carregar dashboard: ${error.message}</p>`;
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
});

// Carregar lista de lojas
function loadLojas() {
    const lojasDiv = document.getElementById('lojas-list');
    showLoading(lojasDiv);
    
    fetch('/lojas')
    .then(response => response.json())
    .then(data => {
        if (data.lojas && data.lojas.length > 0) {
            lojasDiv.innerHTML = `
                <h3>🏪 Lojas Cadastradas (${data.lojas.length})</h3>
                ${data.lojas.map(loja => `
                    <p class="card-hover">
                        <strong>ID: ${loja.id}</strong> - ${loja.nome}<br>
                        <small>📝 ${loja.descricao}</small><br>
                        <small>📍 ${loja.endereco}</small><br>
                        <small>📞 ${loja.contato}</small>
                    </p>
                `).join('')}
            `;
        } else {
            lojasDiv.innerHTML = '<p>Nenhuma loja cadastrada ainda</p>';
        }
    })
    .catch(error => {
        lojasDiv.innerHTML = `<p class="error">❌ Erro ao carregar lojas: ${error.message}</p>`;
    });
}

// Atualizar histórico
function atualizarHistorico() {
    const historicoDiv = document.getElementById('historico');
    showLoading(historicoDiv);
    
    fetch('/historico')
    .then(response => response.json())
    .then(data => {
        if (data.historico && data.historico.length > 0) {
            historicoDiv.innerHTML = `
                <h3>📊 Histórico de Vendas (${data.total_vendas} vendas)</h3>
                ${data.historico.map(venda => `
                    <div class="historico-item">
                        <strong>🏪 ${venda.loja_nome}</strong> - 📦 ${venda.produto_nome}<br>
                        Quantidade: ${venda.quantidade} | 
                        Valor: R$ ${parseFloat(venda.valor_total).toFixed(2)}<br>
                        <small>🕒 ${venda.data_formatada}</small>
                    </div>
                `).join('')}
            `;
        } else {
            historicoDiv.innerHTML = '<p>📋 Nenhuma venda registrada ainda</p>';
        }
    })
    .catch(error => {
        historicoDiv.innerHTML = `<p class="error">❌ Erro ao carregar histórico: ${error.message}</p>`;
    });
}

function loadLojas() {
    fetch('/lojas')
    .then(response => response.json())
    .then(data => {
        const lojasList = document.getElementById('lojas-list');
        lojasList.innerHTML = '<h3>Lojas Cadastradas</h3><ul>' + data.lojas.map(loja => `<li>${loja.nome} - ${loja.descricao}</li>`).join('') + '</ul>';
    });
}

loadLojas();