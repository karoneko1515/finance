/**
 * メインアプリケーションロジック
 * UIコントロールとデータ管理
 */

// グローバル状態
let simulationData = null;
let mcResults = { plan: null, actual: null }; // モンテカルロ結果
let currentAge = 25;
let isDarkMode = false;
let currentScenarioResults = null; // 現在のシナリオ比較結果
let baselineData = null; // 初期値（ベースライン）データ
let ageUpdateTimer = null; // 年齢更新のデバウンスタイマー
let lastRenderedAge = null; // 最後に描画した年齢（重複描画防止）
let salaryTableData = []; // データ編集タブ用給与テーブルキャッシュ

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

    // 設定ボタン → エディタの設定タブに遷移
    document.getElementById('settingsBtn').addEventListener('click', () => {
        switchView('editor');
        switchEditorTab('settings');
    });

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
    const ageEl  = document.getElementById('actualAge');
    if (yearEl) yearEl.value = now.getFullYear();
    if (monthEl) monthEl.value = now.getMonth() + 1;

    // 年変更時に年齢を自動補完
    const autoFillAge = async () => {
        if (!yearEl || !ageEl) return;
        const y = parseInt(yearEl.value);
        if (isNaN(y) || y < 2020 || y > 2070) return;
        try {
            const res = await eel.get_age_for_year(y)();
            if (res.success) {
                ageEl.value = res.age;
                ageEl.style.borderColor = res.is_exact ? '' : 'var(--accent-color)';
                ageEl.title = res.is_exact ? '' : '実績データから正確な年齢を計算できないため推定値です';
            }
        } catch (_) {}
    };
    if (yearEl) {
        yearEl.addEventListener('change', autoFillAge);
        // 初回も自動補完を試みる
        autoFillAge();
    }

    // 実績ベース予測ボタン (Feature 1)
    const runPredictBtn = document.getElementById('runActualPredictBtn');
    if (runPredictBtn) runPredictBtn.addEventListener('click', runActualBasedPrediction);

    // ゴールゲージ更新ボタン (Feature 4)
    const refreshGoalBtn = document.getElementById('refreshGoalBtn');
    if (refreshGoalBtn) refreshGoalBtn.addEventListener('click', loadGoalGauges);

    // データ編集タブ切り替え
    document.querySelectorAll('.editor-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            switchEditorTab(e.currentTarget.dataset.editor);
        });
    });

    // 設定タブ: 保存・リセットボタン
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    if (saveSettingsBtn) saveSettingsBtn.addEventListener('click', saveSettingsFromEditor);
    const resetSettingsBtn = document.getElementById('resetSettingsBtn');
    if (resetSettingsBtn) resetSettingsBtn.addEventListener('click', resetSettingsToDefault);
    const addSpouseRangeBtn = document.getElementById('addSpouseRangeBtn');
    if (addSpouseRangeBtn) addSpouseRangeBtn.addEventListener('click', addSpouseRangeRow);

    // 給与範囲一括適用ボタン
    const applyRangeSalaryBtn = document.getElementById('applyRangeSalaryBtn');
    if (applyRangeSalaryBtn) applyRangeSalaryBtn.addEventListener('click', applyRangeSalary);

    // カスタムイベント追加ボタン
    const addCustomEventBtn = document.getElementById('addCustomEventBtn');
    if (addCustomEventBtn) addCustomEventBtn.addEventListener('click', addCustomEvent);

    // 老後の使用可能額 - 利回り変更時に再計算
    const retirementRate = document.getElementById('retirementReturnRate');
    if (retirementRate) retirementRate.addEventListener('change', loadRetirementIncomeAnalysis);

    // モンテカルロ
    const mcRunPlan   = document.getElementById('mcRunPlanBtn');
    const mcRunActual = document.getElementById('mcRunActualBtn');
    const mcClear     = document.getElementById('mcClearBtn');
    if (mcRunPlan)   mcRunPlan.addEventListener('click',   () => runMonteCarlo('plan'));
    if (mcRunActual) mcRunActual.addEventListener('click', () => runMonteCarlo('actual'));
    if (mcClear)     mcClear.addEventListener('click',    clearMonteCarloResults);
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
    } else if (viewName === 'editor') {
        // データ編集ビューを読み込み
        loadEditorView();
    } else if (viewName === 'montecarlo') {
        // モンテカルロビューを表示（既存結果があれば再描画）
        renderMonteCarloView();
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
    showProgress('シミュレーション計算中', '40年分のキャッシュフローを計算しています...', 3000);

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
            loadRetirementIncomeAnalysis();

            hideProgress();
        } else {
            console.error('シミュレーションエラー:', result.error);
            hideProgress();
            showToast('シミュレーションに失敗しました: ' + result.error);
        }
    } catch (error) {
        console.error('通信エラー:', error);
        hideProgress();
        showToast('サーバーとの通信に失敗しました');
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
    showProgress('シナリオ比較計算中', '複数シナリオのシミュレーションを実行しています...', 4000);

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

            hideProgress();
        } else {
            hideProgress();
            showToast('シナリオ比較に失敗しました: ' + result.error);
        }
    } catch (error) {
        console.error('シナリオ比較エラー:', error);
        hideProgress();
        showToast('シナリオ比較に失敗しました');
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

    const safePercent = (diff, base) => {
        if (!base || base === 0 || !isFinite(base)) return '0.0';
        const p = ((diff / base) * 100).toFixed(1);
        return isFinite(parseFloat(p)) ? p : '0.0';
    };

    const baselineFinalAssets = baseline.final_assets || 0;
    const comparisonFinalAssets = comparison.final_assets || 0;
    const assetsDiff = comparisonFinalAssets - baselineFinalAssets;
    const assetsDiffPercent = safePercent(assetsDiff, baselineFinalAssets);

    // 累積キャッシュフローを計算
    const baselineCumulativeCF = baselineYearly.reduce((sum, y) => sum + (y.cashflow_annual || 0), 0);
    const comparisonCumulativeCF = comparisonYearly.reduce((sum, y) => sum + (y.cashflow_annual || 0), 0);
    const cfDiff = comparisonCumulativeCF - baselineCumulativeCF;
    const cfDiffPercent = safePercent(cfDiff, Math.abs(baselineCumulativeCF));

    // 総投資額を計算
    const baselineTotalInvestment = baselineYearly.reduce((sum, y) => sum + (y.investment_total || 0), 0);
    const comparisonTotalInvestment = comparisonYearly.reduce((sum, y) => sum + (y.investment_total || 0), 0);
    const investmentDiff = comparisonTotalInvestment - baselineTotalInvestment;
    const investmentDiffPercent = safePercent(investmentDiff, baselineTotalInvestment);

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

// ========== 進捗オーバーレイ ==========
let _progressTimer = null;
let _progressValue = 0;

function showProgress(title, message, estimatedMs = 3000) {
    const overlay = document.getElementById('progressOverlay');
    const titleEl = document.getElementById('progressTitle');
    const msgEl   = document.getElementById('progressMessage');
    const fill    = document.getElementById('progressBarFill');
    const pct     = document.getElementById('progressPercent');

    if (!overlay) return;
    titleEl.textContent = title;
    msgEl.textContent   = message;

    // バー初期化
    fill.style.transition = 'none';
    fill.style.width = '0%';
    if (pct) pct.textContent = '0%';
    _progressValue = 0;

    overlay.classList.add('active');

    // タイマーで疑似進捗を更新（1%ずつ、estimatedMsを90%到達時間とする）
    if (_progressTimer) clearInterval(_progressTimer);
    const intervalMs = estimatedMs / 90;
    _progressTimer = setInterval(() => {
        if (_progressValue < 89) {
            _progressValue += 1;
            fill.style.transition = 'width 0.3s ease';
            fill.style.width = _progressValue + '%';
            if (pct) pct.textContent = _progressValue + '%';
        }
    }, intervalMs);
}

function hideProgress() {
    if (_progressTimer) { clearInterval(_progressTimer); _progressTimer = null; }
    const overlay = document.getElementById('progressOverlay');
    const fill    = document.getElementById('progressBarFill');
    const pct     = document.getElementById('progressPercent');
    if (!overlay) return;

    // 100%に完成させてからフェードアウト
    fill.style.transition = 'width 0.25s ease';
    fill.style.width = '100%';
    if (pct) pct.textContent = '100%';

    setTimeout(() => {
        overlay.classList.remove('active');
        fill.style.transition = 'none';
        fill.style.width = '0%';
        if (pct) pct.textContent = '0%';
    }, 350);
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

// ========== エディタタブ切り替え ==========
function switchEditorTab(target) {
    document.querySelectorAll('.editor-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.editor-panel').forEach(p => p.classList.remove('active'));
    const btn = document.querySelector(`.editor-tab[data-editor="${target}"]`);
    if (btn) btn.classList.add('active');
    const panel = document.getElementById(`editor-${target}`);
    if (panel) panel.classList.add('active');
    if (target === 'settings') loadSettingsEditor();
}

// ========== 設定エディタ ==========
async function loadSettingsEditor() {
    try {
        const result = await eel.get_plan_data()();
        if (!result.success) { showToast('設定の読み込みに失敗しました'); return; }
        const data = result.data;

        // 基本設定
        document.getElementById('cfgStartAge').value    = data.basic_info.start_age;
        document.getElementById('cfgEndAge').value      = data.basic_info.end_age;
        document.getElementById('cfgMarriageAge').value = data.basic_info.marriage_age;
        document.getElementById('cfgFirstChild').value  = data.basic_info.first_child_birth_age;
        document.getElementById('cfgSecondChild').value = data.basic_info.second_child_birth_age;
        document.getElementById('cfgHomePurchase').value = data.life_events.home_purchase.age;

        // 配偶者収入テーブル
        renderSpouseRangeTable(data.spouse_income);

        // 投資設定
        document.getElementById('cfgNisaReturn').value =
            (data.investment_settings.nisa.expected_return * 100).toFixed(1);
        document.getElementById('cfgTaxableReturn').value =
            (data.investment_settings.taxable_account.expected_return * 100).toFixed(1);
        document.getElementById('cfgEducationReturn').value =
            (data.investment_settings.education_fund.expected_return * 100).toFixed(1);
        document.getElementById('cfgInflationLiving').value =
            (data.inflation_settings.living_expenses_rate * 100).toFixed(1);
        document.getElementById('cfgInflationEducation').value =
            (data.inflation_settings.education_rate * 100).toFixed(1);
        document.getElementById('cfgIncentiveRate').value =
            Math.round(data.investment_settings.company_stock.incentive_rate * 100);
    } catch (err) {
        console.error('設定読み込みエラー:', err);
        showToast('設定の読み込みに失敗しました');
    }
}

// 配偶者収入テーブルの描画
function renderSpouseRangeTable(spouseIncome) {
    const tbody = document.getElementById('spouseRangeBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    // {"28-47": 80000, ...} → [{from, to, amount}] に変換
    const rows = Object.entries(spouseIncome)
        .map(([key, amount]) => {
            const [from, to] = key.split('-').map(Number);
            return { from, to, amount };
        })
        .sort((a, b) => a.from - b.from);

    rows.forEach(row => tbody.appendChild(createSpouseRangeRow(row.from, row.to, row.amount)));
}

function createSpouseRangeRow(from = '', to = '', amount = 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="number" class="spouse-range-input" placeholder="例: 28" value="${from}" min="18" max="99"></td>
        <td style="color:var(--text-secondary);">〜</td>
        <td><input type="number" class="spouse-range-input" placeholder="例: 47" value="${to}" min="18" max="99"></td>
        <td><input type="number" class="spouse-range-input spouse-monthly-input" placeholder="月額（円）" value="${amount}" min="0" step="10000"></td>
        <td><button class="btn-spouse-del">削除</button></td>
    `;
    tr.querySelector('.btn-spouse-del').addEventListener('click', () => tr.remove());
    return tr;
}

function addSpouseRangeRow() {
    const tbody = document.getElementById('spouseRangeBody');
    if (!tbody) return;
    tbody.appendChild(createSpouseRangeRow());
}

function collectSpouseRangeData() {
    const tbody = document.getElementById('spouseRangeBody');
    if (!tbody) return {};
    const result = {};
    tbody.querySelectorAll('tr').forEach(tr => {
        const inputs = tr.querySelectorAll('input');
        if (inputs.length < 3) return;
        const from   = parseInt(inputs[0].value);
        const to     = parseInt(inputs[1].value);
        const amount = parseInt(inputs[2].value) || 0;
        if (!isNaN(from) && !isNaN(to) && from <= to) {
            result[`${from}-${to}`] = amount;
        }
    });
    return result;
}

async function saveSettingsFromEditor() {
    try {
        const result = await eel.get_plan_data()();
        if (!result.success) { showToast('設定の取得に失敗しました'); return; }
        const planData = result.data;

        const startAge    = parseInt(document.getElementById('cfgStartAge').value);
        const endAge      = parseInt(document.getElementById('cfgEndAge').value);
        const marriageAge = parseInt(document.getElementById('cfgMarriageAge').value);
        const firstChild  = parseInt(document.getElementById('cfgFirstChild').value);
        const secondChild = parseInt(document.getElementById('cfgSecondChild').value);
        const homePurchase = parseInt(document.getElementById('cfgHomePurchase').value);

        if (isNaN(startAge) || isNaN(endAge) || startAge < 18 || endAge > 100 || startAge >= endAge) {
            showToast('開始年齢・終了年齢が不正です');
            return;
        }

        const nisaReturn        = parseFloat(document.getElementById('cfgNisaReturn').value);
        const taxableReturn     = parseFloat(document.getElementById('cfgTaxableReturn').value);
        const educationReturn   = parseFloat(document.getElementById('cfgEducationReturn').value);
        const inflationLiving   = parseFloat(document.getElementById('cfgInflationLiving').value);
        const inflationEducation = parseFloat(document.getElementById('cfgInflationEducation').value);
        const incentiveRate     = parseFloat(document.getElementById('cfgIncentiveRate').value);

        planData.basic_info.start_age = startAge;
        planData.basic_info.end_age   = endAge;
        planData.basic_info.marriage_age = marriageAge;
        planData.basic_info.first_child_birth_age  = firstChild;
        planData.basic_info.second_child_birth_age = secondChild;
        planData.life_events.home_purchase.age     = homePurchase;

        // 配偶者収入（テーブルから収集）
        planData.spouse_income = collectSpouseRangeData();

        planData.investment_settings.nisa.expected_return = nisaReturn / 100;
        planData.investment_settings.taxable_account.expected_return = taxableReturn / 100;
        planData.investment_settings.education_fund.expected_return  = educationReturn / 100;
        planData.inflation_settings.living_expenses_rate  = inflationLiving / 100;
        planData.inflation_settings.education_rate        = inflationEducation / 100;
        planData.investment_settings.company_stock.incentive_rate = incentiveRate / 100;

        const updateResult = await eel.update_plan_data(planData)();
        if (updateResult.success) {
            await runSimulation();
            showToast('設定を保存して再計算しました ✓');
        } else {
            showToast('設定の保存に失敗しました');
        }
    } catch (err) {
        console.error('設定保存エラー:', err);
        showToast('設定の保存に失敗しました');
    }
}

async function resetSettingsToDefault() {
    if (!confirm('設定を初期値に戻しますか？')) return;
    try {
        const result = await eel.reset_plan_to_default()();
        if (result.success) {
            await loadSettingsEditor();
            await runSimulation();
            showToast('設定を初期値に戻しました ✓');
        } else {
            showToast('リセットに失敗しました');
        }
    } catch (err) {
        console.error('リセットエラー:', err);
        showToast('リセットに失敗しました');
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

        const hasRecords = recordsResult.success && recordsResult.data.length > 0;

        if (recordsResult.success) {
            renderActualRecordsTable(recordsResult.data);
        }

        // 比較グラフ・サマリーカード：実績がある場合のみ表示
        const chartSections = document.querySelectorAll(
            '#actualSummaryCards, .chart-container:has(#actualIncomeChart), ' +
            '.chart-container:has(#actualExpensesChart), .chart-container:has(#actualInvestmentChart)'
        );
        if (hasRecords && comparisonResult.success) {
            chartSections.forEach(el => el.style.display = '');
            renderActualComparisonCharts(comparisonResult.data);
            renderActualSummaryCards(comparisonResult.data);
        } else {
            chartSections.forEach(el => el.style.display = 'none');
        }

        // ゴール達成率ゲージ・予測は常にロード（計画ベースでも表示）
        loadGoalGauges();

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
            showToast('実績データを保存しました');
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

// ==================== Feature 1: 実績ベース将来予測 ====================

async function runActualBasedPrediction() {
    try {
        showLoading(true);
        const result = await eel.run_simulation_from_actual()();
        showLoading(false);

        const infoBar = document.getElementById('actualPredictInfo');
        const chartEl = document.getElementById('actualPredictChart');
        if (!result.success) {
            alert(result.error);
            return;
        }

        const diffSign = result.cash_diff >= 0 ? '+' : '';
        infoBar.style.display = 'flex';
        infoBar.innerHTML = '';

        const makeChip = (label, val, positive) => {
            const chip = document.createElement('span');
            chip.className = `predict-chip ${positive ? 'chip-green' : 'chip-red'}`;
            chip.textContent = `${label}: ${val}`;
            return chip;
        };
        infoBar.appendChild(makeChip('基準年齢', `${result.from_age}歳`, true));
        infoBar.appendChild(makeChip('計画現金', formatCurrency(result.plan_cash), true));
        infoBar.appendChild(makeChip('実績現金', formatCurrency(result.actual_cash), result.cash_diff >= 0));
        infoBar.appendChild(makeChip('乖離額', `${diffSign}${formatCurrency(result.cash_diff)}`, result.cash_diff >= 0));

        // グラフ描画
        renderActualPredictionChart(result.data, result.from_age, chartEl.id);
    } catch (err) {
        showLoading(false);
        console.error('実績ベース予測エラー:', err);
        alert('予測の実行に失敗しました');
    }
}

// ==================== Feature 4: ゴール達成率ゲージ ====================

async function loadGoalGauges() {
    try {
        const result = await eel.get_goal_achievement()();
        if (!result.success) return;

        const grid = document.getElementById('goalGaugesGrid');
        const section = document.getElementById('goalGaugeSection');
        if (!grid || !section) return;
        section.style.display = 'block';
        grid.innerHTML = '';

        // ヘッダーに「計画ベース / 実績ベース」バッジと現在年齢を反映
        const header = section.querySelector('.goal-gauge-header h3');
        if (header) {
            const badge = document.createElement('span');
            badge.className = result.has_actual
                ? 'goal-source-badge badge-actual'
                : 'goal-source-badge badge-plan';
            badge.textContent = result.has_actual
                ? `実績ベース (${result.current_age}歳時点)`
                : `計画ベース (${result.current_age}歳時点・推定)`;
            // 既存バッジがあれば置き換え
            const existing = section.querySelector('.goal-source-badge');
            if (existing) existing.remove();
            header.after(badge);
        }

        const goals = result.data;
        Object.values(goals).forEach(g => {
            const gauge = document.createElement('div');
            gauge.className = 'goal-gauge-item';

            const rate = Math.min(100, Math.max(0, g.rate));
            const color = rate >= 100 ? '#10b981' : rate >= 70 ? '#f59e0b' : '#ef4444';

            // ソースバッジ: 実績/計画
            const sourceBadge = (g.source === 'actual')
                ? '<span class="gauge-src-badge gauge-src-actual">実績</span>'
                : '<span class="gauge-src-badge gauge-src-plan">計画</span>';

            gauge.innerHTML = `
                <div class="goal-gauge-label-row">
                    <span class="goal-gauge-label">${escapeHTML(g.label)}</span>
                    ${sourceBadge}
                </div>
                <div class="goal-gauge-bar-wrap">
                    <div class="goal-gauge-bar" style="width:0%; background:${color};"
                         data-target="${rate}"></div>
                </div>
                <div class="goal-gauge-values">
                    <span class="goal-current">${formatCurrency(g.current)}</span>
                    <span class="goal-rate" style="color:${color};">${rate}%</span>
                    <span class="goal-target">/ ${formatCurrency(g.target)}</span>
                </div>
            `;
            grid.appendChild(gauge);
        });

        // バーをアニメーション表示（requestAnimationFrame で DOM 確定後に実行）
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                grid.querySelectorAll('.goal-gauge-bar').forEach(bar => {
                    bar.style.width = bar.dataset.target + '%';
                });
            });
        });
    } catch (err) {
        console.error('ゴールゲージ読み込みエラー:', err);
    }
}

// ==================== データ編集タブ ====================

async function loadEditorView() {
    await Promise.all([
        loadSalaryEditor(),
        loadEventsEditor(),
        loadExpensesEditor()
    ]);
    // アクティブタブが設定なら設定も読み込む
    const activeTab = document.querySelector('.editor-tab.active');
    if (activeTab && activeTab.dataset.editor === 'settings') {
        await loadSettingsEditor();
    }
}

// ───────────────────────────────────────
// 給与エディタ
// ───────────────────────────────────────

async function loadSalaryEditor() {
    try {
        const result = await eel.get_full_salary_table()();
        if (!result.success) return;
        salaryTableData = result.data;
        renderSalaryTable(salaryTableData);
        renderSalaryCurveChart(salaryTableData);
    } catch (err) {
        console.error('給与テーブル読み込みエラー:', err);
    }
}

function renderSalaryTable(data) {
    const tbody = document.getElementById('salaryTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    data.forEach((row, idx) => {
        const tr = document.createElement('tr');
        tr.dataset.age = row.age;

        const annualMan = Math.round(row.annual_income / 10000);
        tr.innerHTML = `
            <td class="salary-age-cell">${row.age}歳</td>
            <td class="salary-edit-cell" data-field="base_salary" data-idx="${idx}">${row.base_salary.toLocaleString()}</td>
            <td class="salary-edit-cell" data-field="bonus_months" data-idx="${idx}">${row.bonus_months}</td>
            <td class="salary-annual-cell">${annualMan}万円/年</td>
            <td>
                <button class="btn btn-sm btn-salary-edit" data-idx="${idx}">編集</button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    // インライン編集ボタン
    tbody.querySelectorAll('.btn-salary-edit').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const idx = parseInt(e.currentTarget.dataset.idx);
            openSalaryRowEdit(idx);
        });
    });
}

