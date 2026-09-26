// Painel do lojas-service: CRUD de lojas, estoque, vendas e histórico.
const $ = (id) => document.getElementById(id);
const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

const estado = { lojas: [], produtos: [], selecionada: null };

function esc(valor) {
  return String(valor ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[c]);
}

function toast(msg, erro = false) {
  const el = $('toast');
  el.textContent = msg;
  el.classList.toggle('is-error', erro);
  el.classList.add('is-visible');
  clearTimeout(toast.t);
  toast.t = setTimeout(() => el.classList.remove('is-visible'), 2600);
}

async function api(url, opcoes = {}) {
  const resp = await fetch(url, opcoes);
  const dados = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(dados.error || `Erro ${resp.status}`);
  return dados;
}

function corpoForm(obj) {
  return { method: 'POST', body: new URLSearchParams(obj) };
}

// Status do banco
async function verificarStatus() {
  const el = $('status');
  try {
    const dados = await api('/status');
    el.dataset.state = 'ok';
    el.querySelector('.status__text').textContent = 'MySQL conectado';
    return dados;
  } catch {
    el.dataset.state = 'erro';
    el.querySelector('.status__text').textContent = 'banco indisponível';
  }
}

// Lojas
function renderLojas() {
  const termo = $('busca').value.trim().toLowerCase();
  const lista = estado.lojas.filter((l) =>
    !termo || `${l.nome} ${l.endereco} ${l.descricao}`.toLowerCase().includes(termo));
  $('kpi-lojas').textContent = estado.lojas.length;

  if (!lista.length) {
    $('lojas-body').innerHTML = `<tr><td colspan="5" class="empty">${termo ? 'Nenhuma loja encontrada.' : 'Nenhuma loja cadastrada ainda.'}</td></tr>`;
    return;
  }
  $('lojas-body').innerHTML = lista.map((l) => `
    <tr class="is-clickable ${estado.selecionada === l.id ? 'is-selected' : ''}" data-id="${l.id}">
      <td class="id">#${l.id}</td>
      <td><div class="loja-nome">${esc(l.nome)}</div><div class="loja-desc">${esc(l.descricao) || '<span class="pill">sem descrição</span>'}</div></td>
      <td>${esc(l.endereco) || '<span class="loja-desc">não informado</span>'}</td>
      <td class="id">${esc(l.contato)}</td>
      <td><div class="actions">
        <button class="icon-btn" data-acao="editar" data-id="${l.id}">Editar</button>
        <button class="icon-btn icon-btn--danger" data-acao="remover" data-id="${l.id}">Remover</button>
      </div></td>
    </tr>`).join('');
}

async function carregarLojas() {
  try {
    estado.lojas = (await api('/lojas')).lojas;
    renderLojas();
  } catch (e) {
    $('lojas-body').innerHTML = `<tr><td colspan="5" class="empty">Erro ao carregar lojas: ${esc(e.message)}</td></tr>`;
  }
}

function modoEdicao(loja) {
  $('loja-id').value = loja ? loja.id : '';
  ['nome', 'descricao', 'endereco', 'contato'].forEach((c) => { $(c).value = loja ? (loja[c] || '') : ''; });
  $('form-title').textContent = loja ? `Editar loja #${loja.id}` : 'Nova loja';
  $('form-sub').textContent = loja ? 'Altere os campos e salve.' : 'Preencha os dados para cadastrar.';
  $('form-submit').textContent = loja ? 'Salvar alterações' : 'Cadastrar loja';
  $('form-cancel').hidden = !loja;
  if (loja) $('nome').focus();
}

$('loja-form').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const id = $('loja-id').value;
  const campos = Object.fromEntries(['nome', 'descricao', 'endereco', 'contato'].map((c) => [c, $(c).value]));
  const botao = $('form-submit');
  botao.disabled = true;
  try {
    if (id) {
      await api(`/lojas/${id}`, { method: 'PUT', body: new URLSearchParams(campos) });
      toast('Loja atualizada.');
    } else {
      const dados = await api('/lojas', corpoForm(campos));
      toast(`Loja #${dados.loja_id} cadastrada.`);
    }
    modoEdicao(null);
    await carregarLojas();
    if (estado.selecionada) abrirDetalhe(estado.selecionada);
  } catch (e) {
    toast(e.message, true);
  } finally {
    botao.disabled = false;
  }
});

$('form-cancel').addEventListener('click', () => modoEdicao(null));
$('busca').addEventListener('input', renderLojas);

$('lojas-body').addEventListener('click', async (ev) => {
  const botao = ev.target.closest('button[data-acao]');
  const linha = ev.target.closest('tr[data-id]');
  if (!linha) return;
  const id = Number((botao || linha).dataset.id);
  const loja = estado.lojas.find((l) => l.id === id);

  if (botao?.dataset.acao === 'editar') return modoEdicao(loja);
  if (botao?.dataset.acao === 'remover') {
    if (!confirm(`Remover a loja "${loja.nome}"? Estoque e vendas dela também serão apagados.`)) return;
    try {
      await api(`/lojas/${id}`, { method: 'DELETE' });
      toast('Loja removida.');
      if (estado.selecionada === id) fecharDetalhe();
      await Promise.all([carregarLojas(), carregarHistorico()]);
    } catch (e) { toast(e.message, true); }
    return;
  }
  abrirDetalhe(id);
});

