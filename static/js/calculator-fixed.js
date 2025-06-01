/**
 * MindTraderPro Calculator - Version corrigée
 */

// Variables globales
let priceCache = {};
let priceUpdateInterval;

// Fonction principale d'initialisation
document.addEventListener('DOMContentLoaded', function() {
    initializeCalculator();
});

function initializeCalculator() {
    // Event listeners
    const form = document.getElementById('calculatorForm');
    const pairSelect = document.getElementById('pairSymbol');
    
    if (form) {
        form.addEventListener('submit', handleCalculation);
    }
    
    if (pairSelect) {
        pairSelect.addEventListener('change', updateRealTimePrice);
        // Charger le prix initial si une paire est déjà sélectionnée
        if (pairSelect.value) {
            updateRealTimePrice();
        }
    }
    
    // Toggle pour Stop Loss et Take Profit
    setupPipsToggle('sl', 'stopLoss');
    setupPipsToggle('tp', 'takeProfit');
    
    // Auto-calcul en temps réel
    setupAutoCalculation();
}

function setupPipsToggle(prefix, fieldId) {
    const pipsBtn = document.getElementById(`${prefix}PipsBtn`);
    const priceBtn = document.getElementById(`${prefix}PriceBtn`);
    const pipsInput = document.getElementById(`${prefix}Pips`);
    const priceInput = document.getElementById(`${prefix}Price`);
    const description = document.getElementById(`${prefix}Description`);
    const entryPriceRow = document.getElementById('entryPriceRow');
    
    if (pipsBtn && priceBtn) {
        pipsBtn.addEventListener('click', () => {
            toggleMode(prefix, 'pips', pipsBtn, priceBtn, pipsInput, priceInput, description, entryPriceRow);
        });
        
        priceBtn.addEventListener('click', () => {
            toggleMode(prefix, 'price', pipsBtn, priceBtn, pipsInput, priceInput, description, entryPriceRow);
        });
    }
}

function toggleMode(prefix, mode, pipsBtn, priceBtn, pipsInput, priceInput, description, entryPriceRow) {
    if (mode === 'pips') {
        pipsBtn.classList.add('active');
        priceBtn.classList.remove('active');
        pipsInput.style.display = 'block';
        priceInput.style.display = 'none';
        description.textContent = prefix === 'sl' ? 
            'Distance en pips entre votre entrée et votre stop loss' :
            'Distance en pips entre votre entrée et votre take profit';
    } else {
        priceBtn.classList.add('active');
        pipsBtn.classList.remove('active');
        pipsInput.style.display = 'none';
        priceInput.style.display = 'block';
        description.textContent = prefix === 'sl' ? 
            'Prix exact de votre stop loss' :
            'Prix exact de votre take profit';
        
        // Afficher le champ prix d'entrée si nécessaire
        if (entryPriceRow) {
            entryPriceRow.style.display = 'block';
        }
    }
    
    // Vérifier si on doit cacher le prix d'entrée
    checkEntryPriceVisibility();
}

function checkEntryPriceVisibility() {
    const slPriceBtn = document.getElementById('slPriceBtn');
    const tpPriceBtn = document.getElementById('tpPriceBtn');
    const entryPriceRow = document.getElementById('entryPriceRow');
    
    if (entryPriceRow) {
        const showEntry = (slPriceBtn && slPriceBtn.classList.contains('active')) || 
                         (tpPriceBtn && tpPriceBtn.classList.contains('active'));
        entryPriceRow.style.display = showEntry ? 'block' : 'none';
    }
}

async function updateRealTimePrice() {
    const pairSelect = document.getElementById('pairSymbol');
    const priceDisplay = document.getElementById('priceDisplay');
    const displayPairName = document.getElementById('displayPairName');
    const currentPrice = document.getElementById('currentPrice');
    const priceLoading = document.getElementById('priceLoading');
    
    if (!pairSelect || !pairSelect.value) {
        if (priceDisplay) priceDisplay.style.display = 'none';
        return;
    }
    
    const symbol = pairSelect.value;
    
    // Afficher le loading
    if (priceDisplay) priceDisplay.style.display = 'block';
    if (priceLoading) priceLoading.style.display = 'block';
    if (currentPrice) currentPrice.textContent = '--';
    
    try {
        const response = await fetch(`/api/current-price/${symbol}`);
        const data = await response.json();
        
        if (priceLoading) priceLoading.style.display = 'none';
        
        if (data.success) {
            if (displayPairName) displayPairName.textContent = symbol;
            if (currentPrice) currentPrice.textContent = data.price;
            priceCache[symbol] = data.price;
        } else {
            if (displayPairName) displayPairName.textContent = symbol;
            if (currentPrice) currentPrice.textContent = 'Indisponible';
        }
    } catch (error) {
        console.error('Erreur récupération prix:', error);
        if (priceLoading) priceLoading.style.display = 'none';
        if (displayPairName) displayPairName.textContent = symbol;
        if (currentPrice) currentPrice.textContent = 'API déconnectée';
    }
}

function setupAutoCalculation() {
    const inputs = document.querySelectorAll('#calculatorForm input, #calculatorForm select');
    inputs.forEach(input => {
        input.addEventListener('input', debounceCalculate);
        input.addEventListener('change', debounceCalculate);
    });
}

let calculateTimeout;
function debounceCalculate() {
    clearTimeout(calculateTimeout);
    calculateTimeout = setTimeout(() => {
        if (isFormValid()) {
            performCalculation();
        }
    }, 300);
}