function openSalaryRowEdit(idx) {
    const row = salaryTableData[idx];
    const tbody = document.getElementById('salaryTableBody');
    if (!tbody) return;

    const tr = tbody.children[idx];
    if (!tr) return;

    // 編集行に変換
    tr.innerHTML = `
        <td class="salary-age-cell">${row.age}歳</td>
        <td><input type="number" class="settings-input salary-inline-input" id="editSalary_${idx}"
             value="${row.base_salary}" min="0" step="10000" style="width:130px;"></td>
        <td><input type="number" class="settings-input salary-inline-input" id="editBonus_${idx}"
             value="${row.bonus_months}" min="0" max="20" step="0.5" style="width:80px;"></td>
        <td class="salary-annual-cell" id="editAnnualPreview_${idx}">-</td>
        <td>
            <button class="btn btn-sm btn-primary" id="confirmSalaryEdit_${idx}">✔</button>
            <button class="btn btn-sm btn-secondary" id="cancelSalaryEdit_${idx}">✕</button>
        </td>
    `;

    const salaryInput = document.getElementById(`editSalary_${idx}`);
    const bonusInput  = document.getElementById(`editBonus_${idx}`);
    const preview     = document.getElementById(`editAnnualPreview_${idx}`);

    const updatePreview = () => {
        const s = parseInt(salaryInput.value) || 0;
        const b = parseFloat(bonusInput.value) || 0;
        preview.textContent = `${Math.round(s * (12 + b) / 10000)}万円/年`;
    };
    salaryInput.addEventListener('input', updatePreview);
    bonusInput.addEventListener('input', updatePreview);
    updatePreview();

    document.getElementById(`confirmSalaryEdit_${idx}`).addEventListener('click', async () => {
        const newSalary = parseInt(salaryInput.value);
        const newBonus  = parseFloat(bonusInput.value);
        if (isNaN(newSalary) || newSalary < 0) { alert('月給を正しく入力してください'); return; }
        if (isNaN(newBonus)  || newBonus < 0)  { alert('ボーナス倍数を正しく入力してください'); return; }

        showLoading(true);
        const res = await eel.update_single_age_salary(row.age, newSalary, newBonus)();
        showLoading(false);
        if (res.success) {
            salaryTableData[idx].base_salary  = newSalary;
            salaryTableData[idx].bonus_months = newBonus;
            salaryTableData[idx].annual_income = Math.round(newSalary * (12 + newBonus));
            renderSalaryTable(salaryTableData);
            renderSalaryCurveChart(salaryTableData);
            // ダッシュボードのデータも更新
            await refreshAfterEdit();
        } else {
            alert('保存に失敗しました');
        }
    });

    document.getElementById(`cancelSalaryEdit_${idx}`).addEventListener('click', () => {
        renderSalaryTable(salaryTableData);
    });

    salaryInput.focus();
}

