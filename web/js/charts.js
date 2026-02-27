/**
 * グラフ描画モジュール
 * Plotly.jsを使用した各種グラフの描画
 */

// ========== 総資産推移グラフ ==========
function renderAssetsChart() {
    if (!simulationData) return;

    const yearlyData = simulationData.yearly_data;
    const ages = yearlyData.map(d => d.age);
    const totalAssets = yearlyData.map(d => d.assets_end);

    const trace = {
        x: ages,
        y: totalAssets,
        type: 'scatter',
        mode: 'lines+markers',
        name: '総資産',
        line: {
            color: '#1e3a8a',
            width: 3
        },
        marker: {
            size: 6,
            color: '#3b82f6'
        },
        hovertemplate: '%{x}歳: %{y:,.0f}円<extra></extra>'
    };

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: {
            title: '年齢',
            dtick: 5,
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        yaxis: {
            title: '資産額 (円)',
            tickformat: ',.0f',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        hovermode: 'closest',
        margin: { t: 30, r: 30, b: 50, l: 80 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d']
    };

    Plotly.newPlot('assetsChart', [trace], layout, config);
}

// ========== 資産内訳推移グラフ（積み上げエリア） ==========
function renderAssetsBreakdownChart() {
    if (!simulationData) return;

    const yearlyData = simulationData.yearly_data;
    const ages = yearlyData.map(d => d.age);

    const traces = [
        {
            x: ages,
            y: yearlyData.map(d => d.cash),
            name: '現金・預金',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#10b981',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - 現金: %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: yearlyData.map(d => d.education_fund),
            name: '教育資金',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#f59e0b',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - 教育資金: %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: yearlyData.map(d => d.taxable_account || 0),
            name: '特定口座',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#ec4899',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - 特定口座: %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: yearlyData.map(d => d.company_stock),
            name: '自社株',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#8b5cf6',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - 自社株: %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: yearlyData.map(d => d.nisa_fang || 0),
            name: 'NISA(FANG+)',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#3b82f6',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - NISA(FANG+): %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: yearlyData.map(d => d.nisa_orcan || 0),
            name: 'NISA(オルカン)',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#1e3a8a',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - NISA(オルカン): %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: yearlyData.map(d => d.nisa_sp500 || 0),
            name: 'NISA(SP500)',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#0ea5e9',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - NISA(SP500): %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: yearlyData.map(d => (d.spouse_nisa_orcan || 0) + (d.spouse_nisa_sp500 || 0)),
            name: '配偶者NISA',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#f472b6',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - 配偶者NISA: %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: yearlyData.map(d => (d.child1_nisa || 0) + (d.child2_nisa || 0)),
            name: '子供NISA',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#6ee7b7',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - 子供NISA: %{y:,.0f}円<extra></extra>'
        }
    ];

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: {
            title: '年齢',
            dtick: 5,
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        yaxis: {
            title: '資産額 (円)',
            tickformat: ',.0f',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        hovermode: 'x unified',
        legend: {
            orientation: 'h',
            y: -0.2
        },
        margin: { t: 30, r: 30, b: 80, l: 80 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };

    Plotly.newPlot('assetsBreakdownChart', traces, layout, config);
}

// ========== 年間キャッシュフローグラフ ==========
function renderCashflowChart() {
    if (!simulationData) return;

    const yearlyData = simulationData.yearly_data;
    const ages = yearlyData.map(d => d.age);
    const cashflows = yearlyData.map(d => d.cashflow_annual);

    const colors = cashflows.map(cf => cf >= 0 ? '#10b981' : '#ef4444');

    const trace = {
        x: ages,
        y: cashflows,
        type: 'bar',
        name: '年間収支',
        marker: {
            color: colors
        },
        hovertemplate: '%{x}歳: %{y:,.0f}円<extra></extra>'
    };

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: {
            title: '年齢',
            dtick: 5,
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        yaxis: {
            title: 'キャッシュフロー (円)',
            tickformat: ',.0f',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb',
            zeroline: true,
            zerolinecolor: isDarkMode ? '#6b7280' : '#9ca3af',
            zerolinewidth: 2
        },
        hovermode: 'closest',
        margin: { t: 30, r: 30, b: 50, l: 80 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };

    Plotly.newPlot('cashflowChart', [trace], layout, config);
}

// ========== 累積キャッシュフローグラフ ==========
function renderCumulativeCashflowChart() {
    if (!simulationData) return;

    const yearlyData = simulationData.yearly_data;
    const ages = yearlyData.map(d => d.age);

    // 累積キャッシュフロー計算
    let cumulative = 0;
    const cumulativeCashflows = yearlyData.map(d => {
        cumulative += d.cashflow_annual;
        return cumulative;
    });

    const trace = {
        x: ages,
        y: cumulativeCashflows,
        type: 'scatter',
        mode: 'lines+markers',
        name: '累積キャッシュフロー',
        line: {
            color: '#10b981',
            width: 3
        },
        marker: {
            size: 6,
            color: '#059669'
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(16, 185, 129, 0.2)',
        hovertemplate: '%{x}歳: %{y:,.0f}円<extra></extra>'
    };

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: {
            title: '年齢',
            dtick: 5,
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        yaxis: {
            title: '累積額 (円)',
            tickformat: ',.0f',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        hovermode: 'closest',
        margin: { t: 30, r: 30, b: 50, l: 80 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };

    Plotly.newPlot('cumulativeCashflowChart', [trace], layout, config);
}

// ========== タイムラインチャート ==========
function renderTimelineChart() {
    const events = [
        { age: 25, year: 2025, event: '入社', category: 'career' },
        { age: 28, year: 2028, event: '結婚', category: 'family' },
        { age: 30, year: 2030, event: '第一子誕生', category: 'family' },
        { age: 32, year: 2032, event: '第二子誕生', category: 'family' },
        { age: 37, year: 2037, event: 'つみたてNISA満額', category: 'investment' },
        { age: 45, year: 2045, event: 'NISA満額達成', category: 'investment' },
        { age: 48, year: 2048, event: '第一子大学入学', category: 'education' },
        { age: 50, year: 2050, event: '持ち家購入', category: 'housing' },
        { age: 52, year: 2052, event: '第一子大学卒業', category: 'education' },
        { age: 54, year: 2054, event: '第二子大学卒業', category: 'education' },
        { age: 56, year: 2056, event: '資産形成最終期', category: 'investment' },
        { age: 60, year: 2060, event: '役職定年', category: 'career' },
        { age: 65, year: 2065, event: '定年退職', category: 'career' }
    ];

    const categoryColors = {
        career: '#1e3a8a',
        family: '#10b981',
        investment: '#3b82f6',
        education: '#f59e0b',
        housing: '#8b5cf6'
    };

    const trace = {
        x: events.map(e => e.age),
        y: events.map((e, i) => (i % 2 === 0 ? 1 : 2)),
        mode: 'markers+text',
        type: 'scatter',
        marker: {
            size: 20,
            color: events.map(e => categoryColors[e.category]),
            line: {
                color: 'white',
                width: 2
            }
        },
        text: events.map(e => e.event),
        textposition: 'top center',
        textfont: {
            size: 11,
            color: isDarkMode ? '#f9fafb' : '#111827'
        },
        hovertemplate: '%{x}歳 (%{text})<extra></extra>'
    };

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: {
            title: '年齢',
            range: [23, 67],
            dtick: 5,
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        yaxis: {
            visible: false,
            range: [0, 3]
        },
        hovermode: 'closest',
        margin: { t: 60, r: 30, b: 50, l: 50 },
        showlegend: false
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot('timelineChart', [trace], layout, config);
}

// ========== 月次収入内訳（円グラフ） ==========
function renderMonthlyCharts(monthlyData) {
    // 12ヶ月の平均を計算
    const avgIncome = calculateMonthlyAverage(monthlyData, 'income');
    const avgExpenses = calculateMonthlyAverage(monthlyData, 'expenses');
    const avgInvestment = calculateMonthlyAverage(monthlyData, 'investment');

    // 収入円グラフ
    renderPieChart('monthlyIncomeChart', avgIncome, '収入内訳');

    // 支出円グラフ
    renderPieChart('monthlyExpensesChart', avgExpenses, '支出内訳');

    // 投資円グラフ
    renderPieChart('monthlyInvestmentChart', avgInvestment, '投資内訳');

    // 月別キャッシュフロー棒グラフ
    renderMonthlyCashflowBarChart(monthlyData);
}

function calculateMonthlyAverage(monthlyData, category) {
    const result = {};
    const sampleMonth = monthlyData[0][category];

    Object.keys(sampleMonth).forEach(key => {
        if (key === 'total') return;

        const sum = monthlyData.reduce((acc, month) => {
            return acc + (month[category][key] || 0);
        }, 0);

        const avg = sum / monthlyData.length;
        if (avg > 0) {
            // キーを日本語化
            const jpKey = translateKey(key);
            result[jpKey] = Math.round(avg);
        }
    });

    return result;
}

function translateKey(key) {
    const translations = {
        'salary_net': '給与手取り',
        'bonus_net': 'ボーナス',
        'spouse_income': '配偶者収入',
        'child_allowance': '児童手当',
        'housing_allowance': '家賃補助',
        'housing_rent': '家賃',
        'housing_mortgage': '住宅ローン',
        'housing_utilities': '光熱費',
        'food': '食費',
        'communication': '通信費',
        'transportation': '交通費',
        'daily_goods': '日用品',
        'daily_goods_children': '子供用品',
        'insurance': '保険',
        'entertainment': '娯楽・交際費',
        'spouse_allowance': '配偶者小遣い',
        'childcare_lessons': '保育園・習い事',
        'education_cram_school': '塾・教育費',
        'pet': 'ペット',
        'clothing_medical': '被服・医療',
        'basic_living': '基本生活費',
        'university_living_support': '大学生活費',
        'nisa_orcan': 'NISA(オルカン)',
        'nisa_fang': 'NISA(FANG+)',
        'nisa_sp500': 'NISA(SP500)',
        'spouse_nisa_orcan': '配偶者NISA(オルカン)',
        'spouse_nisa_sp500': '配偶者NISA(SP500)',
        'child1_nisa': '子供NISA(第一子)',
        'child2_nisa': '子供NISA(第二子)',
        'company_stock': '自社株(三菱重工)',
        'education_fund': '教育資金',
        'marriage_fund': '結婚資金',
        'emergency_fund': '緊急予備費',
        'child_preparation_fund': '子供準備資金',
        'high_dividend_stocks': '高配当株',
        'travel': '旅行',
        'reserve': '予備費',
        'living_supplement': '生活費補填',
        'home_appliances': '家電',
        'university_tuition': '大学学費'
    };

    return translations[key] || key;
}

function renderPieChart(elementId, data, title) {
    const labels = Object.keys(data);
    const values = Object.values(data);

    const trace = {
        labels: labels,
        values: values,
        type: 'pie',
        hole: 0.4,
        textinfo: 'label+percent',
        textposition: 'outside',
        automargin: true,
        hovertemplate: '%{label}: %{value:,.0f}円 (%{percent})<extra></extra>'
    };

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        showlegend: true,
        legend: {
            orientation: 'v',
            x: 1.1,
            y: 0.5
        },
        margin: { t: 30, r: 150, b: 30, l: 30 }
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    // 既存のグラフがあれば完全に再描画（レイアウト崩れ防止）
    Plotly.newPlot(elementId, [trace], layout, config);
}

function renderMonthlyCashflowBarChart(monthlyData) {
    const months = monthlyData.map(m => `${m.month}月`);
    const cashflows = monthlyData.map(m => m.cashflow.monthly);

    const colors = cashflows.map(cf => cf >= 0 ? '#10b981' : '#ef4444');

    const trace = {
        x: months,
        y: cashflows,
        type: 'bar',
        marker: { color: colors },
        hovertemplate: '%{x}: %{y:,.0f}円<extra></extra>'
    };

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: {
            title: '月',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        yaxis: {
            title: '収支 (円)',
            tickformat: ',.0f',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb',
            zeroline: true,
            zerolinecolor: isDarkMode ? '#6b7280' : '#9ca3af',
            zerolinewidth: 2
        },
        margin: { t: 30, r: 30, b: 50, l: 80 }
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot('monthlyCashflowChart', [trace], layout, config);
}

// ========== シナリオ比較グラフ ==========
function renderScenarioComparisonChart(scenarios) {
    const traces = scenarios.map((scenario, index) => {
        const ages = scenario.yearly_data.map(d => d.age);
        const assets = scenario.yearly_data.map(d => d.assets_end);

        const colors = ['#1e3a8a', '#10b981', '#f59e0b', '#8b5cf6'];

        return {
            x: ages,
            y: assets,
            type: 'scatter',
            mode: 'lines+markers',
            name: scenario.scenario_name,
            line: {
                color: colors[index % colors.length],
                width: 3
            },
            marker: {
                size: 6
            },
            hovertemplate: '%{x}歳: %{y:,.0f}円<extra></extra>'
        };
    });

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: {
            title: '年齢',
            dtick: 5,
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        yaxis: {
            title: '総資産 (円)',
            tickformat: ',.0f',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        hovermode: 'x unified',
        legend: {
            orientation: 'h',
            y: -0.2
        },
        margin: { t: 30, r: 30, b: 80, l: 80 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };

    Plotly.newPlot('scenarioComparisonChart', traces, layout, config);
}

// ========== 教育費グラフ ==========
async function renderEducationView() {
    const result = await eel.get_education_summary()();

    if (!result.success) {
        console.error('教育費データ取得エラー:', result.error);
        return;
    }

    const data = result.data;

    // サマリーカード更新
    document.getElementById('child1Total').textContent = formatCurrency(data.child1_total);
    document.getElementById('child2Total').textContent = formatCurrency(data.child2_total);
    document.getElementById('childAllowanceTotal').textContent = formatCurrency(data.child_allowance_total);
    document.getElementById('netEducationCost').textContent = formatCurrency(data.net_education_cost);

    // 子供別累積教育費グラフ
    const child1Ages = data.child1_by_age.map(d => d.child_age);
    const child1Cumulative = data.child1_by_age.map(d => d.cumulative_cost);

    const child2Ages = data.child2_by_age.map(d => d.child_age);
    const child2Cumulative = data.child2_by_age.map(d => d.cumulative_cost);

    const traces = [
        {
            x: child1Ages,
            y: child1Cumulative,
            name: '第一子',
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#3b82f6', width: 3 },
            marker: { size: 6 },
            hovertemplate: '%{x}歳: %{y:,.0f}円<extra></extra>'
        },
        {
            x: child2Ages,
            y: child2Cumulative,
            name: '第二子',
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#f59e0b', width: 3 },
            marker: { size: 6 },
            hovertemplate: '%{x}歳: %{y:,.0f}円<extra></extra>'
        }
    ];

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: {
            title: '子供の年齢',
            dtick: 2,
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        yaxis: {
            title: '累積教育費 (円)',
            tickformat: ',.0f',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        hovermode: 'closest',
        legend: {
            orientation: 'h',
            y: -0.2
        },
        margin: { t: 30, r: 30, b: 80, l: 80 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };

    Plotly.newPlot('educationCostChart', traces, layout, config);
}

// ========== 配当金グラフ ==========
async function renderDividendView() {
    const result = await eel.get_dividend_summary()();

    if (!result.success) {
        console.error('配当金データ取得エラー:', result.error);
        return;
    }

    const data = result.data;

    // サマリーカード更新
    document.getElementById('dividendAssets').textContent = formatCurrency(data.dividend_assets);
    document.getElementById('annualDividend').textContent = formatCurrency(data.annual_dividend);
    document.getElementById('monthlyDividend').textContent = formatCurrency(data.monthly_dividend);
    document.getElementById('dividendYield').textContent = data.dividend_yield.toFixed(2) + '%';

    // 配当金推移グラフ
    const ages = data.dividend_history.map(d => d.age);
    const dividendTotal = data.dividend_history.map(d => d.dividend_total);
    const dividendReceived = data.dividend_history.map(d => d.dividend_received);

    const traces = [
        {
            x: ages,
            y: dividendTotal,
            name: '配当金総額（税引前）',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#3b82f6', width: 2 },
            hovertemplate: '%{x}歳: %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: dividendReceived,
            name: '受取配当金（再投資なし）',
            type: 'scatter',
            mode: 'lines',
            fill: 'tozeroy',
            fillcolor: 'rgba(16, 185, 129, 0.2)',
            line: { color: '#10b981', width: 3 },
            hovertemplate: '%{x}歳: %{y:,.0f}円<extra></extra>'
        }
    ];

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: {
            title: '年齢',
            dtick: 5,
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        yaxis: {
            title: '配当金 (円)',
            tickformat: ',.0f',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        hovermode: 'x unified',
        legend: {
            orientation: 'h',
            y: -0.2
        },
        margin: { t: 30, r: 30, b: 80, l: 80 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };

    Plotly.newPlot('dividendChart', traces, layout, config);
}

// ========== 資産内訳円グラフ（年始・年末） ==========
function renderAssetsPieCharts(assetsData) {
    const assetsStart = assetsData.assets_start;
    const assetsEnd = assetsData.assets_end;

    // 年始の円グラフ
    const startLabels = [];
    const startValues = [];
    const allColors = ['#1e3a8a', '#3b82f6', '#0ea5e9', '#8b5cf6', '#f472b6', '#6ee7b7', '#ec4899', '#f59e0b', '#10b981'];
    const startColors = [];

    const addStart = (label, value, color) => {
        if (value > 0) { startLabels.push(label); startValues.push(value); startColors.push(color); }
    };
    addStart('NISA(オルカン)',  assetsStart.nisa_orcan || 0,       '#1e3a8a');
    addStart('NISA(FANG+)',    assetsStart.nisa_fang  || 0,       '#3b82f6');
    addStart('NISA(SP500)',    assetsStart.nisa_sp500 || 0,       '#0ea5e9');
    addStart('配偶者NISA',     (assetsStart.spouse_nisa_orcan || 0) + (assetsStart.spouse_nisa_sp500 || 0), '#f472b6');
    addStart('子供NISA',       (assetsStart.child1_nisa || 0) + (assetsStart.child2_nisa || 0), '#6ee7b7');
    addStart('自社株',          assetsStart.company_stock || 0,    '#8b5cf6');
    addStart('特定口座',        assetsStart.taxable_account || 0,  '#ec4899');
    addStart('教育資金',        assetsStart.education_fund || 0,   '#f59e0b');
    addStart('現金・預金',      assetsStart.cash || 0,             '#10b981');

    const startTrace = {
        labels: startLabels,
        values: startValues,
        type: 'pie',
        marker: { colors: startColors },
        textinfo: 'label+percent',
        textposition: 'inside',
        hovertemplate: '%{label}: %{value:,.0f}円<br>%{percent}<extra></extra>'
    };

    const startLayout = {
        ...getPlotlyTheme(),
        showlegend: true,
        legend: {
            orientation: 'v',
            x: 1.1,
            y: 0.5
        },
        margin: { t: 20, r: 150, b: 20, l: 20 }
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot('assetsStartPieChart', [startTrace], startLayout, config);

    // 年末の円グラフ
    const endLabels = [];
    const endValues = [];
    const endColors = [];

    const addEnd = (label, value, color) => {
        if (value > 0) { endLabels.push(label); endValues.push(value); endColors.push(color); }
    };
    addEnd('NISA(オルカン)',  assetsEnd.nisa_orcan || 0,       '#1e3a8a');
    addEnd('NISA(FANG+)',    assetsEnd.nisa_fang  || 0,       '#3b82f6');
    addEnd('NISA(SP500)',    assetsEnd.nisa_sp500 || 0,       '#0ea5e9');
    addEnd('配偶者NISA',     (assetsEnd.spouse_nisa_orcan || 0) + (assetsEnd.spouse_nisa_sp500 || 0), '#f472b6');
    addEnd('子供NISA',       (assetsEnd.child1_nisa || 0) + (assetsEnd.child2_nisa || 0), '#6ee7b7');
    addEnd('自社株',          assetsEnd.company_stock || 0,    '#8b5cf6');
    addEnd('特定口座',        assetsEnd.taxable_account || 0,  '#ec4899');
    addEnd('教育資金',        assetsEnd.education_fund || 0,   '#f59e0b');
    addEnd('現金・預金',      assetsEnd.cash || 0,             '#10b981');

    const endTrace = {
        labels: endLabels,
        values: endValues,
        type: 'pie',
        marker: { colors: endColors },
        textinfo: 'label+percent',
        textposition: 'inside',
        hovertemplate: '%{label}: %{value:,.0f}円<br>%{percent}<extra></extra>'
    };

    const endLayout = {
        ...getPlotlyTheme(),
        showlegend: true,
        legend: {
            orientation: 'v',
            x: 1.1,
            y: 0.5
        },
        margin: { t: 20, r: 150, b: 20, l: 20 }
    };

    Plotly.newPlot('assetsEndPieChart', [endTrace], endLayout, config);
}

// ==================== 計画 vs 実績グラフ ====================

/**
 * 計画値と実績値の比較グラフを3系統（収入・支出・投資）描画
 * @param {Array} comparisonData - get_plan_vs_actual() の返り値
 */
function renderActualComparisonCharts(comparisonData) {
    if (!comparisonData || comparisonData.length === 0) return;

    const isDark = document.body.classList.contains('dark-mode');
    const textColor  = isDark ? '#f9fafb' : '#111827';
    const gridColor  = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
    const plotBg     = isDark ? '#1f2937' : '#ffffff';
    const paperBg    = isDark ? '#111827' : '#ffffff';
    const config = { responsive: true, displayModeBar: false };

    // 全年の計画値
    const ages = comparisonData.map(d => `${d.age}歳 (${d.year})`);
    const planIncome     = comparisonData.map(d => Math.round(d.plan_income / 10000));
    const planExpenses   = comparisonData.map(d => Math.round(d.plan_expenses / 10000));
    const planInvestment = comparisonData.map(d => Math.round(d.plan_investment / 10000));

    // 実績値（未入力はnull → グラフに表示されない）
    const actualIncome     = comparisonData.map(d => d.actual_income     != null ? Math.round(d.actual_income / 10000)     : null);
    const actualExpenses   = comparisonData.map(d => d.actual_expenses   != null ? Math.round(d.actual_expenses / 10000)   : null);
    const actualInvestment = comparisonData.map(d => d.actual_investment  != null ? Math.round(d.actual_investment / 10000) : null);

    // 乖離（差分）
    const incomeDiff     = comparisonData.map(d => d.income_diff     != null ? Math.round(d.income_diff / 10000)     : null);
    const expensesDiff   = comparisonData.map(d => d.expenses_diff   != null ? Math.round(d.expenses_diff / 10000)   : null);
    const investmentDiff = comparisonData.map(d => d.investment_diff != null ? Math.round(d.investment_diff / 10000) : null);

    const baseLayout = (title) => ({
        title: { text: title, font: { color: textColor } },
        xaxis: { tickfont: { color: textColor, size: 10 }, gridcolor: gridColor, tickangle: -45 },
        yaxis: { title: '万円', tickfont: { color: textColor }, gridcolor: gridColor },
        yaxis2: { title: '乖離（万円）', overlaying: 'y', side: 'right', tickfont: { color: textColor }, zeroline: true, zerolinecolor: gridColor },
        plot_bgcolor: plotBg,
        paper_bgcolor: paperBg,
        font: { color: textColor },
        legend: { font: { color: textColor } },
        barmode: 'overlay',
        margin: { t: 50, r: 80, b: 100, l: 60 }
    });

    // ---- 収入グラフ ----
    Plotly.newPlot('actualIncomeChart', [
        { type: 'bar', name: '計画収入', x: ages, y: planIncome,    marker: { color: 'rgba(59,130,246,0.3)' }, yaxis: 'y' },
        { type: 'bar', name: '実績収入', x: ages, y: actualIncome,  marker: { color: 'rgba(16,185,129,0.8)' }, yaxis: 'y' },
        { type: 'scatter', mode: 'lines+markers', name: '乖離', x: ages, y: incomeDiff,
          line: { color: '#f59e0b', width: 2 }, marker: { size: 6 }, yaxis: 'y2' }
    ], baseLayout('収入: 計画 vs 実績'), config);

    // ---- 支出グラフ ----
    Plotly.newPlot('actualExpensesChart', [
        { type: 'bar', name: '計画支出', x: ages, y: planExpenses,    marker: { color: 'rgba(239,68,68,0.3)' }, yaxis: 'y' },
        { type: 'bar', name: '実績支出', x: ages, y: actualExpenses,  marker: { color: 'rgba(239,68,68,0.8)' }, yaxis: 'y' },
        { type: 'scatter', mode: 'lines+markers', name: '乖離', x: ages, y: expensesDiff,
          line: { color: '#f59e0b', width: 2 }, marker: { size: 6 }, yaxis: 'y2' }
    ], baseLayout('支出: 計画 vs 実績'), config);

    // ---- 投資グラフ ----
    Plotly.newPlot('actualInvestmentChart', [
        { type: 'bar', name: '計画投資', x: ages, y: planInvestment,    marker: { color: 'rgba(139,92,246,0.3)' }, yaxis: 'y' },
        { type: 'bar', name: '実績投資', x: ages, y: actualInvestment,  marker: { color: 'rgba(139,92,246,0.8)' }, yaxis: 'y' },
        { type: 'scatter', mode: 'lines+markers', name: '乖離', x: ages, y: investmentDiff,
          line: { color: '#f59e0b', width: 2 }, marker: { size: 6 }, yaxis: 'y2' }
    ], baseLayout('投資額: 計画 vs 実績'), config);
}

// ========== 実績ベース将来予測チャート ==========
function renderActualPredictionChart(data, fromAge, elementId) {
    if (!data || data.length === 0) return;

    const ages = data.map(d => d.age);
    const planAssets = data.map(d => d.assets_end);
    const adjAssets  = data.map(d => d.assets_end_adjusted);

    const tracePlan = {
        x: ages, y: planAssets,
        type: 'scatter', mode: 'lines',
        name: '計画資産',
        line: { color: '#94a3b8', width: 2, dash: 'dot' },
        hovertemplate: '%{x}歳 (計画): %{y:,.0f}円<extra></extra>'
    };

    const traceAdj = {
        x: ages, y: adjAssets,
        type: 'scatter', mode: 'lines+markers',
        name: '実績調整後資産',
        line: { color: '#3b82f6', width: 3 },
        marker: { size: 5, color: '#1d4ed8' },
        hovertemplate: '%{x}歳 (調整後): %{y:,.0f}円<extra></extra>'
    };

    // 実績基準点
    const basePoint = data.find(d => d.age === fromAge);
    const traceBase = basePoint ? {
        x: [fromAge], y: [basePoint.assets_end_adjusted],
        type: 'scatter', mode: 'markers',
        name: '実績基準点',
        marker: { size: 12, color: '#10b981', symbol: 'star' },
        hovertemplate: `${fromAge}歳 (実績基準): %{y:,.0f}円<extra></extra>`
    } : null;

    const traces = traceBase ? [tracePlan, traceAdj, traceBase] : [tracePlan, traceAdj];

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: {
            title: '年齢',
            dtick: 5,
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        yaxis: {
            title: '資産額 (円)',
            tickformat: ',.0f',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        legend: { orientation: 'h', y: -0.15 },
        hovermode: 'x unified',
        margin: { t: 30, r: 30, b: 60, l: 80 }
    };

    Plotly.newPlot(elementId, traces, layout, { responsive: true, displaylogo: false });
}

// ========== 給与曲線チャート（エディタ用） ==========
function renderSalaryCurveChart(salaryData) {
    if (!salaryData || salaryData.length === 0) return;
    const el = document.getElementById('salaryCurveChart');
    if (!el) return;

    const ages    = salaryData.map(d => d.age);
    const annual  = salaryData.map(d => d.annual_income);
    const base    = salaryData.map(d => d.base_salary);

    const traceAnnual = {
        x: ages, y: annual,
        type: 'scatter', mode: 'lines+markers',
        name: '年収（基本給＋賞与）',
        line: { color: '#3b82f6', width: 3 },
        marker: {
            size: salaryData.map(d => d.is_anchor ? 10 : 5),
            color: salaryData.map(d => d.is_anchor ? '#f59e0b' : '#3b82f6'),
            symbol: salaryData.map(d => d.is_anchor ? 'diamond' : 'circle')
        },
        hovertemplate: '%{x}歳: %{y:,.0f}円<extra></extra>'
    };

    const traceBase = {
        x: ages, y: base,
        type: 'scatter', mode: 'lines',
        name: '基本給',
        line: { color: '#94a3b8', width: 1.5, dash: 'dot' },
        hovertemplate: '%{x}歳 基本給: %{y:,.0f}円<extra></extra>'
    };

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: {
            title: '年齢',
            dtick: 5,
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        yaxis: {
            title: '金額 (円)',
            tickformat: ',.0f',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        legend: { orientation: 'h', y: -0.2 },
        hovermode: 'x unified',
        margin: { t: 20, r: 20, b: 60, l: 80 }
    };

    Plotly.newPlot('salaryCurveChart', [traceAnnual, traceBase], layout, {
        responsive: true, displaylogo: false
    });
}

// ========== モンテカルロ 資産推移グラフ ==========
/**
 * モンテカルロ結果を信頼区間バンド付きで描画
 * @param {Array} results - [{label, color, data: {ages,p5,p25,p50,p75,p95,mean}}, ...]
 * @param {string} elementId
 */
function renderMonteCarloChart(results, elementId) {
    if (!results || results.length === 0) return;

    const traces = [];

    results.forEach(({ label, color, data }) => {
        const ages = data.ages;
        const rev  = (arr) => arr.slice().reverse();
        const revAges = ages.slice().reverse();

        // 5-95% バンド（薄い）
        traces.push({
            x: [...ages, ...revAges],
            y: [...data.p95, ...rev(data.p5)],
            fill: 'toself',
            fillcolor: color.band95,
            line: { color: 'transparent' },
            name: `5-95% (${label})`,
            showlegend: true,
            hoverinfo: 'skip',
        });

        // 25-75% バンド（濃い）
        traces.push({
            x: [...ages, ...revAges],
            y: [...data.p75, ...rev(data.p25)],
            fill: 'toself',
            fillcolor: color.band75,
            line: { color: 'transparent' },
            name: `25-75% (${label})`,
            showlegend: true,
            hoverinfo: 'skip',
        });

        // 中央値ライン
        traces.push({
            x: ages, y: data.p50,
            type: 'scatter', mode: 'lines',
            name: `中央値 (${label})`,
            line: { color: color.median, width: 2.5 },
            hovertemplate: `%{x}歳 中央値(${label}): %{y:,.0f}円<extra></extra>`,
        });

        // 平均ライン（破線）
        traces.push({
            x: ages, y: data.mean,
            type: 'scatter', mode: 'lines',
            name: `平均 (${label})`,
            line: { color: color.mean, width: 1.5, dash: 'dot' },
            hovertemplate: `%{x}歳 平均(${label}): %{y:,.0f}円<extra></extra>`,
        });
    });

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: { title: '年齢', dtick: 5, gridcolor: isDarkMode ? '#374151' : '#e5e7eb' },
        yaxis: { title: '資産額 (円)', tickformat: ',.0f', gridcolor: isDarkMode ? '#374151' : '#e5e7eb' },
        hovermode: 'x unified',
        legend: { orientation: 'h', y: -0.2 },
        margin: { t: 20, r: 30, b: 80, l: 80 },
    };

    Plotly.newPlot(elementId, traces, layout, { responsive: true, displaylogo: false });
}

// ========== モンテカルロ 最終資産分布グラフ ==========
/**
 * 各シナリオの最終資産パーセンタイルをグループ棒グラフで表示
 * @param {Array} results - [{label, color, data}, ...]
 * @param {string} elementId
 */
function renderMCDistributionChart(results, elementId) {
    if (!results || results.length === 0) return;

    const percentileLabels = ['最悪 (p5)', '悪い (p25)', '中央 (p50)', '良い (p75)', '最良 (p95)', '平均'];
    const keys = ['final_p5', 'final_p25', 'final_p50', 'final_p75', 'final_p95', 'final_mean'];

    const traces = results.map(({ label, color, data }) => ({
        x: percentileLabels,
        y: keys.map(k => data[k] || 0),
        type: 'bar',
        name: label,
        marker: { color: color.median, opacity: 0.8 },
        hovertemplate: `%{x} (${label}): %{y:,.0f}円<extra></extra>`,
    }));

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        barmode: 'group',
        xaxis: { gridcolor: isDarkMode ? '#374151' : '#e5e7eb' },
        yaxis: { title: '資産額 (円)', tickformat: ',.0f', gridcolor: isDarkMode ? '#374151' : '#e5e7eb' },
        legend: { orientation: 'h', y: -0.2 },
        margin: { t: 20, r: 30, b: 80, l: 80 },
    };

    Plotly.newPlot(elementId, traces, layout, { responsive: true, displaylogo: false });
}

console.log('charts.js ロード完了');