// Detalhe da loja (dashboard)
function opcoesProdutos() {
  return estado.produtos.map((p) =>
    `<option value="${p.id}" data-preco="${p.preco}">${esc(p.nome)} · ${brl.format(p.preco)}</option>`).join('');
}

async function abrirDetalhe(id) {
  try {
    const dados = await api(`/dashboard/${id}`);
    estado.selecionada = id;
    renderLojas();
    $('detalhe').hidden = false;
    $('det-id').textContent = `Loja #${dados.loja.id}`;
    $('det-nome').textContent = dados.loja.nome;
    $('det-desc').textContent = [dados.loja.descricao, dados.loja.endereco].filter(Boolean).join(' · ');

    $('det-estoque').innerHTML = dados.estoque.length ? dados.estoque.map((i) => `
      <tr><td>${esc(i.produto_nome)}</td><td><span class="pill">${esc(i.categoria_nome || 'sem categoria')}</span></td>
      <td class="num">${i.quantidade_estoque}</td><td class="num">${i.preco_loja ? brl.format(i.preco_loja) : '-'}</td></tr>`).join('')
      : '<tr><td colspan="4" class="empty">Nenhum produto associado.</td></tr>';

    $('det-vendas').innerHTML = dados.vendas.length ? dados.vendas.map((v) => `
      <tr><td class="id">${new Date(v.data_venda).toLocaleDateString('pt-BR')}</td><td>${esc(v.produto_nome)}</td>
      <td class="num">${v.quantidade}</td><td class="num">${brl.format(v.valor_total)}</td></tr>`).join('')
      : '<tr><td colspan="4" class="empty">Nenhuma venda registrada.</td></tr>';

    $('detalhe').scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (e) {
    toast(e.message, true);
  }
}

function fecharDetalhe() {
  estado.selecionada = null;
  $('detalhe').hidden = true;
  renderLojas();
}
$('det-fechar').addEventListener('click', fecharDetalhe);

$('assoc-form').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  try {
    await api('/produtos_lojas', corpoForm({
      loja_id: estado.selecionada,
      produto_id: $('assoc-produto').value,
      quantidade_estoque: $('assoc-qtd').value || 0,
      preco_loja: $('assoc-preco').value,
    }));
    toast('Produto associado à loja.');
    ev.target.reset();
    abrirDetalhe(estado.selecionada);
  } catch (e) { toast(e.message, true); }
});

function sugerirTotal() {
  const opt = $('venda-produto').selectedOptions[0];
  if (opt) $('venda-total').value = (Number(opt.dataset.preco) * Number($('venda-qtd').value || 1)).toFixed(2);
}
$('venda-produto').addEventListener('change', sugerirTotal);
$('venda-qtd').addEventListener('input', sugerirTotal);

$('venda-form').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  try {
    await api('/vendas', corpoForm({
      loja_id: estado.selecionada,
      produto_id: $('venda-produto').value,
      quantidade: $('venda-qtd').value,
      valor_total: $('venda-total').value,
    }));
    toast('Venda registrada.');
    abrirDetalhe(estado.selecionada);
    carregarHistorico();
  } catch (e) { toast(e.message, true); }
});

// Produtos e histórico
async function carregarProdutos() {
  try {
    estado.produtos = (await api('/produtos')).produtos;
    $('kpi-produtos').textContent = estado.produtos.length;
    $('assoc-produto').innerHTML = opcoesProdutos();
    $('venda-produto').innerHTML = opcoesProdutos();
    sugerirTotal();
  } catch (e) { toast(e.message, true); }
}

async function carregarHistorico() {
  try {
    const dados = await api('/historico');
    const total = dados.historico.reduce((s, v) => s + Number(v.valor_total), 0);
    $('kpi-vendas').textContent = dados.total_vendas;
    $('kpi-faturamento').textContent = brl.format(total);
    $('historico-body').innerHTML = dados.historico.length ? dados.historico.map((v) => `
      <tr><td class="id">${esc(v.data_formatada)}</td><td>${esc(v.loja_nome)}</td><td>${esc(v.produto_nome)}</td>
      <td class="num">${v.quantidade}</td><td class="num">${brl.format(v.valor_total)}</td></tr>`).join('')
      : '<tr><td colspan="5" class="empty">Nenhuma venda registrada.</td></tr>';
  } catch (e) {
    $('historico-body').innerHTML = `<tr><td colspan="5" class="empty">Erro ao carregar histórico: ${esc(e.message)}</td></tr>`;
  }
}

verificarStatus();
carregarLojas();
carregarProdutos();
carregarHistorico();
setInterval(verificarStatus, 15000);
