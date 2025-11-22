/**
 * メインアプリケーションロジック
 * UIコントロールとデータ管理
 */

// グローバル状態
let simulationData = null;
let retirementData = null; // 退職後シミュレーションデータ
let montecarloData = null; // モンテカルロシミュレーションデータ
let montecarloAdvancedData = null; // 本気モンテカルロシミュレーションデータ
let currentAge = 25;
let isDarkMode = false;
let currentScenarioResults = null; // 現在のシナリオ比較結果
let baselineData = null; // 初期値（ベースライン）データ
let ageUpdateTimer = null; // 年齢更新のデバウンスタイマー
let lastRenderedAge = null; // 最後に描画した年齢（重複描画防止）

// ========== 初期化 ==========
document.addEventListener('DOMContentLoaded', () => {
    console.log('アプリケーション初期化中...');

    // イベントリスナー設定
    setupEventListeners();

    // ダークモード初期状態を読み込み
    loadDarkModePreference();

    // シミュレーション実行
    runSimulation();
});

// ========== イベントリスナー設定 ==========
function setupEventListeners() {
    // ナビゲーションタブ
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            switchView(e.target.dataset.view);
        });
    });

    // ダークモードトグル
    document.getElementById('darkModeToggle').addEventListener('click', toggleDarkMode);

    // 年齢セレクター（デバウンス処理）
    const ageSelector = document.getElementById('ageSelector');
    if (ageSelector) {
        ageSelector.addEventListener('input', (e) => {
            currentAge = parseInt(e.target.value);
            document.getElementById('ageDisplay').textContent = `${currentAge}歳`;

            // デバウンス: 150ms後に更新実行（応答性向上）
            clearTimeout(ageUpdateTimer);
            ageUpdateTimer = setTimeout(() => {
                updateYearlyDetailView(currentAge);
            }, 150);
        });
    }

    // CSVエクスポートボタン
    document.getElementById('exportBtn').addEventListener('click', exportToCSV);

    // 設定ボタン
    document.getElementById('settingsBtn').addEventListener('click', openSettingsModal);

    // シナリオ比較実行ボタン
    const scenarioBtn = document.getElementById('runScenarioBtn');
    if (scenarioBtn) {
        scenarioBtn.addEventListener('click', runScenarioComparison);
    }

    // シナリオ保存ボタン
    const saveScenarioBtn = document.getElementById('saveScenarioBtn');
    if (saveScenarioBtn) {
        saveScenarioBtn.addEventListener('click', saveScenario);
    }

    // モンテカルロ実行ボタン
    const montecarloBtn = document.getElementById('runMontecarloBtn');
    if (montecarloBtn) {
        montecarloBtn.addEventListener('click', runMontecarloSimulation);
    }

    // 本気モンテカルロ実行ボタン
    const montecarloAdvancedBtn = document.getElementById('runMontecarloAdvancedBtn');
    if (montecarloAdvancedBtn) {
        montecarloAdvancedBtn.addEventListener('click', runMontecarloAdvancedSimulation);
    }
}

// ========== ビュー切り替え ==========
function switchView(viewName) {
    // すべてのビューを非表示
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });

    // すべてのタブを非アクティブ化
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // 選択されたビューを表示
    const targetView = document.getElementById(`${viewName}-view`);
    if (targetView) {
        targetView.classList.add('active');
    }

    // 選択されたタブをアクティブ化
    const targetTab = document.querySelector(`.nav-tab[data-view="${viewName}"]`);
    if (targetTab) {
        targetTab.classList.add('active');
    }

    // ビュー固有の初期化処理（遅延読み込み）
    if (viewName === 'dashboard' && simulationData) {
        // ダッシュボードは既に描画済み
    } else if (viewName === 'cashflow' && simulationData) {
        // キャッシュフローグラフを描画
        renderCashflowChart();
        renderCumulativeCashflowChart();
    } else if (viewName === 'retirement') {
        // 退職後シミュレーションを実行
        runRetirementSimulation();
    } else if (viewName === 'montecarlo') {
        // モンテカルロビューは手動実行（ボタンを押すまで待機）
        if (montecarloData) {
            renderMontecarloView();
        }
    } else if (viewName === 'timeline' && simulationData) {
        // タイムラインを描画
        renderTimelineChart();
        renderEventsList();
    } else if (viewName === 'yearly-detail' && simulationData) {
        updateYearlyDetailView(currentAge);
    } else if (viewName === 'education' && simulationData) {
        renderEducationView();
    } else if (viewName === 'dividend' && simulationData) {
        renderDividendView();
    } else if (viewName === 'scenario') {
        // 保存済みシナリオを読み込み
        renderSavedScenarios();
    }
}