function isFormValid() {
    const pairSymbol = document.getElementById('pairSymbol')?.value;
    const capital = document.getElementById('capital')?.value;
    const riskPercent = document.getElementById('riskPercent')?.value;
    
    // Vérifier SL
    const slPips = document.getElementById('slPips');
    const slPrice = document.getElementById('slPrice');
    const slValid = (slPips?.style.display !== 'none' && slPips?.value) || 
                   (slPrice?.style.display !== 'none' && slPrice?.value);
    
    return pairSymbol && capital && riskPercent && slValid;
}

async function handleCalculation(e) {
    if (e) e.preventDefault();
    await performCalculation();
}

async function performCalculation() {
    const resultsDiv = document.getElementById('calculatorResults');
    if (!resultsDiv) return;
    
    showCalculationLoading();
    
    try {
        const formData = collectFormData();
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayCalculationResults(result);
        } else {
            showCalculationError(result.error || 'Erreur de calcul');
        }
    } catch (error) {
        console.error('Erreur calcul:', error);
        showCalculationError('Erreur de connexion');
    }
}

function collectFormData() {
    const pairSymbol = document.getElementById('pairSymbol').value;
    const orderType = document.querySelector('input[name="orderType"]:checked').value;
    const capital = parseFloat(document.getElementById('capital').value);
    const riskPercent = parseFloat(document.getElementById('riskPercent').value);
    
    // Collecte SL
    const slPips = document.getElementById('slPips');
    const slPrice = document.getElementById('slPrice');
    let stopLoss, stopLossType;
    
    if (slPips.style.display !== 'none' && slPips.value) {
        stopLoss = parseFloat(slPips.value);
        stopLossType = 'pips';
    } else if (slPrice.style.display !== 'none' && slPrice.value) {
        stopLoss = parseFloat(slPrice.value);
        stopLossType = 'price';
    }
    
    // Collecte TP
    const tpPips = document.getElementById('tpPips');
    const tpPrice = document.getElementById('tpPrice');
    let takeProfit, takeProfitType;
    
    if (tpPips.style.display !== 'none' && tpPips.value) {
        takeProfit = parseFloat(tpPips.value);
        takeProfitType = 'pips';
    } else if (tpPrice.style.display !== 'none' && tpPrice.value) {
        takeProfit = parseFloat(tpPrice.value);
        takeProfitType = 'price';
    }
    
    // Prix d'entrée si nécessaire
    const entryPriceInput = document.getElementById('entryPrice');
    const entryPrice = entryPriceInput?.value ? parseFloat(entryPriceInput.value) : null;
    
    return {
        pair_symbol: pairSymbol,
        order_type: orderType,
        capital: capital,
        risk_percent: riskPercent,
        stop_loss: stopLoss,
        stop_loss_type: stopLossType,
        take_profit: takeProfit,
        take_profit_type: takeProfitType,
        entry_price: entryPrice
    };
}

function showCalculationLoading() {
    const resultsDiv = document.getElementById('calculatorResults');
    resultsDiv.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-success" role="status">
                <span class="visually-hidden">Calcul...</span>
            </div>
            <p class="mt-2 text-muted">Calcul en cours...</p>
        </div>
    `;
    resultsDiv.style.display = 'block';
}

function displayCalculationResults(result) {
    const resultsDiv = document.getElementById('calculatorResults');
    
    const html = `
        <div class="results-container">
            <div class="results-header text-center mb-4">
                <h4 class="text-success mb-2">
                    <i class="fas fa-check-circle me-2"></i>Position Calculée
                </h4>
                <p class="text-muted">Résultats basés sur vos paramètres de risque</p>
            </div>
            
            <div class="row g-3 mb-4">
                <div class="col-md-3 col-6">
                    <div class="result-card text-center p-3 bg-success bg-opacity-10 rounded">
                        <h5 class="text-success mb-1">${result.lot_size}</h5>
                        <small class="text-muted">Taille de Position</small>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="result-card text-center p-3 bg-warning bg-opacity-10 rounded">
                        <h5 class="text-warning mb-1">${result.risk_usd} $</h5>
                        <small class="text-muted">Risque Monétaire</small>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="result-card text-center p-3 bg-info bg-opacity-10 rounded">
                        <h5 class="text-info mb-1">${result.potential_gain || 'N/A'}</h5>
                        <small class="text-muted">Gain Potentiel</small>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="result-card text-center p-3 bg-primary bg-opacity-10 rounded">
                        <h5 class="text-primary mb-1">${result.rr_ratio || 'N/A'}</h5>
                        <small class="text-muted">Ratio R:R</small>
                    </div>
                </div>
            </div>
            
            <div class="text-center">
                <button type="button" class="btn btn-outline-secondary" onclick="resetCalculator()">
                    <i class="fas fa-redo me-2"></i>Réinitialiser les Champs
                </button>
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

function showCalculationError(message) {
    const resultsDiv = document.getElementById('calculatorResults');
    resultsDiv.innerHTML = `
        <div class="alert alert-danger text-center">
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
        </div>
    `;
    resultsDiv.style.display = 'block';
}

function resetCalculator() {
    // Reset form
    document.getElementById('calculatorForm').reset();
    
    // Reset toggles to pips mode
    const slPipsBtn = document.getElementById('slPipsBtn');
    const tpPipsBtn = document.getElementById('tpPipsBtn');
    
    if (slPipsBtn) slPipsBtn.click();
    if (tpPipsBtn) tpPipsBtn.click();
    
    // Hide results
    const resultsDiv = document.getElementById('calculatorResults');
    if (resultsDiv) resultsDiv.style.display = 'none';
    
    // Hide price display
    const priceDisplay = document.getElementById('priceDisplay');
    if (priceDisplay) priceDisplay.style.display = 'none';
    
    // Hide entry price
    const entryPriceRow = document.getElementById('entryPriceRow');
    if (entryPriceRow) entryPriceRow.style.display = 'none';
}