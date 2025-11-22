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
            y: yearlyData.map(d => d.nisa_growth),
            name: 'NISA成長投資枠',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#3b82f6',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - NISA成長: %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: yearlyData.map(d => d.nisa_tsumitate),
            name: 'NISAつみたて枠',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#1e3a8a',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - NISAつみたて: %{y:,.0f}円<extra></extra>'
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
        'nisa_tsumitate': 'NISAつみたて',
        'nisa_growth': 'NISA成長投資',
        'company_stock': '自社株',
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
    const colors = ['#1e3a8a', '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'];

    if (assetsStart.nisa_tsumitate > 0) {
        startLabels.push('NISAつみたて');
        startValues.push(assetsStart.nisa_tsumitate);
    }
    if (assetsStart.nisa_growth > 0) {
        startLabels.push('NISA成長');
        startValues.push(assetsStart.nisa_growth);
    }
    if (assetsStart.company_stock > 0) {
        startLabels.push('自社株');
        startValues.push(assetsStart.company_stock);
    }
    if (assetsStart.taxable_account > 0) {
        startLabels.push('特定口座');
        startValues.push(assetsStart.taxable_account);
    }
    if (assetsStart.education_fund > 0) {
        startLabels.push('教育資金');
        startValues.push(assetsStart.education_fund);
    }
    if (assetsStart.cash > 0) {
        startLabels.push('現金・預金');
        startValues.push(assetsStart.cash);
    }

    const startTrace = {
        labels: startLabels,
        values: startValues,
        type: 'pie',
        marker: {
            colors: colors.slice(0, startLabels.length)
        },
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

    if (assetsEnd.nisa_tsumitate > 0) {
        endLabels.push('NISAつみたて');
        endValues.push(assetsEnd.nisa_tsumitate);
    }
    if (assetsEnd.nisa_growth > 0) {
        endLabels.push('NISA成長');
        endValues.push(assetsEnd.nisa_growth);
    }
    if (assetsEnd.company_stock > 0) {
        endLabels.push('自社株');
        endValues.push(assetsEnd.company_stock);
    }
    if (assetsEnd.taxable_account > 0) {
        endLabels.push('特定口座');
        endValues.push(assetsEnd.taxable_account);
    }
    if (assetsEnd.education_fund > 0) {
        endLabels.push('教育資金');
        endValues.push(assetsEnd.education_fund);
    }
    if (assetsEnd.cash > 0) {
        endLabels.push('現金・預金');
        endValues.push(assetsEnd.cash);
    }

    const endTrace = {
        labels: endLabels,
        values: endValues,
        type: 'pie',
        marker: {
            colors: colors.slice(0, endLabels.length)
        },
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

// ========== 退職後シミュレーション用グラフ ==========
function renderRetirementAssetsChart(data) {
    const ages = data.map(d => d.age);
    const totalAssets = data.map(d => d.assets.total);

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
        fill: 'tozeroy',
        fillcolor: 'rgba(59, 130, 246, 0.1)',
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
        displaylogo: false
    };

    Plotly.newPlot('retirementAssetsChart', [trace], layout, config);
}

function renderRetirementAssetsBreakdownChart(data) {
    const ages = data.map(d => d.age);

    const traces = [
        {
            x: ages,
            y: data.map(d => d.assets.cash),
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
            y: data.map(d => d.assets.taxable_account),
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
            y: data.map(d => d.assets.company_stock),
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
            y: data.map(d => d.assets.nisa_growth),
            name: 'NISA成長投資枠',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#3b82f6',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - NISA成長: %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: data.map(d => d.assets.nisa_tsumitate),
            name: 'NISAつみたて枠',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#1e3a8a',
            line: { width: 0 },
            hovertemplate: '%{x}歳 - NISAつみたて: %{y:,.0f}円<extra></extra>'
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

    Plotly.newPlot('retirementAssetsBreakdownChart', traces, layout, config);
}

function renderRetirementCashflowChart(data) {
    const ages = data.map(d => d.age);
    const cashflows = data.map(d => d.cashflow);

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

    Plotly.newPlot('retirementCashflowChart', [trace], layout, config);
}

function renderRetirementIncomeBreakdownChart(data) {
    const ages = data.map(d => d.age);

    const traces = [
        {
            x: ages,
            y: data.map(d => d.income.pension),
            name: '年金収入',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#10b981',
            line: { width: 1, color: '#059669' },
            hovertemplate: '%{x}歳 - 年金: %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: data.map(d => d.income.dividend),
            name: '配当金',
            type: 'scatter',
            mode: 'lines',
            stackgroup: 'one',
            fillcolor: '#3b82f6',
            line: { width: 1, color: '#2563eb' },
            hovertemplate: '%{x}歳 - 配当金: %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages,
            y: data.map(d => d.withdrawal),
            name: '資産取り崩し',
            type: 'scatter',
            mode: 'lines',
            line: { width: 3, color: '#ef4444', dash: 'dot' },
            hovertemplate: '%{x}歳 - 取り崩し: %{y:,.0f}円<extra></extra>'
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
            title: '金額 (円)',
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

    Plotly.newPlot('retirementIncomeBreakdownChart', traces, layout, config);
}

// ========== モンテカルロシミュレーション用グラフ ==========
function renderMontecarloHistogram(distribution) {
    const trace = {
        x: distribution,
        type: 'histogram',
        nbinsx: 50,
        marker: {
            color: '#3b82f6',
            line: {
                color: '#1e3a8a',
                width: 1
            }
        },
        hovertemplate: '資産額: %{x:,.0f}円<br>件数: %{y}<extra></extra>'
    };

    const layout = {
        ...getPlotlyTheme(),
        title: '',
        xaxis: {
            title: '最終資産額 (円)',
            tickformat: ',.0f',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        yaxis: {
            title: 'シミュレーション回数',
            gridcolor: isDarkMode ? '#374151' : '#e5e7eb'
        },
        bargap: 0.05,
        margin: { t: 30, r: 30, b: 60, l: 80 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };

    Plotly.newPlot('montecarloHistogram', [trace], layout, config);
}

function renderMontecarloPercentileChart(allResults, percentiles) {
    // 10th, 50th, 90thパーセンタイルの3つのシミュレーションを選択
    const p10Result = allResults.find(r => Math.abs(r.final_assets - percentiles['10th']) < 1000000);
    const p50Result = allResults.find(r => Math.abs(r.final_assets - percentiles['50th']) < 1000000);
    const p90Result = allResults.find(r => Math.abs(r.final_assets - percentiles['90th']) < 1000000);

    if (!p10Result || !p50Result || !p90Result) {
        console.error('パーセンタイルデータが見つかりません');
        return;
    }

    const ages10 = p10Result.yearly_data.map(d => d.age);
    const assets10 = p10Result.yearly_data.map(d => d.assets_end);

    const ages50 = p50Result.yearly_data.map(d => d.age);
    const assets50 = p50Result.yearly_data.map(d => d.assets_end);

    const ages90 = p90Result.yearly_data.map(d => d.age);
    const assets90 = p90Result.yearly_data.map(d => d.assets_end);

    const traces = [
        {
            x: ages90,
            y: assets90,
            type: 'scatter',
            mode: 'lines',
            name: '最良ケース (90%)',
            line: {
                color: '#10b981',
                width: 3
            },
            hovertemplate: '%{x}歳: %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages50,
            y: assets50,
            type: 'scatter',
            mode: 'lines',
            name: '標準ケース (50%)',
            line: {
                color: '#3b82f6',
                width: 3
            },
            hovertemplate: '%{x}歳: %{y:,.0f}円<extra></extra>'
        },
        {
            x: ages10,
            y: assets10,
            type: 'scatter',
            mode: 'lines',
            name: '最悪ケース (10%)',
            line: {
                color: '#ef4444',
                width: 3
            },
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

    Plotly.newPlot('montecarloPercentileChart', traces, layout, config);
}

console.log('charts.js ロード完了');