// ========== ダークモード ==========
function toggleDarkMode() {
    isDarkMode = !isDarkMode;
    document.body.classList.toggle('dark-mode', isDarkMode);

    // アイコン切り替え
    const iconDark = document.querySelector('.icon-dark');
    const iconLight = document.querySelector('.icon-light');

    if (isDarkMode) {
        iconDark.style.display = 'none';
        iconLight.style.display = 'inline';
    } else {
        iconDark.style.display = 'inline';
        iconLight.style.display = 'none';
    }

    // ローカルストレージに保存
    localStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled');

    // 現在のビューのグラフのみ再描画（ダークモード対応）
    if (simulationData) {
        const activeView = document.querySelector('.view.active');
        if (activeView) {
            const viewId = activeView.id;
            if (viewId === 'dashboard-view') {
                renderAssetsChart();
                renderAssetsBreakdownChart();
            } else if (viewId === 'cashflow-view') {
                renderCashflowChart();
                renderCumulativeCashflowChart();
            } else if (viewId === 'timeline-view') {
                renderTimelineChart();
            } else if (viewId === 'yearly-detail-view') {
                updateYearlyDetailView(currentAge);
            } else if (viewId === 'education-view') {
                renderEducationView();
            } else if (viewId === 'dividend-view') {
                renderDividendView();
            } else if (viewId === 'retirement-view') {
                if (retirementData) {
                    renderRetirementView();
                }
            } else if (viewId === 'montecarlo-view') {
                if (montecarloData) {
                    renderMontecarloView();
                }
            } else if (viewId === 'scenario-view') {
                if (currentScenarioResults) {
                    renderScenarioComparisonChart(currentScenarioResults.data);
                }
            }
        }
    }
}

function loadDarkModePreference() {
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode === 'enabled') {
        isDarkMode = true;
        document.body.classList.add('dark-mode');
        document.querySelector('.icon-dark').style.display = 'none';
        document.querySelector('.icon-light').style.display = 'inline';
    }
}

// ========== シミュレーション実行 ==========
async function runSimulation() {
    showLoading(true);

    try {
        const result = await eel.run_simulation()();

        if (result.success) {
            simulationData = result.data;
            console.log('シミュレーション成功:', simulationData);

            // ベースラインデータを保存（初回のみ）
            if (!baselineData) {
                baselineData = JSON.parse(JSON.stringify(result.data));
            }

            // ダッシュボード更新
            updateDashboard();

            // ダッシュボードのグラフのみ描画（他は必要時に遅延読み込み）
            renderAssetsChart();
            renderAssetsBreakdownChart();

            showLoading(false);
        } else {
            console.error('シミュレーションエラー:', result.error);
            alert('シミュレーションに失敗しました: ' + result.error);
            showLoading(false);
        }
    } catch (error) {
        console.error('通信エラー:', error);
        alert('サーバーとの通信に失敗しました');
        showLoading(false);
    }
}

// ========== 退職後シミュレーション実行 ==========
async function runRetirementSimulation() {
    // 既にデータがあれば再描画のみ
    if (retirementData) {
        renderRetirementView();
        return;
    }

    showLoading(true);

    try {
        const result = await eel.run_retirement_simulation()();

        if (result.success) {
            retirementData = result.data;
            console.log('退職後シミュレーション成功:', retirementData);

            // ビューを更新
            renderRetirementView();
            showLoading(false);
        } else {
            console.error('退職後シミュレーションエラー:', result.error);
            alert('退職後シミュレーションに失敗しました: ' + result.error);
            showLoading(false);
        }
    } catch (error) {
        console.error('通信エラー:', error);
        alert('サーバーとの通信に失敗しました');
        showLoading(false);
    }
}

function renderRetirementView() {
    if (!retirementData) return;

    const summary = retirementData.summary;
    const data = retirementData.retirement_data;

    // サマリーカード更新
    document.getElementById('retirementStartAssets').textContent = formatCurrency(summary.start_assets);
    document.getElementById('retirementFinalAssets').textContent = formatCurrency(summary.final_assets);
    document.getElementById('retirementTotalPension').textContent = formatCurrency(summary.total_pension);
    document.getElementById('retirementTotalDividend').textContent = formatCurrency(summary.total_dividend);
    document.getElementById('retirementTotalWithdrawal').textContent = formatCurrency(summary.total_withdrawal);

    // 資産枯渇リスク表示
    const depletionAge = summary.depletion_age;
    const retirementWarning = document.getElementById('retirementWarning');
    const depletionAgeElement = document.getElementById('retirementDepletionAge');

    if (depletionAge) {
        depletionAgeElement.textContent = `${depletionAge}歳で枯渇`;
        depletionAgeElement.classList.add('text-red');
        retirementWarning.style.display = 'block';
    } else {
        depletionAgeElement.textContent = '90歳まで安心';
        depletionAgeElement.classList.add('text-green');
        retirementWarning.style.display = 'none';
    }

    // 色分け
    if (summary.final_assets < 10000000) {
        document.getElementById('retirementFinalAssets').classList.add('text-red');
    } else {
        document.getElementById('retirementFinalAssets').classList.add('text-green');
    }

    // グラフを描画
    renderRetirementAssetsChart(data);
    renderRetirementAssetsBreakdownChart(data);
    renderRetirementCashflowChart(data);
    renderRetirementIncomeBreakdownChart(data);
}

