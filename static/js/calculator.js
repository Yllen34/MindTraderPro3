/**
 * Trading Calculator Pro - JavaScript du calculateur
 */

class TradingCalculator {
    constructor() {
        this.form = document.getElementById('calculatorForm');
        this.resultsDiv = document.getElementById('calculatorResults');
        this.historyTable = document.getElementById('historyTableBody');
        this.calculateBtn = document.getElementById('calculateBtn');
        
        this.init();
    }

    init() {
        // Event listeners
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Auto-calcul en temps réel
        const inputs = this.form.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('input', () => this.debounceCalculate());
        });

        // Charger l'historique
        this.loadHistory();
        
        // Clear history button
        document.getElementById('clearHistory')?.addEventListener('click', () => this.clearHistory());
    }

    debounceCalculate() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            if (this.isFormValid()) {
                this.calculatePosition();
            }
        }, 500);
    }

    async handleSubmit(e) {
        e.preventDefault();
        await this.calculatePosition();
    }

    isFormValid() {
        const required = ['capital', 'risk_percent', 'entry_price', 'stop_loss'];
        return required.every(field => {
            const value = document.getElementById(field).value;
            return value && !isNaN(parseFloat(value));
        });
    }

    async calculatePosition() {
        if (!this.isFormValid()) return;

        this.showLoading();

        try {
            const formData = new FormData(this.form);
            const data = Object.fromEntries(formData.entries());

            const response = await fetch('/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.displayResults(result);
                this.saveToHistory(data, result);
                this.updateHistory();
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError('Erreur de calcul: ' + error.message);
        }
    }

    showLoading() {
        this.calculateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Calcul...';
        this.calculateBtn.disabled = true;
    }

    displayResults(result) {
        const direction = document.getElementById('direction').value;
        const symbol = document.getElementById('symbol').value;
        const capital = parseFloat(document.getElementById('capital').value);
        const riskPercent = parseFloat(document.getElementById('risk_percent').value);
        
        // Calculer le ratio R/R si Take Profit fourni
        const takeProfitInput = document.getElementById('take_profit').value;
        let rrRatio = 'N/A';
        
        if (takeProfitInput) {
            const entryPrice = parseFloat(document.getElementById('entry_price').value);
            const stopLoss = parseFloat(document.getElementById('stop_loss').value);
            const takeProfit = parseFloat(takeProfitInput);
            
            const risk = Math.abs(entryPrice - stopLoss);
            const reward = Math.abs(takeProfit - entryPrice);
            rrRatio = `1:${(reward / risk).toFixed(2)}`;
        }

        const html = `
            <div class="calculator-result">
                <h4 class="mb-3">
                    <i class="fas fa-chart-${direction === 'buy' ? 'line' : 'line-down'} me-2"></i>
                    ${symbol} - ${direction === 'buy' ? 'ACHAT' : 'VENTE'}
                </h4>
                
                <div class="row text-center">
                    <div class="col-6">
                        <h3 class="text-warning">${result.lot_size}</h3>
                        <small>Taille de Position (Lots)</small>
                    </div>
                    <div class="col-6">
                        <h3 class="text-info">€${result.risk_amount}</h3>
                        <small>Risque (${riskPercent}%)</small>
                    </div>
                </div>
                
                <hr class="bg-white">
                
                <div class="row small">
                    <div class="col-6">
                        <strong>Pip Value:</strong> €${result.pip_value}
                    </div>
                    <div class="col-6">
                        <strong>Distance SL:</strong> ${result.pip_difference} pips
                    </div>
                    <div class="col-6">
                        <strong>Capital:</strong> €${capital.toLocaleString()}
                    </div>
                    <div class="col-6">
                        <strong>R/R Ratio:</strong> ${rrRatio}
                    </div>
                </div>
            </div>
        `;

        this.resultsDiv.innerHTML = html;
        this.resultsDiv.classList.add('fade-in');

        // Reset button
        this.calculateBtn.innerHTML = '<i class="fas fa-calculator me-2"></i>Calculer la Position';
        this.calculateBtn.disabled = false;

        // Show AI advice
        this.showAIAdvice(result);
    }

    showAIAdvice(result) {
        const advice = this.generateAdvice(result);
        const adviceDiv = document.getElementById('aiAdvice');
        
        adviceDiv.innerHTML = `
            <div class="alert alert-${advice.type}">
                <i class="fas fa-robot me-2"></i>
                <strong>Conseil IA:</strong> ${advice.message}
            </div>
        `;
    }

    generateAdvice(result) {
        const riskPercent = parseFloat(document.getElementById('risk_percent').value);
        const lotSize = result.lot_size;

        if (riskPercent > 2) {
            return {
                type: 'warning',
                message: 'Attention ! Votre risque dépasse 2%. Considérez réduire la taille de position.'
            };
        } else if (lotSize < 0.01) {
            return {
                type: 'info',
                message: 'Position très petite. Vous pourriez augmenter légèrement le risque pour optimiser.'
            };
        } else if (riskPercent <= 1) {
            return {
                type: 'success',
                message: 'Excellente gestion du risque ! Votre position est bien dimensionnée.'
            };
        } else {
            return {
                type: 'primary',
                message: 'Position équilibrée. Respectez votre plan de trading !'
            };
        }
    }

    showError(message) {
        this.resultsDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
        
        this.calculateBtn.innerHTML = '<i class="fas fa-calculator me-2"></i>Calculer la Position';
        this.calculateBtn.disabled = false;
    }

    saveToHistory(data, result) {
        const history = JSON.parse(localStorage.getItem('calculatorHistory') || '[]');
        const timestamp = new Date().toISOString();
        
        const entry = {
            timestamp,
            symbol: data.symbol,
            direction: data.direction,
            capital: data.capital,
            risk_percent: data.risk_percent,
            entry_price: data.entry_price,
            stop_loss: data.stop_loss,
            take_profit: data.take_profit || null,
            lot_size: result.lot_size,
            risk_amount: result.risk_amount
        };

        history.unshift(entry);
        
        // Garder seulement les 20 derniers
        if (history.length > 20) {
            history.splice(20);
        }

        localStorage.setItem('calculatorHistory', JSON.stringify(history));
    }

    loadHistory() {
        this.updateHistory();
    }

    updateHistory() {
        const history = JSON.parse(localStorage.getItem('calculatorHistory') || '[]');
        
        if (history.length === 0) {
            this.historyTable.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="fas fa-inbox me-2"></i>
                        Aucun calcul effectué
                    </td>
                </tr>
            `;
            return;
        }

        this.historyTable.innerHTML = history.map(entry => {
            const time = new Date(entry.timestamp).toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit'
            });
            
            const directionIcon = entry.direction === 'buy' ? '📈' : '📉';
            const directionClass = entry.direction === 'buy' ? 'text-success' : 'text-danger';
            
            // Calculer R/R si Take Profit disponible
            let rrRatio = 'N/A';
            if (entry.take_profit) {
                const risk = Math.abs(parseFloat(entry.entry_price) - parseFloat(entry.stop_loss));
                const reward = Math.abs(parseFloat(entry.take_profit) - parseFloat(entry.entry_price));
                rrRatio = `1:${(reward / risk).toFixed(2)}`;
            }

            return `
                <tr>
                    <td>${time}</td>
                    <td><strong>${entry.symbol}</strong></td>
                    <td class="${directionClass}">${directionIcon} ${entry.direction.toUpperCase()}</td>
                    <td><span class="badge bg-primary">${entry.lot_size}</span></td>
                    <td>€${parseFloat(entry.risk_amount).toFixed(2)}</td>
                    <td>${rrRatio}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-info" onclick="calculator.reuseCalculation('${entry.timestamp}')">
                            <i class="fas fa-redo fa-xs"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    reuseCalculation(timestamp) {
        const history = JSON.parse(localStorage.getItem('calculatorHistory') || '[]');
        const entry = history.find(h => h.timestamp === timestamp);
        
        if (entry) {
            // Remplir le formulaire avec les données
            document.getElementById('symbol').value = entry.symbol;
            document.getElementById('direction').value = entry.direction;
            document.getElementById('capital').value = entry.capital;
            document.getElementById('risk_percent').value = entry.risk_percent;
            document.getElementById('entry_price').value = entry.entry_price;
            document.getElementById('stop_loss').value = entry.stop_loss;
            if (entry.take_profit) {
                document.getElementById('take_profit').value = entry.take_profit;
            }
            
            // Recalculer
            this.calculatePosition();
        }
    }

    clearHistory() {
        if (confirm('Êtes-vous sûr de vouloir effacer l\'historique ?')) {
            localStorage.removeItem('calculatorHistory');
            this.updateHistory();
        }
    }
}

// Initialiser le calculateur quand la page est chargée
document.addEventListener('DOMContentLoaded', () => {
    window.calculator = new TradingCalculator();
});