/**
 * メインアプリケーションロジック
 * UIコントロールとデータ管理
 */

// グローバル状態
let simulationData = null;
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

    // 実績管理: 保存・更新ボタン
    const saveActualBtn = document.getElementById('saveActualBtn');
    if (saveActualBtn) {
        saveActualBtn.addEventListener('click', saveActualRecord);
    }
    const refreshActualBtn = document.getElementById('refreshActualBtn');
    if (refreshActualBtn) {
        refreshActualBtn.addEventListener('click', loadActualView);
    }

    // 今日の年月をデフォルト入力
    const now = new Date();
    const yearEl = document.getElementById('actualYear');
    const monthEl = document.getElementById('actualMonth');
    if (yearEl) yearEl.value = now.getFullYear();
    if (monthEl) monthEl.value = now.getMonth() + 1;
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
    } else if (viewName === 'actual') {
        // 実績管理ビューを読み込み
        loadActualView();
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

    list.innerHTML = '';

    irregularExpenses.forEach(expense => {
        const item = document.createElement('div');
        item.className = 'irregular-expense-item';

        const expenseHeader = document.createElement('div');
        expenseHeader.className = 'irregular-expense-header';

        const typeSpan = document.createElement('span');
        typeSpan.className = 'irregular-expense-type';
        typeSpan.textContent = expense.type;  // textContent でXSS回避

        const amountSpan = document.createElement('span');
        amountSpan.className = 'irregular-expense-amount';
        amountSpan.textContent = formatCurrency(expense.amount);

        expenseHeader.appendChild(typeSpan);
        expenseHeader.appendChild(amountSpan);

        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'irregular-expense-sources';

        const sourcesLabel = document.createElement('span');
        sourcesLabel.style.cssText = 'font-size: 0.9rem; color: var(--text-secondary);';
        sourcesLabel.textContent = '支払い元:';
        sourcesDiv.appendChild(sourcesLabel);

        expense.payment_sources.forEach(source => {
            const sourceDiv = document.createElement('div');
            sourceDiv.className = 'irregular-expense-source';

            const sourceNameSpan = document.createElement('span');
            sourceNameSpan.className = 'irregular-expense-source-name';
            sourceNameSpan.textContent = source.source;  // textContent でXSS回避

            const sourceAmountSpan = document.createElement('span');
            sourceAmountSpan.className = 'irregular-expense-source-amount';
            sourceAmountSpan.textContent = formatCurrency(source.amount);

            sourceDiv.appendChild(sourceNameSpan);
            sourceDiv.appendChild(sourceAmountSpan);
            sourcesDiv.appendChild(sourceDiv);
        });

        item.appendChild(expenseHeader);
        item.appendChild(sourcesDiv);
        list.appendChild(item);
    });
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
    // DOM要素を直接構築してXSSを回避（innerHTML ではなく textContent を使用）
    list.innerHTML = '';

    scenarios.forEach((scenario) => {
        const updatedDate = new Date(scenario.updated_at).toLocaleString('ja-JP');

        const item = document.createElement('div');
        item.className = 'saved-scenario-item';

        const header = document.createElement('div');
        header.className = 'saved-scenario-header';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'saved-scenario-name';
        nameSpan.textContent = scenario.name;  // textContent でXSS回避

        const actions = document.createElement('div');
        actions.className = 'saved-scenario-actions';

        const loadBtn = document.createElement('button');
        loadBtn.className = 'btn btn-primary';
        loadBtn.textContent = '表示';
        loadBtn.addEventListener('click', () => loadScenarioFromDB(scenario.name));

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-secondary';
        deleteBtn.textContent = '削除';
        deleteBtn.addEventListener('click', () => deleteScenarioFromDB(scenario.name));

        actions.appendChild(loadBtn);
        actions.appendChild(deleteBtn);
        header.appendChild(nameSpan);
        header.appendChild(actions);

        const details = document.createElement('div');
        details.className = 'saved-scenario-details';
        details.textContent = `更新日時: ${updatedDate}`;

        item.appendChild(header);
        item.appendChild(details);
        list.appendChild(item);
    });
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

/**
 * XSS対策: HTML特殊文字をエスケープ
 */
function escapeHTML(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

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

        // フォームから新しい値を取得
        const startAge = parseInt(document.getElementById('settingStartAge').value);
        const endAge = parseInt(document.getElementById('settingEndAge').value);
        const marriageAge = parseInt(document.getElementById('settingMarriageAge').value);
        const firstChild = parseInt(document.getElementById('settingFirstChild').value);
        const secondChild = parseInt(document.getElementById('settingSecondChild').value);
        const homePurchase = parseInt(document.getElementById('settingHomePurchase').value);

        // バリデーション: 年齢の整合性チェック
        if (isNaN(startAge) || isNaN(endAge) || startAge < 18 || endAge > 100 || startAge >= endAge) {
            alert('開始年齢・終了年齢が不正です（18〜100歳の範囲で、開始 < 終了にしてください）');
            showLoading(false);
            return;
        }
        if (isNaN(marriageAge) || marriageAge < startAge || marriageAge > endAge) {
            alert(`結婚年齢は ${startAge}〜${endAge} 歳の範囲で指定してください`);
            showLoading(false);
            return;
        }
        if (isNaN(firstChild) || firstChild < startAge || firstChild > endAge) {
            alert(`第一子誕生年齢は ${startAge}〜${endAge} 歳の範囲で指定してください`);
            showLoading(false);
            return;
        }
        if (isNaN(secondChild) || secondChild < startAge || secondChild > endAge || secondChild < firstChild) {
            alert(`第二子誕生年齢は第一子 (${firstChild}歳) 以降かつ ${endAge} 歳以下で指定してください`);
            showLoading(false);
            return;
        }
        if (isNaN(homePurchase) || homePurchase < startAge || homePurchase > endAge) {
            alert(`住宅購入年齢は ${startAge}〜${endAge} 歳の範囲で指定してください`);
            showLoading(false);
            return;
        }

        // バリデーション: 投資リターン (0〜50%)
        const nisaReturn = parseFloat(document.getElementById('settingNisaReturn').value);
        const taxableReturn = parseFloat(document.getElementById('settingTaxableReturn').value);
        const educationReturn = parseFloat(document.getElementById('settingEducationReturn').value);
        const inflationLiving = parseFloat(document.getElementById('settingInflationLiving').value);
        const inflationEducation = parseFloat(document.getElementById('settingInflationEducation').value);

        for (const [label, val] of [['NISAリターン', nisaReturn], ['特定口座リターン', taxableReturn], ['教育資金リターン', educationReturn]]) {
            if (isNaN(val) || val < 0 || val > 50) {
                alert(`${label}は 0〜50% の範囲で指定してください`);
                showLoading(false);
                return;
            }
        }
        for (const [label, val] of [['生活費インフレ率', inflationLiving], ['教育費インフレ率', inflationEducation]]) {
            if (isNaN(val) || val < 0 || val > 20) {
                alert(`${label}は 0〜20% の範囲で指定してください`);
                showLoading(false);
                return;
            }
        }

        // 検証済みの値を反映
        planData.basic_info.start_age = startAge;
        planData.basic_info.end_age = endAge;
        planData.basic_info.marriage_age = marriageAge;
        planData.basic_info.first_child_birth_age = firstChild;
        planData.basic_info.second_child_birth_age = secondChild;
        planData.life_events.home_purchase.age = homePurchase;

        // 配偶者収入を更新
        planData.spouse_income['28-47'] = parseInt(document.getElementById('settingSpouseIncome1').value) || 0;
        planData.spouse_income['48-64'] = parseInt(document.getElementById('settingSpouseIncome2').value) || 0;
        planData.spouse_income['65-99'] = parseInt(document.getElementById('settingSpouseIncome3').value) || 0;

        // 投資設定を更新（パーセントから小数に変換）
        planData.investment_settings.nisa.expected_return = nisaReturn / 100;
        planData.investment_settings.taxable_account.expected_return = taxableReturn / 100;
        planData.investment_settings.education_fund.expected_return = educationReturn / 100;
        planData.inflation_settings.living_expenses_rate = inflationLiving / 100;
        planData.inflation_settings.education_rate = inflationEducation / 100;

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

// ==================== 実績管理 ====================

/**
 * 実績管理ビューの読み込み（グラフ + 一覧テーブル）
 */
async function loadActualView() {
    try {
        showLoading(true);
        const [recordsResult, comparisonResult] = await Promise.all([
            eel.get_actual_records()(),
            eel.get_plan_vs_actual()()
        ]);
        showLoading(false);

        if (recordsResult.success) {
            renderActualRecordsTable(recordsResult.data);
        }

        if (comparisonResult.success) {
            renderActualComparisonCharts(comparisonResult.data);
            renderActualSummaryCards(comparisonResult.data);
        }
    } catch (err) {
        console.error('実績ビュー読み込みエラー:', err);
        showLoading(false);
    }
}

/**
 * 実績レコードを保存する
 */
async function saveActualRecord() {
    const year   = parseInt(document.getElementById('actualYear').value);
    const month  = parseInt(document.getElementById('actualMonth').value);
    const age    = parseInt(document.getElementById('actualAge').value);
    const income = parseInt(document.getElementById('actualIncome').value) || 0;
    const exp    = parseInt(document.getElementById('actualExpenses').value) || 0;
    const inv    = parseInt(document.getElementById('actualInvestment').value) || 0;
    const cash   = parseInt(document.getElementById('actualCashBalance').value) || 0;
    const notes  = document.getElementById('actualNotes').value || '';

    if (isNaN(year) || year < 2020 || year > 2070) {
        alert('年は2020〜2070の範囲で入力してください');
        return;
    }
    if (isNaN(month) || month < 1 || month > 12) {
        alert('月は1〜12で入力してください');
        return;
    }
    if (isNaN(age) || age < 18 || age > 80) {
        alert('年齢は18〜80歳で入力してください');
        return;
    }

    try {
        showLoading(true);
        const result = await eel.save_actual_record(year, month, age, income, exp, inv, cash, notes)();
        showLoading(false);

        if (result.success) {
            alert('実績データを保存しました');
            loadActualView();
        } else {
            alert('保存に失敗しました: ' + result.error);
        }
    } catch (err) {
        console.error('実績保存エラー:', err);
        showLoading(false);
        alert('保存中にエラーが発生しました');
    }
}

/**
 * 実績レコードを削除する
 */
async function deleteActualRecord(year, month) {
    if (!confirm(`${year}年${month}月の実績データを削除しますか？`)) return;

    try {
        showLoading(true);
        const result = await eel.delete_actual_record(year, month)();
        showLoading(false);

        if (result.success) {
            loadActualView();
        } else {
            alert('削除に失敗しました: ' + result.error);
        }
    } catch (err) {
        console.error('実績削除エラー:', err);
        showLoading(false);
    }
}

/**
 * 実績レコード一覧テーブルを描画
 */
function renderActualRecordsTable(records) {
    const container = document.getElementById('actualRecordsList');
    if (!container) return;

    if (!records || records.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">実績データがありません。上のフォームから入力してください。</p>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'actual-records-table';

    const thead = document.createElement('thead');
    thead.innerHTML = `<tr>
        <th>年月</th><th>年齢</th>
        <th>収入（実績）</th><th>支出（実績）</th>
        <th>投資（実績）</th><th>現金残高</th>
        <th>メモ</th><th>操作</th>
    </tr>`;
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    records.forEach(r => {
        const tr = document.createElement('tr');

        const yearMonthTd = document.createElement('td');
        yearMonthTd.textContent = `${r.year}年${r.month}月`;

        const ageTd = document.createElement('td');
        ageTd.textContent = `${r.age}歳`;

        const incomeTd = document.createElement('td');
        incomeTd.textContent = formatCurrency(r.income_actual);

        const expTd = document.createElement('td');
        expTd.textContent = formatCurrency(r.expenses_actual);

        const invTd = document.createElement('td');
        invTd.textContent = formatCurrency(r.investment_actual);

        const cashTd = document.createElement('td');
        cashTd.textContent = formatCurrency(r.cash_balance_actual);

        const notesTd = document.createElement('td');
        notesTd.textContent = r.notes || '';
        notesTd.style.maxWidth = '150px';
        notesTd.style.overflow = 'hidden';
        notesTd.style.textOverflow = 'ellipsis';
        notesTd.style.whiteSpace = 'nowrap';

        const actionTd = document.createElement('td');
        const delBtn = document.createElement('button');
        delBtn.className = 'btn btn-secondary btn-sm';
        delBtn.textContent = '削除';
        delBtn.addEventListener('click', () => deleteActualRecord(r.year, r.month));
        actionTd.appendChild(delBtn);

        tr.append(yearMonthTd, ageTd, incomeTd, expTd, invTd, cashTd, notesTd, actionTd);
        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.innerHTML = '';
    container.appendChild(table);
}

/**
 * サマリーカード（累計乖離）を描画
 */
function renderActualSummaryCards(comparisonData) {
    const cardsEl = document.getElementById('actualSummaryCards');
    if (!cardsEl) return;

    const entered = comparisonData.filter(d => d.months_entered > 0);
    if (entered.length === 0) { cardsEl.style.display = 'none'; return; }

    cardsEl.style.display = 'flex';

    // 12ヶ月入力済みの年のみ乖離計算
    const fullYears = comparisonData.filter(d => d.income_diff !== null);
    const totalIncomeDiff = fullYears.reduce((s, d) => s + (d.income_diff || 0), 0);
    const totalExpDiff    = fullYears.reduce((s, d) => s + (d.expenses_diff || 0), 0);
    const totalInvDiff    = fullYears.reduce((s, d) => s + (d.investment_diff || 0), 0);
    const totalMonths     = entered.reduce((s, d) => s + d.months_entered, 0);

    const setCard = (id, val, invertColor = false) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = (val >= 0 ? '+' : '') + formatCurrency(val);
        const positive = invertColor ? val <= 0 : val >= 0;
        el.className = 'amount ' + (positive ? 'text-green' : 'text-red');
    };

    document.getElementById('actualMonthsCount').textContent = `${totalMonths}ヶ月`;
    setCard('actualIncomeDiff', totalIncomeDiff);
    setCard('actualExpensesDiff', totalExpDiff, true);  // 支出は少ない方がgood
    setCard('actualInvestmentDiff', totalInvDiff);
}

console.log('app.js ロード完了');