// ========== モンテカルロシミュレーション実行 ==========
async function runMontecarloSimulation() {
    const iterations = parseInt(document.getElementById('montecarloIterations').value);
    const btn = document.getElementById('runMontecarloBtn');

    btn.disabled = true;
    btn.textContent = `⏳ 計算中... (${iterations}回実行)`;
    showLoading(true);

    try {
        const result = await eel.run_monte_carlo_simulation(iterations)();

        if (result.success) {
            montecarloData = result.data;
            console.log('モンテカルロシミュレーション成功:', montecarloData);

            // 結果を表示
            renderMontecarloView();

            btn.disabled = false;
            btn.textContent = '🎲 モンテカルロ計算を開始';
            showLoading(false);
        } else {
            console.error('モンテカルロシミュレーションエラー:', result.error);
            alert('モンテカルロシミュレーションに失敗しました: ' + result.error);
            btn.disabled = false;
            btn.textContent = '🎲 モンテカルロ計算を開始';
            showLoading(false);
        }
    } catch (error) {
        console.error('通信エラー:', error);
        alert('サーバーとの通信に失敗しました');
        btn.disabled = false;
        btn.textContent = '🎲 モンテカルロ計算を開始';
        showLoading(false);
    }
}

function renderMontecarloView() {
    if (!montecarloData) return;

    const summary = montecarloData.summary;

    // 結果エリアを表示
    document.getElementById('montecarloResults').style.display = 'block';

    // サマリーカード更新
    document.getElementById('montecarloMedian').textContent = formatCurrency(summary.median);
    document.getElementById('montecarloMean').textContent = formatCurrency(summary.mean);
    document.getElementById('montecarlo90th').textContent = formatCurrency(summary.percentiles['90th']);
    document.getElementById('montecarlo10th').textContent = formatCurrency(summary.percentiles['10th']);

    // 確率表示
    document.getElementById('montecarlo50mProb').textContent = summary.target_probabilities['50m'].toFixed(1) + '%';
    document.getElementById('montecarlo70mProb').textContent = summary.target_probabilities['70m'].toFixed(1) + '%';
    document.getElementById('montecarlo100mProb').textContent = summary.target_probabilities['100m'].toFixed(1) + '%';

    // グラフを描画
    renderMontecarloHistogram(montecarloData.distribution);
    renderMontecarloPercentileChart(montecarloData.all_results, summary.percentiles);
}

// ========== 本気モンテカルロシミュレーション実行 ==========
async function runMontecarloAdvancedSimulation() {
    const iterations = parseInt(document.getElementById('montecarloAdvancedIterations').value);
    const btn = document.getElementById('runMontecarloAdvancedBtn');

    btn.disabled = true;
    btn.textContent = `⏳ 本気計算中... (${iterations}回実行)`;
    showLoading(true);

    try {
        const result = await eel.run_monte_carlo_advanced_simulation(iterations)();

        if (result.success) {
            montecarloAdvancedData = result.data;
            console.log('本気モンテカルロシミュレーション成功:', montecarloAdvancedData);

            // 結果を表示
            renderMontecarloAdvancedView();

            btn.disabled = false;
            btn.textContent = '🚀 本気モンテカルロ計算を開始';
            showLoading(false);
        } else {
            console.error('本気モンテカルロシミュレーションエラー:', result.error);
            alert('本気モンテカルロシミュレーションに失敗しました: ' + result.error);
            btn.disabled = false;
            btn.textContent = '🚀 本気モンテカルロ計算を開始';
            showLoading(false);
        }
    } catch (error) {
        console.error('通信エラー:', error);
        alert('サーバーとの通信に失敗しました');
        btn.disabled = false;
        btn.textContent = '🚀 本気モンテカルロ計算を開始';
        showLoading(false);
    }
}

function renderMontecarloAdvancedView() {
    if (!montecarloAdvancedData) return;

    const summary = montecarloAdvancedData.summary;

    // 結果エリアを表示
    document.getElementById('montecarloAdvancedResults').style.display = 'block';

    // サマリーカード更新
    document.getElementById('montecarloAdvancedMedian').textContent = formatCurrency(summary.median);
    document.getElementById('montecarloAdvancedMean').textContent = formatCurrency(summary.mean);
    document.getElementById('montecarloAdvanced90th').textContent = formatCurrency(summary.percentiles['90th']);
    document.getElementById('montecarloAdvanced10th').textContent = formatCurrency(summary.percentiles['10th']);

    // 確率表示
    document.getElementById('montecarloAdvanced50mProb').textContent = summary.target_probabilities['50m'].toFixed(1) + '%';
    document.getElementById('montecarloAdvanced70mProb').textContent = summary.target_probabilities['70m'].toFixed(1) + '%';
    document.getElementById('montecarloAdvanced100mProb').textContent = summary.target_probabilities['100m'].toFixed(1) + '%';

    // グラフを描画
    renderMontecarloAdvancedHistogram(montecarloAdvancedData.distribution);
    renderMontecarloAdvancedPercentileChart(summary.yearly_progression);
}