async function applyRangeSalary() {
    const start      = parseInt(document.getElementById('salaryRangeStart').value);
    const end        = parseInt(document.getElementById('salaryRangeEnd').value);
    const amount     = parseFloat(document.getElementById('salaryRangeAmount').value);
    const bonus      = parseFloat(document.getElementById('salaryRangeBonus').value);
    const changeType = document.getElementById('salaryChangeType').value;

    if (isNaN(start) || isNaN(end) || start > end) {
        alert('開始年齢〜終了年齢を正しく入力してください（開始 ≤ 終了）');
        return;
    }
    if (isNaN(amount)) {
        alert('月給（または変化率）を入力してください');
        return;
    }

    showLoading(true);
    const res = await eel.update_salary_range(start, end, amount, bonus < 0 ? -1 : bonus, changeType)();
    showLoading(false);

    if (res.success) {
        await loadSalaryEditor();
        await refreshAfterEdit();
        // 成功トースト
        showToast(`${start}〜${end}歳の給与を更新しました`);
    } else {
        alert('更新に失敗しました: ' + res.error);
    }
}

// ───────────────────────────────────────
// ライフイベントエディタ
// ───────────────────────────────────────

async function loadEventsEditor() {
    try {
        const [planResult, customResult] = await Promise.all([
            eel.get_plan_data()(),
            eel.get_custom_events()()
        ]);
        if (planResult.success) renderPresetEvents(planResult.data);
        if (customResult.success) renderCustomEventsList(customResult.data);
    } catch (err) {
        console.error('イベントエディタ読み込みエラー:', err);
    }
}

