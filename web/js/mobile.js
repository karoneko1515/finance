/**
 * モバイルUX/UI制御
 * ボトムナビゲーション・ボトムシート・スワイプジェスチャー
 */

(function () {
    'use strict';

    // ===== 定数 =====
    const MOBILE_BREAKPOINT = 768;
    const SWIPE_THRESHOLD = 50;      // px: スワイプ判定距離
    const SWIPE_VELOCITY = 0.3;      // px/ms: スワイプ判定速度
    const SHEET_CLOSE_RATIO = 0.35;  // シート高さに対する閉じる判定比率

    // ボトムナビに表示する4ビュー（順序 = スワイプ順）
    const PRIMARY_VIEWS = ['dashboard', 'yearly-detail', 'cashflow', 'editor'];

    // ===== 状態 =====
    let currentViewIndex = 0;        // PRIMARY_VIEWS内の現在インデックス
    let sheetOpen = false;
    let sheetStartY = 0;
    let sheetCurrentY = 0;
    let sheetDragging = false;
    let swipeStartX = 0;
    let swipeStartY = 0;
    let swipeStartTime = 0;

    // ===== DOM参照 =====
    const bottomNav    = document.getElementById('mobileBottomNav');
    const moreBtn      = document.getElementById('mobileMoreBtn');
    const sheet        = document.getElementById('mobileBottomSheet');
    const overlay      = document.getElementById('mobileSheetOverlay');
    const navItems     = document.querySelectorAll('.mobile-nav-item[data-view]');
    const sheetItems   = document.querySelectorAll('.mobile-sheet-item[data-view]');

    // ===== ユーティリティ =====
    function isMobile() {
        return window.innerWidth <= MOBILE_BREAKPOINT;
    }

    function getCurrentViewName() {
        const activeView = document.querySelector('.view.active');
        return activeView ? activeView.id.replace('-view', '') : 'dashboard';
    }

    // ===== ボトムナビ アクティブ状態同期 =====
    // app.js の switchView() から呼ばれる（グローバル公開）
    function syncMobileNav(viewName) {
        // ボトムナビボタンのアクティブ状態
        navItems.forEach(item => {
            item.classList.toggle('active', item.dataset.view === viewName);
        });

        // ボトムシートアイテムのアクティブ状態
        sheetItems.forEach(item => {
            item.classList.toggle('active', item.dataset.view === viewName);
        });

        // PRIMARY_VIEWSのインデックス更新
        const idx = PRIMARY_VIEWS.indexOf(viewName);
        if (idx !== -1) currentViewIndex = idx;
    }

    // ===== ボトムシート =====
    function openSheet() {
        sheetOpen = true;
        sheet.classList.add('active');
        overlay.classList.add('active');
        moreBtn.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSheet() {
        sheetOpen = false;
        sheet.classList.remove('active');
        overlay.classList.remove('active');
        moreBtn.classList.remove('active');
        document.body.style.overflow = '';
        sheet.style.transform = '';
    }

    function toggleSheet() {
        sheetOpen ? closeSheet() : openSheet();
    }

    // シートのスワイプダウン閉じ
    function onSheetTouchStart(e) {
        const touch = e.touches[0];
        sheetStartY = touch.clientY;
        sheetCurrentY = touch.clientY;
        sheetDragging = true;
        sheet.style.transition = 'none';
    }

    function onSheetTouchMove(e) {
        if (!sheetDragging) return;
        const touch = e.touches[0];
        sheetCurrentY = touch.clientY;
        const delta = sheetCurrentY - sheetStartY;
        if (delta > 0) {
            sheet.style.transform = `translateY(${delta}px)`;
        }
    }

    function onSheetTouchEnd() {
        if (!sheetDragging) return;
        sheetDragging = false;
        sheet.style.transition = '';

        const delta = sheetCurrentY - sheetStartY;
        const sheetHeight = sheet.offsetHeight || 300;

        if (delta > sheetHeight * SHEET_CLOSE_RATIO) {
            closeSheet();
        } else {
            sheet.style.transform = '';
        }
    }

    // ===== スワイプナビゲーション（ビュー間） =====
    function onDocTouchStart(e) {
        // シートが開いている場合・入力要素上では無効
        if (sheetOpen) return;
        const tag = e.target.tagName;
        if (['INPUT', 'TEXTAREA', 'SELECT', 'RANGE'].includes(tag)) return;
        if (e.target.closest('.mobile-bottom-nav') || e.target.closest('.mobile-bottom-sheet')) return;

        swipeStartX = e.touches[0].clientX;
        swipeStartY = e.touches[0].clientY;
        swipeStartTime = Date.now();
    }

    function onDocTouchEnd(e) {
        if (sheetOpen) return;
        if (!swipeStartX) return;

        const dx = e.changedTouches[0].clientX - swipeStartX;
        const dy = e.changedTouches[0].clientY - swipeStartY;
        const dt = Date.now() - swipeStartTime;

        // 水平スワイプのみ（縦方向スクロールと区別）
        if (Math.abs(dx) < SWIPE_THRESHOLD) return;
        if (Math.abs(dy) > Math.abs(dx) * 0.7) return;
        if (Math.abs(dx) / dt < SWIPE_VELOCITY) return;

        // ボトムシートが開いている場合は無視（既にreturnしているが念のため）
        const currentView = getCurrentViewName();
        const idx = PRIMARY_VIEWS.indexOf(currentView);
        if (idx === -1) return; // セカンダリビューではスワイプナビしない

        if (dx < 0 && idx < PRIMARY_VIEWS.length - 1) {
            // 左スワイプ → 次のビュー
            if (typeof switchView === 'function') switchView(PRIMARY_VIEWS[idx + 1]);
        } else if (dx > 0 && idx > 0) {
            // 右スワイプ → 前のビュー
            if (typeof switchView === 'function') switchView(PRIMARY_VIEWS[idx - 1]);
        }

        swipeStartX = 0;
    }

    // ===== チャートのモバイルレイアウト調整 =====
    function relayoutChartsForMobile() {
        if (!window.Plotly) return;
        const plots = document.querySelectorAll('.js-plotly-plot');
        plots.forEach(plot => {
            try {
                const mobile = isMobile();
                Plotly.relayout(plot, {
                    'margin.l': mobile ? 40 : 60,
                    'margin.r': mobile ? 10 : 30,
                    'margin.t': mobile ? 30 : 50,
                    'margin.b': mobile ? 50 : 60,
                    'legend.orientation': mobile ? 'h' : 'v',
                    'legend.x': mobile ? 0 : 1.02,
                    'legend.y': mobile ? -0.25 : 1,
                    'legend.xanchor': mobile ? 'left' : 'left',
                    'legend.yanchor': mobile ? 'top' : 'top',
                    'font.size': mobile ? 10 : 12,
                });
            } catch (e) {
                // Plotly未初期化チャートは無視
            }
        });
    }

    // ビューが切り替わった時にアクティブビュー内チャートを調整
    function relayoutActiveViewCharts() {
        if (!window.Plotly) return;
        const activeView = document.querySelector('.view.active');
        if (!activeView) return;
        activeView.querySelectorAll('.js-plotly-plot').forEach(plot => {
            try {
                Plotly.Plots.resize(plot);
            } catch (e) { /* 無視 */ }
        });
    }

    // MutationObserver: チャートが追加されたらモバイル調整
    let chartObserver = null;
    function setupChartObserver() {
        if (chartObserver) chartObserver.disconnect();
        chartObserver = new MutationObserver((mutations) => {
            if (!isMobile()) return;
            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === 1) {
                        const plots = node.classList && node.classList.contains('js-plotly-plot')
                            ? [node]
                            : node.querySelectorAll('.js-plotly-plot');
                        plots.forEach(plot => {
                            try { Plotly.Plots.resize(plot); } catch (e) { /* 無視 */ }
                        });
                    }
                }
            }
        });
        chartObserver.observe(document.body, { childList: true, subtree: true });
    }

    // ===== リサイズハンドラー =====
    let resizeTimer = null;
    function onResize() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (isMobile()) {
                syncMobileNav(getCurrentViewName());
            } else {
                // PC表示に戻った時はシートを閉じる
                if (sheetOpen) closeSheet();
            }
            relayoutActiveViewCharts();
        }, 200);
    }

    // ===== イベント登録 =====
    function init() {
        // ボトムナビ各ボタン
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                if (typeof switchView === 'function') {
                    switchView(item.dataset.view);
                }
            });
        });

        // その他ボタン
        if (moreBtn) {
            moreBtn.addEventListener('click', toggleSheet);
        }

        // ボトムシートアイテム
        sheetItems.forEach(item => {
            item.addEventListener('click', () => {
                const view = item.dataset.view;
                closeSheet();
                if (typeof switchView === 'function') {
                    switchView(view);
                }
            });
        });

        // オーバーレイタップでシートを閉じる
        if (overlay) {
            overlay.addEventListener('click', closeSheet);
        }

        // シートのスワイプダウン
        if (sheet) {
            sheet.addEventListener('touchstart', onSheetTouchStart, { passive: true });
            sheet.addEventListener('touchmove', onSheetTouchMove, { passive: true });
            sheet.addEventListener('touchend', onSheetTouchEnd);
        }

        // ドキュメント全体のスワイプナビゲーション
        document.addEventListener('touchstart', onDocTouchStart, { passive: true });
        document.addEventListener('touchend', onDocTouchEnd, { passive: true });

        // リサイズ
        window.addEventListener('resize', onResize);

        // チャートMutationObserver
        setupChartObserver();

        // 初期アクティブ状態を同期
        syncMobileNav(getCurrentViewName());
    }

    // ===== グローバル公開 =====
    // app.js の switchView() から呼ばれるためwindowに登録
    window.syncMobileNav = syncMobileNav;
    window.relayoutChartsForMobile = relayoutChartsForMobile;

    // DOM準備後に初期化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
