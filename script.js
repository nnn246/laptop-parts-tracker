let globalData = null;
let currentCurrency = 'JPY';

async function loadData() {
  try {
    const res = await fetch('data.json?t=' + new Date().getTime());
    globalData = await res.json();
    
    document.getElementById('update-time').textContent = `Last updated: ${globalData.last_updated}`;
    renderAll();
  } catch (err) {
    console.error('Data load error:', err);
    document.getElementById('update-time').textContent = 'Failed to load data';
  }
}

function setCurrency(curr) {
  currentCurrency = curr;
  document.querySelectorAll('.curr-btn').forEach(btn => {
    btn.classList.remove('active');
    if (btn.textContent.includes(curr)) {
      btn.classList.add('active');
    }
  });
  renderAll();
}

function formatPrice(priceJPY, priceMYR) {
  if (!globalData || !globalData.exchange_rates) return '-';
  const rates = globalData.exchange_rates;
  
  if (currentCurrency === 'JPY') {
    if (priceJPY) return `¥${priceJPY.toLocaleString()}`;
    if (priceMYR) return `¥${Math.round(priceMYR * rates.MYR_JPY).toLocaleString()}`;
  } else if (currentCurrency === 'MYR') {
    if (priceMYR) return `RM ${priceMYR.toFixed(2)}`;
    if (priceJPY) return `RM ${(priceJPY / rates.MYR_JPY).toFixed(2)}`;
  } else if (currentCurrency === 'USD') {
    if (priceJPY) return `$${(priceJPY / rates.USD_JPY).toFixed(2)}`;
    if (priceMYR) return `$${((priceMYR * rates.MYR_JPY) / rates.USD_JPY).toFixed(2)}`;
  }
  return '-';
}

function createShopCell(info) {
  if (!info || !info.price) return '<td>-</td>';
  const priceStr = formatPrice(info.price_jpy || (currentCurrency === 'JPY' ? info.price : null), info.price_myr || (currentCurrency === 'MYR' ? info.price : null));
  const shopName = info.shop ? info.shop : 'Store Link';
  
  if (info.url) {
    return `<td><div><strong>${priceStr}</strong></div><div style="font-size:0.8em;"><a href="${info.url}" target="_blank" rel="noopener">${shopName}</a></div></td>`;
  }
  return `<td><div><strong>${priceStr}</strong></div></td>`;
}

function renderTable(items, tbodyId) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  
  if (!items || items.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5">No data available</td></tr>';
    return;
  }
  
  let html = '';
  items.forEach(item => {
    html += `<tr>
      <td>${item.brand || '-'}</td>
      <td>${item.model || '-'}</td>
      <td>${item.capacity || '-'}</td>
      ${createShopCell(item.rakuten)}
      ${createShopCell(item.shopee)}
    </tr>`;
  });
  
  tbody.innerHTML = html;
}

function renderAll() {
  if (!globalData) return;
  
  const ddr4 = (globalData.ram || []).filter(i => i.type === 'DDR4');
  const ddr5 = (globalData.ram || []).filter(i => i.type === 'DDR5');
  const gen3 = (globalData.ssd || []).filter(i => i.spec === 'PCIe 3.0');
  const gen4 = (globalData.ssd || []).filter(i => i.spec === 'PCIe 4.0');
  
  renderTable(ddr4, 'ram-ddr4-table-body');
  renderTable(ddr5, 'ram-ddr5-table-body');
  renderTable(gen3, 'ssd-gen3-table-body');
  renderTable(gen4, 'ssd-gen4-table-body');
}

document.addEventListener('DOMContentLoaded', loadData);