function renderPresetEvents(planData) {
    const grid = document.getElementById('presetEventsGrid');
    if (!grid) return;
    grid.innerHTML = '';

    const events = [
        {
            key: 'marriage', label: '結婚',
            icon: '💒',
            fields: [
                { name: 'age',  label: '年齢', type: 'number', path: 'basic_info.marriage_age' },
                { name: 'cost', label: '費用（円）', type: 'number', path: 'life_events.marriage.cost' }
            ]
        },
        {
            key: 'home', label: '住宅購入',
            icon: '🏠',
            fields: [
                { name: 'age',          label: '購入年齢', type: 'number', path: 'life_events.home_purchase.age' },
                { name: 'down_payment', label: '頭金（円）', type: 'number', path: 'life_events.home_purchase.down_payment' },
                { name: 'loan_amount',  label: 'ローン額（円）', type: 'number', path: 'life_events.home_purchase.loan_amount' },
                { name: 'interest_rate',label: '金利（%）', type: 'number', path: 'life_events.home_purchase.interest_rate', multiplier: 100 },
                { name: 'loan_years',   label: '返済年数', type: 'number', path: 'life_events.home_purchase.loan_years' }
            ]
        }
    ];

    events.forEach(ev => {
        const card = document.createElement('div');
        card.className = 'preset-event-card';

        const fields = ev.fields.map(f => {
            const raw = getNestedValue(planData, f.path);
            const displayVal = f.multiplier ? Math.round(raw * f.multiplier * 10) / 10 : raw;
            return `<div class="settings-item">
                <label>${escapeHTML(f.label)}</label>
                <input type="${f.type}" class="settings-input preset-event-input"
                    data-path="${f.path}" data-multiplier="${f.multiplier || 1}"
                    value="${displayVal}">
            </div>`;
        }).join('');

        card.innerHTML = `
            <div class="preset-event-header">
                <span class="preset-event-icon">${ev.icon}</span>
                <h4>${escapeHTML(ev.label)}</h4>
                <button class="btn btn-sm btn-primary save-preset-event-btn" data-key="${ev.key}">保存</button>
            </div>
            <div class="preset-event-fields">${fields}</div>
        `;
        grid.appendChild(card);

        card.querySelector('.save-preset-event-btn').addEventListener('click', async () => {
            await savePresetEvent(card, planData);
        });
    });
}

