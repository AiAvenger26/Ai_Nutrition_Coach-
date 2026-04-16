document.addEventListener('DOMContentLoaded', function() {
    loadProfile();
    loadTracking();
    updateNutrition();
    initChart();

    window.saveProfile = function() {
        const age = document.getElementById('age').value;
        const height = parseFloat(document.getElementById('height').value);
        const weight = parseFloat(document.getElementById('weight').value);
        
        localStorage.setItem('nutritionProfile', JSON.stringify({age, height, weight}));
        calculateBMI();
        alert('Profile saved!');
    };

    window.addFood = function() {
        const foodInput = document.getElementById('food-input');
        const foodName = foodInput.value;
        if (!foodName) {
            alert('Enter food name');
            return;
        }
        
        const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const logList = document.getElementById('food-log-list');
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `<span class="time">${time}</span><span>${foodName} - 450 kcal | P: 35g</span>`;
        logList.appendChild(logEntry);
        foodInput.value = '';
        updateNutrition();
    };

    window.updateTracking = function() {
        const water = parseInt(document.getElementById('water').value) || 0;
        const steps = parseInt(document.getElementById('steps').value) || 0;
        
        localStorage.setItem('tracking', JSON.stringify({water, steps}));
        updateProgress('water', water, 3000);
        updateProgress('steps', steps, 10000);
    };

    window.getAdvice = function() {
        document.getElementById('ai-output').innerHTML = '🤖 "Great progress! Aim for 150g protein daily, stay hydrated with 3L water, walk 10k steps."';
    };

    function loadProfile() {
        const profile = JSON.parse(localStorage.getItem('nutritionProfile') || '{}');
        document.getElementById('age').value = profile.age || '';
        document.getElementById('height').value = profile.height || '';
        document.getElementById('weight').value = profile.weight || '';
        calculateBMI();
    }

    function calculateBMI() {
        const height = parseFloat(document.getElementById('height').value);
        const weight = parseFloat(document.getElementById('weight').value);
        const bmiDisplay = document.getElementById('bmi-display');
        if (height && weight && bmiDisplay) {
            const bmi = (weight / ((height / 100) ** 2)).toFixed(1);
            const status = bmi < 18.5 ? 'Underweight' : bmi < 25 ? 'Normal' : bmi < 30 ? 'Overweight' : 'Obese';
            bmiDisplay.innerHTML = `BMI: ${bmi} (${status})`;
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
            barEl.style.width = `${percent}%`;
        }
    }

    function updateNutrition() {
        document.getElementById('energy-val').textContent = '1850 kcal';
        document.getElementById('protein-val').textContent = '95 g';
        document.getElementById('carbs-val').textContent = '220 g';
        document.getElementById('fat-val').textContent = '65 g';
    }

    function initChart() {
        const canvas = document.getElementById('nutrition-chart');
        if (canvas && typeof Chart !== 'undefined') {
            new Chart(canvas.getContext('2d'), {
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
                    scales: { y: { beginAtZero: true } },
                    plugins: { legend: { display: false } }
                }
            });
        }
    }
});
