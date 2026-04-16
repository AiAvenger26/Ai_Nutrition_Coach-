document.addEventListener('DOMContentLoaded', function() {
    // Dashboard functionality - Fixed syntax
    if (document.querySelector('.dashboard-container')) {
        loadProfile();
        loadTracking();
        updateNutrition();
        initChart();
    }

    window.saveProfile = function() {
        const age = document.getElementById('age').value;
        const height = parseFloat(document.getElementById('height').value);
        const weight = parseFloat(document.getElementById('weight').value);
        
        localStorage.setItem('nutritionProfile', JSON.stringify({age, height, weight}));
        calculateBMI();
        alert('Profile saved!');
    };

    window.addFood = function() {
        const foodName = document.getElementById('food-input').value;
        if (!foodName) return alert('Enter food name');
        
        const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `
            <span class="time">${time}</span>
            <span>${foodName} - 450 kcal | P: 35g</span>
        `;
        document.getElementById('food-log-list').appendChild(logEntry);
        document.getElementById('food-input').value = '';
        updateNutritionMock();
    };

    window.updateTracking = function() {
        const water = parseInt(document.getElementById('water').value) || 0;
        const steps = parseInt(document.getElementById('steps').value) || 0;
        
        localStorage.setItem('tracking', JSON.stringify({water, steps}));
        updateProgress('water', water, 3000);
        updateProgress('steps', steps, 10000);
    };

    window.getAdvice = function() {
        document.getElementById('ai-output').innerHTML = '🤖 "Great job tracking! Aim for 150g protein daily. Drink more water to stay hydrated!"';
    };

    function loadProfile() {
        const profile = JSON.parse(localStorage.getItem('nutritionProfile') || '{}');
        const ageEl = document.getElementById('age');
        const heightEl = document.getElementById('height');
        const weightEl = document.getElementById('weight');
        if (ageEl) ageEl.value = profile.age || '';
        if (heightEl) heightEl.value = profile.height || '';
        if (weightEl) weightEl.value = profile.weight || '';
        calculateBMI();
    }

    function calculateBMI() {
        const height = parseFloat(document.getElementById('height').value);
        const weight = parseFloat(document.getElementById('weight').value);
        const bmiEl = document.getElementById('bmi-display');
        if (bmiEl && height && weight && height > 0) {
            const bmi = (weight / Math.pow(height/100, 2)).toFixed(1);
            let status = bmi < 18.5 ? 'Underweight' : bmi < 25 ? 'Normal' : 'Overweight';
            bmiEl.innerHTML = `<strong>BMI: ${bmi} (${status})</strong>`;
        }
    }

    function loadTracking() {
        const tracking = JSON.parse(localStorage.getItem('tracking') || '{"water":0,"steps":0}');
        updateProgress('water', tracking.water, 3000);
        updateProgress('steps', tracking.steps, 10000);
    }

    function updateProgress(type, value, max) {
        const progressEl = document.getElementById(`${type}-progress`);
        const barEl = document.getElementById(`${type}-bar`);
        if (progressEl && barEl) {
            const percent = Math.min((value / max) * 100, 100);
            progressEl.textContent = `${value}/${max}`;
            barEl.style.width = percent + '%';
        }
    }

    function updateNutritionMock() {
        // Update with mock accumulating values
        document.getElementById('energy-val').textContent = '1850 kcal';
        document.getElementById('protein-val').textContent = '95 g';
        document.getElementById('carbs-val').textContent = '220 g';
        document.getElementById('fat-val').textContent = '65 g';
    }

    function initChart() {
        const chartEl = document.getElementById('nutrition-chart');
        if (chartEl && Chart) {
            const ctx = chartEl.getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Protein (g)',
                        data: [75, 85, 95, 110, 90, 105, 120],
                        backgroundColor: 'rgba(16,185,129,0.6)',
                        borderColor: 'rgba(16,185,129,1)',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true } },
                    plugins: { legend: { display: false } }
                }
            });
        }
    }
});