function getNestedValue(obj, path) {
    return path.split('.').reduce((o, k) => (o && o[k] !== undefined ? o[k] : null), obj);
}

function setNestedValue(obj, path, val) {
    const keys = path.split('.');
    let cur = obj;
    for (let i = 0; i < keys.length - 1; i++) {
        if (!cur[keys[i]]) cur[keys[i]] = {};
        cur = cur[keys[i]];
    }
    cur[keys[keys.length - 1]] = val;
}

async function savePresetEvent(card, planData) {
    const inputs = card.querySelectorAll('.preset-event-input');
    inputs.forEach(inp => {
        const path = inp.dataset.path;
        const mult = parseFloat(inp.dataset.multiplier) || 1;
        const rawVal = parseFloat(inp.value);
        setNestedValue(planData, path, mult === 1 ? rawVal : rawVal / mult);
    });

    // marriage_age は basic_info にも反映
    const marriageAgeInput = card.querySelector('[data-path="basic_info.marriage_age"]');
    if (marriageAgeInput) {
        planData.basic_info.marriage_age = parseInt(marriageAgeInput.value);
        planData.life_events.marriage.age = parseInt(marriageAgeInput.value);
    }

    showLoading(true);
    const res = await eel.update_plan_data(planData)();
    showLoading(false);
    if (res.success) {
        await refreshAfterEdit();
        showToast('イベント設定を保存しました');
    } else {
        alert('保存に失敗しました');
    }
}