// ========== ダッシュボード更新 ==========
function updateDashboard() {
    if (!simulationData) return;

    const summary = simulationData.summary;
    const yearlyData = simulationData.yearly_data;
    const lastYear = yearlyData[yearlyData.length - 1];

    // サマリーカード更新
    document.getElementById('finalAssets').textContent = formatCurrency(summary.final_assets);
    document.getElementById('totalInvestment').textContent = formatCurrency(summary.total_investment);
    document.getElementById('totalCashflow').textContent = formatCurrency(summary.total_cashflow);
    document.getElementById('cashBalance').textContent = formatCurrency(lastYear.cash);

    // 現金残高警告
    const emergencyReserve = 3000000; // 300万円
    const cashWarning = document.getElementById('cashWarning');
    if (lastYear.cash < emergencyReserve) {
        cashWarning.style.display = 'block';
    } else {
        cashWarning.style.display = 'none';
    }

    // 金額の色分け
    document.getElementById('totalCashflow').classList.add(
        summary.total_cashflow >= 0 ? 'text-green' : 'text-red'
    );
}

// ========== 年齢別詳細ビューのクリア ==========
function clearYearlyDetailView() {
    // グラフコンテナをクリア（読み込み中表示）
    const chartIds = [
        'monthlyIncomeChart',
        'monthlyExpensesChart',
        'monthlyInvestmentChart',
        'monthlyCashflowChart',
        'assetsStartPieChart',
        'assetsEndPieChart'
    ];

    chartIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            // Plotlyグラフを完全削除
            Plotly.purge(id);
            // 読み込み中メッセージを表示
            element.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 300px; color: var(--text-secondary); font-size: 1.1rem;">📊 データ読み込み中...</div>';
        }
    });

    // サマリーカードをクリア
    document.getElementById('yearIncome').textContent = '-';
    document.getElementById('yearExpenses').textContent = '-';
    document.getElementById('yearInvestment').textContent = '-';
    document.getElementById('yearCashflow').textContent = '-';
    document.getElementById('yearEducationCost').textContent = '-';

    // 資産総額をクリア
    document.getElementById('assetsStartTotal').textContent = '-';
    document.getElementById('assetsEndTotal').textContent = '-';

    // 配当情報をクリア
    document.getElementById('yearDividendTotal').textContent = '-';
    document.getElementById('yearDividendReceived').textContent = '-';
    document.getElementById('yearCompanyDividend').textContent = '-';
    document.getElementById('yearTaxableDividend').textContent = '-';

    // テーブルをクリア
    const tableContainer = document.getElementById('monthlyDetailTable');
    if (tableContainer) {
        tableContainer.innerHTML = '<p style="color: var(--text-secondary); padding: 2rem; text-align: center;">データ読み込み中...</p>';
    }

    // イレギュラー支出を非表示
    document.getElementById('irregularExpensesSection').style.display = 'none';
}

// ========== 年齢別詳細ビュー更新 ==========
async function updateYearlyDetailView(age) {
    if (!simulationData) return;

    // 同じ年齢の重複描画を防止
    if (lastRenderedAge === age) {
        return;
    }
    lastRenderedAge = age;

    // 古いグラフとデータをすべてクリア
    clearYearlyDetailView();

    // ローディング表示
    showLoading(true);

    try {
        // 特定年齢の12ヶ月分データを取得
        const monthlyResult = await eel.get_age_detail(age)();
        // 資産詳細データを取得
        const assetsResult = await eel.get_age_assets_detail(age)();

        if (monthlyResult.success && monthlyResult.data.length > 0) {
            const monthlyData = monthlyResult.data;

            // 年間集計を計算
            const yearIncome = monthlyData.reduce((sum, m) => sum + m.income.total, 0);
            const yearExpenses = monthlyData.reduce((sum, m) => sum + m.expenses.total, 0);
            const yearInvestment = monthlyData.reduce((sum, m) => sum + m.investment.total, 0);
            const yearCashflow = monthlyData.reduce((sum, m) => sum + m.cashflow.monthly, 0);

            // サマリーカード更新
            document.getElementById('yearIncome').textContent = formatCurrency(yearIncome);
            document.getElementById('yearExpenses').textContent = formatCurrency(yearExpenses);
            document.getElementById('yearInvestment').textContent = formatCurrency(yearInvestment);
            document.getElementById('yearCashflow').textContent = formatCurrency(yearCashflow);

            // 色分け
            document.getElementById('yearCashflow').classList.remove('text-green', 'text-red');
            document.getElementById('yearCashflow').classList.add(
                yearCashflow >= 0 ? 'text-green' : 'text-red'
            );

            // 月次詳細テーブル更新（高速）
            renderMonthlyTable(monthlyData);

            // 月次グラフ更新（重い処理なので非同期化）
            setTimeout(() => renderMonthlyCharts(monthlyData), 0);
        }

        // 資産詳細データを表示
        if (assetsResult.success && assetsResult.data) {
            const assetsData = assetsResult.data;

            // 教育費を表示
            document.getElementById('yearEducationCost').textContent =
                '教育費: ' + formatCurrency(assetsData.education_cost);

            // 資産総額を表示
            document.getElementById('assetsStartTotal').textContent =
                formatCurrency(assetsData.assets_start.total);
            document.getElementById('assetsEndTotal').textContent =
                formatCurrency(assetsData.assets_end.total);

            // 配当金情報を表示
            const dividendInfo = assetsData.dividend_info;
            document.getElementById('yearDividendTotal').textContent =
                formatCurrency(dividendInfo.total_dividend_pretax);
            document.getElementById('yearDividendReceived').textContent =
                formatCurrency(dividendInfo.total_dividend_received);
            document.getElementById('yearCompanyDividend').textContent =
                formatCurrency(dividendInfo.company_stock_dividend);
            document.getElementById('yearTaxableDividend').textContent =
                formatCurrency(dividendInfo.taxable_dividend);

            // イレギュラー支出を表示（高速）
            renderIrregularExpenses(assetsData.irregular_expenses);

            // 資産内訳の円グラフを描画（重い処理なので非同期化）
            setTimeout(() => renderAssetsPieCharts(assetsData), 100);
        }

        // ローディング非表示
        showLoading(false);
    } catch (error) {
        console.error('年齢別詳細データ取得エラー:', error);
        showLoading(false);
    }
}