function renderCustomEventsList(events) {
    const container = document.getElementById('customEventsList');
    if (!container) return;

    if (!events || events.length === 0) {
        container.innerHTML = '<p style="color:var(--text-secondary);">カスタムイベントはありません</p>';
        return;
    }

    container.innerHTML = '';
    const table = document.createElement('table');
    table.className = 'actual-records-table';
    table.innerHTML = `<thead><tr>
        <th>イベント名</th><th>年齢</th><th>費用</th><th>メモ</th><th>操作</th>
    </tr></thead>`;
    const tbody = document.createElement('tbody');
    events.forEach(ev => {
        const tr = document.createElement('tr');
        const nameTd    = document.createElement('td'); nameTd.textContent = ev.name;
        const ageTd     = document.createElement('td'); ageTd.textContent = `${ev.age}歳`;
        const costTd    = document.createElement('td'); costTd.textContent = formatCurrency(ev.cost);
        const descTd    = document.createElement('td'); descTd.textContent = ev.description || '';
        const actionTd  = document.createElement('td');
        const delBtn    = document.createElement('button');
        delBtn.className = 'btn btn-secondary btn-sm';
        delBtn.textContent = '削除';
        delBtn.addEventListener('click', async () => {
            if (!confirm(`「${ev.name}」を削除しますか？`)) return;
            showLoading(true);
            const res = await eel.delete_custom_event(ev.id)();
            showLoading(false);
            if (res.success) {
                await loadEventsEditor();
                await refreshAfterEdit();
                showToast('カスタムイベントを削除しました');
            }
        });
        actionTd.appendChild(delBtn);
        tr.append(nameTd, ageTd, costTd, descTd, actionTd);
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    container.appendChild(table);
}

async function addCustomEvent() {
    const name = document.getElementById('customEventName').value.trim();
    const age  = parseInt(document.getElementById('customEventAge').value);
    const cost = parseInt(document.getElementById('customEventCost').value) || 0;
    const desc = document.getElementById('customEventDesc').value.trim();

    if (!name) { alert('イベント名を入力してください'); return; }
    if (isNaN(age) || age < 18 || age > 80) { alert('年齢を18〜80歳で入力してください'); return; }

    showLoading(true);
    const res = await eel.save_custom_event({ name, age, cost, description: desc })();
    showLoading(false);

    if (res.success) {
        document.getElementById('customEventName').value = '';
        document.getElementById('customEventAge').value  = '';
        document.getElementById('customEventCost').value = '';
        document.getElementById('customEventDesc').value = '';
        await loadEventsEditor();
        await refreshAfterEdit();
        showToast('カスタムイベントを追加しました');
    } else {
        alert('追加に失敗しました: ' + res.error);
    }
}

// ───────────────────────────────────────
// 生活費エディタ
// ───────────────────────────────────────

const EXPENSE_LABEL_MAP = {
    food: '食費', communication: '通信費', transportation: '交通費',
    daily_goods: '日用品', insurance: '保険', entertainment: '娯楽',
    daily_goods_children: '日用品(子育て)', childcare_lessons: '保育・習い事',
    pet: 'ペット費', clothing_medical: '衣服・医療',
    education_cram_school: '塾・教育費', spouse_allowance: '配偶者小遣い',
    basic_living: '基本生活費', leisure_travel: '余暇・旅行',
    child_preparation_fund: '子供準備資金'
};

async function loadExpensesEditor() {
    try {
        const result = await eel.get_plan_data()();
        if (!result.success) return;
        const phases = result.data.phase_definitions;
        renderPhaseExpensesAccordion(phases);
    } catch (err) {
        console.error('生活費エディタ読み込みエラー:', err);
    }
}

function renderPhaseExpensesAccordion(phases) {
    const container = document.getElementById('phaseExpensesAccordion');
    if (!container) return;
    container.innerHTML = '';

    Object.entries(phases).forEach(([phaseName, phase]) => {
        const expenses = phase.monthly_expenses || {};
        const total = Object.values(expenses).reduce((s, v) => s + v, 0);

        const card = document.createElement('div');
        card.className = 'phase-expense-card';

        const fieldRows = Object.entries(expenses).map(([key, val]) => {
            const label = EXPENSE_LABEL_MAP[key] || key;
            return `<div class="settings-item">
                <label>${escapeHTML(label)}</label>
                <input type="number" class="settings-input phase-expense-input"
                    data-key="${key}" value="${val}" min="0" step="1000">
            </div>`;
        }).join('');

        card.innerHTML = `
            <div class="phase-card-header" data-phase="${phaseName}">
                <div class="phase-card-title">
                    <span class="phase-card-name">${escapeHTML(phase.name)}</span>
                    <span class="phase-card-range">${escapeHTML(phase.ages)}歳</span>
                    <span class="phase-card-total">月計: ${Math.round(total/10000)}万円</span>
                </div>
                <div class="phase-card-actions">
                    <button class="btn btn-sm btn-primary save-phase-btn" data-phase="${phaseName}">保存</button>
                    <span class="phase-toggle-icon">▼</span>
                </div>
            </div>
            <div class="phase-card-body">
                <div class="phase-expense-fields">${fieldRows}</div>
            </div>
        `;
        container.appendChild(card);

        // アコーディオン開閉
        card.querySelector('.phase-card-header').addEventListener('click', (e) => {
            if (e.target.classList.contains('save-phase-btn')) return;
            card.classList.toggle('open');
        });

        // 合計プレビュー更新
        card.querySelectorAll('.phase-expense-input').forEach(inp => {
            inp.addEventListener('input', () => {
                const newTotal = Array.from(card.querySelectorAll('.phase-expense-input'))
                    .reduce((s, el) => s + (parseInt(el.value) || 0), 0);
                card.querySelector('.phase-card-total').textContent =
                    `月計: ${Math.round(newTotal / 10000)}万円`;
            });
        });

        // 保存ボタン
        card.querySelector('.save-phase-btn').addEventListener('click', async (e) => {
            e.stopPropagation();
            const inputs = card.querySelectorAll('.phase-expense-input');
            const newExpenses = {};
            inputs.forEach(inp => { newExpenses[inp.dataset.key] = parseInt(inp.value) || 0; });

            showLoading(true);
            const res = await eel.update_phase_expenses(phaseName, newExpenses)();
            showLoading(false);
            if (res.success) {
                await refreshAfterEdit();
                showToast(`${phase.name}の生活費を更新しました`);
            } else {
                alert('保存に失敗しました: ' + res.error);
            }
        });
    });
}

// ───────────────────────────────────────
// 共通ユーティリティ
// ───────────────────────────────────────

/** 編集後にシミュレーションデータを再取得してダッシュボードを更新 */
async function refreshAfterEdit() {
    showProgress('再計算中', 'データ変更を反映しています...', 2000);
    try {
        const result = await eel.run_simulation()();
        if (result.success) {
            simulationData = result.data;
            updateDashboard();
        }
        hideProgress();
    } catch (err) {
        hideProgress();
        console.error('refreshAfterEdit エラー:', err);
    }
}

/** トースト通知（軽量フィードバック） */
function showToast(message) {
    let toast = document.getElementById('appToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'appToast';
        toast.className = 'app-toast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
}

// ==================== 老後の使用可能額 ====================

async function loadRetirementIncomeAnalysis() {
    const rateEl = document.getElementById('retirementReturnRate');
    const rate   = rateEl ? parseFloat(rateEl.value) : 0.02;

    try {
        const result = await eel.get_retirement_income_analysis(rate)();
        if (!result || !result.success) return;
        renderRetirementIncomeSection(result.data);
    } catch (err) {
        console.warn('老後収支分析エラー:', err);
    }
}

function renderRetirementIncomeSection(d) {
    const baseRow = document.getElementById('retirementIncomeBase');
    if (baseRow) {
        const items = [
            { label: '65歳時 総資産',       value: formatCurrency(d.final_assets) },
            { label: '配当資産（元本維持）', value: formatCurrency(d.dividend_assets) },
            { label: '取り崩し資産',         value: formatCurrency(d.withdrawal_assets) },
            { label: '月額 配当収入（税後）',value: formatCurrency(d.monthly_dividend) },
            { label: '月額 公的年金',        value: formatCurrency(d.pension_monthly) },
        ];
        if (d.spouse_monthly > 0) {
            items.push({ label: '月額 配偶者収入', value: formatCurrency(d.spouse_monthly) });
        }
        items.push({ label: '固定収入合計（月）', value: formatCurrency(d.fixed_monthly) });
        items.push({ label: 'NISA等利回り', value: `${(d.post_return_rate * 100).toFixed(0)}%` });

        baseRow.innerHTML = items.map(it => `
            <div class="rb-item">
                <span class="rb-label">${escapeHTML(it.label)}</span>
                <span class="rb-value">${escapeHTML(it.value)}</span>
            </div>
        `).join('');
    }

    const tbody = document.getElementById('retirementIncomeRows');
    if (!tbody) return;

    tbody.innerHTML = d.scenarios.map(s => {
        const isStd = s.target_age === 90;
        return `<tr class="${isStd ? 'row-highlight' : ''}">
            <td>${s.target_age}歳${isStd ? ' ★' : ''}</td>
            <td>${s.n_years}年間</td>
            <td>${formatCurrency(s.monthly_withdrawal)}</td>
            <td>${formatCurrency(s.monthly_dividend)}</td>
            <td>${formatCurrency(s.monthly_pension + s.monthly_spouse)}</td>
            <td class="highlight-col">${formatCurrency(s.total_monthly)}</td>
            <td class="highlight-col">${formatCurrency(s.total_yearly)}</td>
        </tr>`;
    }).join('');
}

// ==================== モンテカルロ ====================

const MC_COLORS = {
    plan: {
        band95: 'rgba(59,130,246,0.10)',
        band75: 'rgba(59,130,246,0.22)',
        median: '#2563eb',
        mean:   '#93c5fd',
    },
    actual: {
        band95: 'rgba(16,185,129,0.10)',
        band75: 'rgba(16,185,129,0.22)',
        median: '#059669',
        mean:   '#6ee7b7',
    },
};

async function runMonteCarlo(baseType) {
    const n   = parseInt(document.getElementById('mcNSimulations').value);
    const std = parseFloat(document.getElementById('mcReturnStd').value);

    const label = baseType === 'actual' ? '実績ベース' : 'プラン通り';
    // 回数に応じた推定時間 (100回≒2s, 300回≒5s, 1000回≒15s)
    const estimatedMs = n <= 100 ? 2000 : n <= 300 ? 5000 : 15000;

    showProgress(
        `モンテカルロ計算中（${label}）`,
        `${n}回のシミュレーションを実行しています... しばらくお待ちください`,
        estimatedMs
    );
    document.getElementById('mcRunPlanBtn').disabled   = true;
    document.getElementById('mcRunActualBtn').disabled = true;

    try {
        const result = await eel.run_monte_carlo_simulation(n, std, baseType)();

        if (!result.success) {
            hideProgress();
            showToast('モンテカルロシミュレーション失敗: ' + result.error);
            return;
        }

        mcResults[baseType] = result.data;
        hideProgress();
        renderMonteCarloView();
    } catch (err) {
        console.error('モンテカルロエラー:', err);
        hideProgress();
        showToast('モンテカルロシミュレーション中にエラーが発生しました');
    } finally {
        document.getElementById('mcRunPlanBtn').disabled   = false;
        document.getElementById('mcRunActualBtn').disabled = false;
    }
}

function clearMonteCarloResults() {
    mcResults = { plan: null, actual: null };
    renderMonteCarloView();
}

function renderMonteCarloView() {
    const hasAny = mcResults.plan || mcResults.actual;
    document.getElementById('mcEmptyState').style.display    = hasAny ? 'none'  : 'block';
    document.getElementById('mcResultSection').style.display = hasAny ? 'block' : 'none';
    if (!hasAny) return;

    // 描画用データ配列を構築
    const chartData = [];
    if (mcResults.plan) {
        chartData.push({ label: 'プラン通り', color: MC_COLORS.plan,   data: mcResults.plan });
    }
    if (mcResults.actual) {
        chartData.push({ label: '実績ベース', color: MC_COLORS.actual, data: mcResults.actual });
    }

    // サマリーカード
    renderMCSummaryCards(chartData);

    // グラフ
    renderMonteCarloChart(chartData, 'mcChart');
    renderMCDistributionChart(chartData, 'mcDistributionChart');
}

function renderMCSummaryCards(chartData) {
    const grid = document.getElementById('mcSummaryCards');
    if (!grid) return;
    grid.innerHTML = '';

    chartData.forEach(({ label, color, data }) => {
        const badgeClass = label.includes('実績') ? 'mc-badge-actual' : 'mc-badge-plan';
        const items = [
            { title: '最悪ケース (p5)',  value: data.final_p5 },
            { title: '下位 (p25)',       value: data.final_p25 },
            { title: '中央値 (p50)',     value: data.final_p50 },
            { title: '上位 (p75)',       value: data.final_p75 },
            { title: '最良ケース (p95)', value: data.final_p95 },
            { title: '平均',             value: data.final_mean },
        ];
        items.forEach(({ title, value }) => {
            const card = document.createElement('div');
            card.className = 'mc-summary-card';
            card.innerHTML = `
                <div class="mc-card-badge ${badgeClass}">${escapeHTML(label)}</div>
                <div class="mc-card-label">${escapeHTML(title)}</div>
                <div class="mc-card-value">${formatCurrency(value)}</div>
            `;
            grid.appendChild(card);
        });
    });
}

console.log('app.js ロード完了');