// ========== イレギュラー支出表示 ==========
function renderIrregularExpenses(irregularExpenses) {
    const section = document.getElementById('irregularExpensesSection');
    const list = document.getElementById('irregularExpensesList');

    if (!irregularExpenses || irregularExpenses.length === 0) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    let html = '';

    irregularExpenses.forEach(expense => {
        html += `
            <div class="irregular-expense-item">
                <div class="irregular-expense-header">
                    <span class="irregular-expense-type">${expense.type}</span>
                    <span class="irregular-expense-amount">${formatCurrency(expense.amount)}</span>
                </div>
                <div class="irregular-expense-sources">
                    <span style="font-size: 0.9rem; color: var(--text-secondary);">支払い元:</span>
        `;

        expense.payment_sources.forEach(source => {
            html += `
                <div class="irregular-expense-source">
                    <span class="irregular-expense-source-name">${source.source}</span>
                    <span class="irregular-expense-source-amount">${formatCurrency(source.amount)}</span>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;
    });

    list.innerHTML = html;
}

// ========== 月次詳細テーブル描画 ==========
function renderMonthlyTable(monthlyData) {
    const container = document.getElementById('monthlyDetailTable');
    if (!container) return;

    let html = '<table><thead><tr>';
    html += '<th>月</th><th>収入</th><th>支出</th><th>投資</th><th>収支</th><th>現金残高</th>';
    html += '</tr></thead><tbody>';

    monthlyData.forEach(month => {
        const cashflowClass = month.cashflow.monthly >= 0 ? 'text-green' : 'text-red';
        html += '<tr>';
        html += `<td>${month.month}月</td>`;
        html += `<td>${formatCurrency(month.income.total)}</td>`;
        html += `<td>${formatCurrency(month.expenses.total)}</td>`;
        html += `<td>${formatCurrency(month.investment.total)}</td>`;
        html += `<td class="${cashflowClass}">${formatCurrency(month.cashflow.monthly)}</td>`;
        html += `<td>${formatCurrency(month.assets.cash_balance)}</td>`;
        html += '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// ========== すべてのグラフを描画 ==========
function renderAllCharts() {
    if (!simulationData) return;

    // ダッシュボードのグラフ
    renderAssetsChart();
    renderAssetsBreakdownChart();

    // キャッシュフロービューのグラフ
    renderCashflowChart();
    renderCumulativeCashflowChart();

    // タイムラインビューのグラフ
    renderTimelineChart();
    renderEventsList();
}

// ========== CSV エクスポート ==========
async function exportToCSV() {
    try {
        const result = await eel.export_data_csv()();

        if (result.success) {
            // CSV文字列をダウンロード
            const blob = new Blob([result.data], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);

            link.setAttribute('href', url);
            link.setAttribute('download', `life_plan_${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            alert('CSVファイルをエクスポートしました');
        } else {
            alert('エクスポートに失敗しました: ' + result.error);
        }
    } catch (error) {
        console.error('CSVエクスポートエラー:', error);
        alert('エクスポートに失敗しました');
    }
}

// ========== シナリオ比較実行 ==========
async function runScenarioComparison() {
    showLoading(true);

    try {
        // シナリオ設定を取得
        const scenarioName = document.getElementById('scenarioName').value || '選択シナリオ';
        const returnRate = parseFloat(document.getElementById('scenarioReturn').value);
        const spouseIncome = document.getElementById('scenarioSpouse').value;
        const salaryGrowth = document.getElementById('scenarioSalary').value;

        const scenarios = [
            {
                name: '現在の設定（ベースライン）',
                investment_return: 0.05,
                spouse_income: 'あり',
                salary_growth: '標準'
            },
            {
                name: scenarioName,
                investment_return: returnRate,
                spouse_income: spouseIncome,
                salary_growth: salaryGrowth
            }
        ];

        const result = await eel.calculate_scenario_comparison(scenarios)();

        if (result.success) {
            // 結果を保存
            currentScenarioResults = {
                name: scenarioName,
                settings: {
                    investment_return: returnRate,
                    spouse_income: spouseIncome,
                    salary_growth: salaryGrowth
                },
                data: result.data
            };

            // グラフを描画
            renderScenarioComparisonChart(result.data);

            // 比較テーブルを表示
            renderComparisonTable(result.data);

            // 保存ボタンを表示
            document.getElementById('saveScenarioBtn').style.display = 'inline-block';

            showLoading(false);
        } else {
            alert('シナリオ比較に失敗しました: ' + result.error);
            showLoading(false);
        }
    } catch (error) {
        console.error('シナリオ比較エラー:', error);
        alert('シナリオ比較に失敗しました');
        showLoading(false);
    }
}

// ========== シナリオ管理機能（データベース版） ==========
async function saveScenario() {
    if (!currentScenarioResults) {
        alert('保存するシナリオがありません');
        return;
    }

    try {
        // データベースに保存
        const result = await eel.save_scenario_to_db(
            currentScenarioResults.name,
            currentScenarioResults.settings,
            currentScenarioResults.data
        )();

        if (result.success) {
            alert('シナリオをデータベースに保存しました');
            // 保存済みシナリオリストを更新
            renderSavedScenarios();
        } else {
            alert('保存に失敗しました: ' + result.error);
        }
    } catch (error) {
        console.error('シナリオ保存エラー:', error);
        alert('保存に失敗しました');
    }
}

async function loadSavedScenarios() {
    try {
        const result = await eel.list_saved_scenarios()();
        if (result.success) {
            return result.data;
        }
        return [];
    } catch (error) {
        console.error('シナリオリスト取得エラー:', error);
        return [];
    }
}

async function renderSavedScenarios() {
    const scenarios = await loadSavedScenarios();
    const section = document.getElementById('savedScenariosSection');
    const list = document.getElementById('savedScenariosList');

    if (scenarios.length === 0) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    let html = '';

    scenarios.forEach((scenario, index) => {
        // 更新日時を表示
        const updatedDate = new Date(scenario.updated_at).toLocaleString('ja-JP');

        html += `
            <div class="saved-scenario-item">
                <div class="saved-scenario-header">
                    <span class="saved-scenario-name">${scenario.name}</span>
                    <div class="saved-scenario-actions">
                        <button class="btn btn-primary" onclick="loadScenarioFromDB('${scenario.name}')">表示</button>
                        <button class="btn btn-secondary" onclick="deleteScenarioFromDB('${scenario.name}')">削除</button>
                    </div>
                </div>
                <div class="saved-scenario-details">
                    更新日時: ${updatedDate}
                </div>
            </div>
        `;
    });

    list.innerHTML = html;
}

async function loadScenarioFromDB(name) {
    try {
        showLoading(true);
        const result = await eel.load_scenario_from_db(name)();

        if (result.success) {
            const scenario = result.data;

            // フォームに設定を反映
            document.getElementById('scenarioName').value = scenario.name;
            document.getElementById('scenarioReturn').value = scenario.settings.investment_return;
            document.getElementById('scenarioSpouse').value = scenario.settings.spouse_income;
            document.getElementById('scenarioSalary').value = scenario.settings.salary_growth;

            // 結果を表示
            currentScenarioResults = scenario;
            renderScenarioComparisonChart(scenario.data);
            renderComparisonTable(scenario.data);

            // 保存ボタンを表示
            document.getElementById('saveScenarioBtn').style.display = 'inline-block';

            // 画面をスクロール
            document.getElementById('scenarioComparisonChart').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert('シナリオの読み込みに失敗しました: ' + result.error);
        }
        showLoading(false);
    } catch (error) {
        console.error('シナリオ読み込みエラー:', error);
        alert('シナリオの読み込みに失敗しました');
        showLoading(false);
    }
}

async function deleteScenarioFromDB(name) {
    if (!confirm(`「${name}」をデータベースから削除しますか？`)) {
        return;
    }

    try {
        const result = await eel.delete_scenario_from_db(name)();

        if (result.success) {
            alert('シナリオを削除しました');
            renderSavedScenarios();
        } else {
            alert('削除に失敗しました: ' + result.error);
        }
    } catch (error) {
        console.error('シナリオ削除エラー:', error);
        alert('削除に失敗しました');
    }
}

function renderComparisonTable(scenarioData) {
    const table = document.getElementById('scenarioComparisonTable');
    const content = document.getElementById('comparisonTableContent');

    if (!scenarioData || scenarioData.length < 2) {
        table.style.display = 'none';
        return;
    }

    table.style.display = 'block';

    const baseline = scenarioData[0];
    const comparison = scenarioData[1];

    // 主要指標を比較
    const baselineYearly = baseline.yearly_data;
    const comparisonYearly = comparison.yearly_data;

    const baselineFinalAssets = baseline.final_assets;
    const comparisonFinalAssets = comparison.final_assets;
    const assetsDiff = comparisonFinalAssets - baselineFinalAssets;
    const assetsDiffPercent = ((assetsDiff / baselineFinalAssets) * 100).toFixed(1);

    // 累積キャッシュフローを計算
    const baselineCumulativeCF = baselineYearly.reduce((sum, y) => sum + y.cashflow_annual, 0);
    const comparisonCumulativeCF = comparisonYearly.reduce((sum, y) => sum + y.cashflow_annual, 0);
    const cfDiff = comparisonCumulativeCF - baselineCumulativeCF;
    const cfDiffPercent = ((cfDiff / Math.abs(baselineCumulativeCF)) * 100).toFixed(1);

    // 総投資額を計算
    const baselineTotalInvestment = baselineYearly.reduce((sum, y) => sum + y.investment_annual, 0);
    const comparisonTotalInvestment = comparisonYearly.reduce((sum, y) => sum + y.investment_annual, 0);
    const investmentDiff = comparisonTotalInvestment - baselineTotalInvestment;
    const investmentDiffPercent = ((investmentDiff / baselineTotalInvestment) * 100).toFixed(1);

    const html = `
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>指標</th>
                    <th>${baseline.scenario_name}</th>
                    <th>${comparison.scenario_name}</th>
                    <th>差分</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>最終資産額 (65歳時)</td>
                    <td>${formatCurrency(baselineFinalAssets)}</td>
                    <td>${formatCurrency(comparisonFinalAssets)}</td>
                    <td>
                        ${formatCurrency(assetsDiff)}
                        <span class="comparison-diff ${assetsDiff >= 0 ? 'positive' : 'negative'}">
                            ${assetsDiff >= 0 ? '+' : ''}${assetsDiffPercent}%
                        </span>
                    </td>
                </tr>
                <tr>
                    <td>累積キャッシュフロー</td>
                    <td>${formatCurrency(baselineCumulativeCF)}</td>
                    <td>${formatCurrency(comparisonCumulativeCF)}</td>
                    <td>
                        ${formatCurrency(cfDiff)}
                        <span class="comparison-diff ${cfDiff >= 0 ? 'positive' : 'negative'}">
                            ${cfDiff >= 0 ? '+' : ''}${cfDiffPercent}%
                        </span>
                    </td>
                </tr>
                <tr>
                    <td>総投資額</td>
                    <td>${formatCurrency(baselineTotalInvestment)}</td>
                    <td>${formatCurrency(comparisonTotalInvestment)}</td>
                    <td>
                        ${formatCurrency(investmentDiff)}
                        <span class="comparison-diff ${investmentDiff >= 0 ? 'positive' : 'negative'}">
                            ${investmentDiff >= 0 ? '+' : ''}${investmentDiffPercent}%
                        </span>
                    </td>
                </tr>
                <tr>
                    <td>現金残高 (最終年)</td>
                    <td>${formatCurrency(baselineYearly[baselineYearly.length - 1].cash)}</td>
                    <td>${formatCurrency(comparisonYearly[comparisonYearly.length - 1].cash)}</td>
                    <td>
                        ${formatCurrency(comparisonYearly[comparisonYearly.length - 1].cash - baselineYearly[baselineYearly.length - 1].cash)}
                    </td>
                </tr>
            </tbody>
        </table>
    `;

    content.innerHTML = html;
}

// ========== ユーティリティ関数 ==========
function formatCurrency(amount) {
    return new Intl.NumberFormat('ja-JP', {
        style: 'currency',
        currency: 'JPY',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = show ? 'block' : 'none';
    }
}

function getPlotlyTheme() {
    return isDarkMode ? {
        paper_bgcolor: '#1f2937',
        plot_bgcolor: '#1f2937',
        font: { color: '#f9fafb' },
        xaxis: { gridcolor: '#374151' },
        yaxis: { gridcolor: '#374151' }
    } : {
        paper_bgcolor: '#ffffff',
        plot_bgcolor: '#ffffff',
        font: { color: '#111827' },
        xaxis: { gridcolor: '#e5e7eb' },
        yaxis: { gridcolor: '#e5e7eb' }
    };
}

// ========== イベントリスト描画 ==========
function renderEventsList() {
    const container = document.getElementById('eventsList');
    if (!container) return;

    const events = [
        { age: 25, description: '入社' },
        { age: 28, description: '結婚' },
        { age: 30, description: '第一子誕生・猫飼育開始' },
        { age: 32, description: '第二子誕生' },
        { age: 37, description: 'つみたてNISA完了 (1,200万円)' },
        { age: 45, description: 'NISA満額達成 (1,800万円)' },
        { age: 48, description: '第一子大学入学' },
        { age: 50, description: '持ち家購入・第二子大学入学' },
        { age: 52, description: '第一子大学卒業' },
        { age: 54, description: '第二子大学卒業' },
        { age: 56, description: '子育て完了・資産形成最終期' },
        { age: 60, description: '役職定年' },
        { age: 65, description: '定年退職' }
    ];

    let html = '';
    events.forEach(event => {
        html += `
            <div class="event-item">
                <div class="event-age">${event.age}歳</div>
                <div class="event-description">${event.description}</div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// ========== 設定モーダル ==========
async function openSettingsModal() {
    try {
        const result = await eel.get_plan_data()();

        if (result.success) {
            const data = result.data;

            // 基本情報をinputフィールドに設定
            document.getElementById('settingStartAge').value = data.basic_info.start_age;
            document.getElementById('settingEndAge').value = data.basic_info.end_age;
            document.getElementById('settingMarriageAge').value = data.basic_info.marriage_age;
            document.getElementById('settingFirstChild').value = data.basic_info.first_child_birth_age;
            document.getElementById('settingSecondChild').value = data.basic_info.second_child_birth_age;
            document.getElementById('settingHomePurchase').value = data.life_events.home_purchase.age;

            // 配偶者収入をinputフィールドに設定
            document.getElementById('settingSpouseIncome1').value = data.spouse_income['28-47'];
            document.getElementById('settingSpouseIncome2').value = data.spouse_income['48-64'];
            document.getElementById('settingSpouseIncome3').value = data.spouse_income['65-99'];

            // 投資設定をinputフィールドに設定（パーセント表示）
            document.getElementById('settingNisaReturn').value =
                (data.investment_settings.nisa.expected_return * 100).toFixed(1);
            document.getElementById('settingTaxableReturn').value =
                (data.investment_settings.taxable_account.expected_return * 100).toFixed(1);
            document.getElementById('settingEducationReturn').value =
                (data.investment_settings.education_fund.expected_return * 100).toFixed(1);
            document.getElementById('settingInflationLiving').value =
                (data.inflation_settings.living_expenses_rate * 100).toFixed(1);
            document.getElementById('settingInflationEducation').value =
                (data.inflation_settings.education_rate * 100).toFixed(1);

            // モーダルを表示
            document.getElementById('settingsModal').style.display = 'block';
        } else {
            alert('設定の読み込みに失敗しました: ' + result.error);
        }
    } catch (error) {
        console.error('設定データ取得エラー:', error);
        alert('設定の読み込みに失敗しました');
    }
}

function closeSettingsModal() {
    document.getElementById('settingsModal').style.display = 'none';
}

async function saveAndRecalculate() {
    try {
        showLoading(true);

        // 現在のプランデータを取得
        const result = await eel.get_plan_data()();

        if (!result.success) {
            alert('設定の取得に失敗しました');
            showLoading(false);
            return;
        }

        const planData = result.data;

        // フォームから新しい値を取得して更新
        planData.basic_info.start_age = parseInt(document.getElementById('settingStartAge').value);
        planData.basic_info.end_age = parseInt(document.getElementById('settingEndAge').value);
        planData.basic_info.marriage_age = parseInt(document.getElementById('settingMarriageAge').value);
        planData.basic_info.first_child_birth_age = parseInt(document.getElementById('settingFirstChild').value);
        planData.basic_info.second_child_birth_age = parseInt(document.getElementById('settingSecondChild').value);
        planData.life_events.home_purchase.age = parseInt(document.getElementById('settingHomePurchase').value);

        // 配偶者収入を更新
        planData.spouse_income['28-47'] = parseInt(document.getElementById('settingSpouseIncome1').value);
        planData.spouse_income['48-64'] = parseInt(document.getElementById('settingSpouseIncome2').value);
        planData.spouse_income['65-99'] = parseInt(document.getElementById('settingSpouseIncome3').value);

        // 投資設定を更新（パーセントから小数に変換）
        planData.investment_settings.nisa.expected_return =
            parseFloat(document.getElementById('settingNisaReturn').value) / 100;
        planData.investment_settings.taxable_account.expected_return =
            parseFloat(document.getElementById('settingTaxableReturn').value) / 100;
        planData.investment_settings.education_fund.expected_return =
            parseFloat(document.getElementById('settingEducationReturn').value) / 100;
        planData.inflation_settings.living_expenses_rate =
            parseFloat(document.getElementById('settingInflationLiving').value) / 100;
        planData.inflation_settings.education_rate =
            parseFloat(document.getElementById('settingInflationEducation').value) / 100;

        // 設定を保存
        const updateResult = await eel.update_plan_data(planData)();

        if (updateResult.success) {
            // モーダルを閉じる
            closeSettingsModal();

            // シミュレーションを再実行
            await runSimulation();

            alert('設定を更新し、再計算しました');
        } else {
            alert('設定の保存に失敗しました: ' + updateResult.error);
            showLoading(false);
        }
    } catch (error) {
        console.error('設定保存エラー:', error);
        alert('設定の保存に失敗しました');
        showLoading(false);
    }
}

async function resetToDefault() {
    if (!confirm('設定を初期値に戻しますか？')) {
        return;
    }

    try {
        showLoading(true);

        const result = await eel.reset_plan_to_default()();

        if (result.success) {
            // モーダルを閉じる
            closeSettingsModal();

            // シミュレーションを再実行
            await runSimulation();

            alert('設定を初期値に戻しました');
        } else {
            alert('リセットに失敗しました: ' + result.error);
            showLoading(false);
        }
    } catch (error) {
        console.error('リセットエラー:', error);
        alert('リセットに失敗しました');
        showLoading(false);
    }
}

// モーダル外クリックで閉じる
window.onclick = function(event) {
    const modal = document.getElementById('settingsModal');
    if (event.target === modal) {
        closeSettingsModal();
    }
}

console.log('app.js ロード完了');
