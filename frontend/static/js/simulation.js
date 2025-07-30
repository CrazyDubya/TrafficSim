/**
 * Traffic Simulation JavaScript Controller
 * Handles WebSocket communication, simulation controls, and UI updates
 */

class TrafficSimulationController {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.simulationData = null;
        this.lastUpdateTime = 0;
        
        this.init();
    }
    
    init() {
        this.initializeWebSocket();
        this.initializeEventListeners();
        this.initializeUI();
    }
    
    initializeWebSocket() {
        // Initialize Socket.IO connection
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to simulation server');
            this.isConnected = true;
            this.updateConnectionStatus(true);
            this.requestUpdate();
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from simulation server');
            this.isConnected = false;
            this.updateConnectionStatus(false);
        });
        
        this.socket.on('simulation_update', (data) => {
            this.handleSimulationUpdate(data);
        });
        
        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.showMessage('Connection error: ' + error, 'error');
        });
    }
    
    initializeEventListeners() {
        // Simulation control buttons
        document.getElementById('start-btn').addEventListener('click', () => this.startSimulation());
        document.getElementById('pause-btn').addEventListener('click', () => this.pauseSimulation());
        document.getElementById('resume-btn').addEventListener('click', () => this.resumeSimulation());
        document.getElementById('step-btn').addEventListener('click', () => this.stepSimulation());
        document.getElementById('stop-btn').addEventListener('click', () => this.stopSimulation());
        document.getElementById('reset-btn').addEventListener('click', () => this.resetSimulation());
        
        // Scenario buttons
        document.getElementById('load-simple-btn').addEventListener('click', () => this.loadSimpleScenario());
        document.getElementById('clear-vehicles-btn').addEventListener('click', () => this.clearVehicles());
        
        // Vehicle controls
        document.getElementById('add-vehicle-btn').addEventListener('click', () => this.addVehicle());
        
        // Settings
        document.getElementById('update-settings-btn').addEventListener('click', () => this.updateSettings());
        
        // Modal controls
        document.querySelector('.close').addEventListener('click', () => this.closeModal());
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('vehicle-modal');
            if (event.target === modal) {
                this.closeModal();
            }
        });
    }
    
    initializeUI() {
        this.updateConnectionStatus(false);
        this.updateSimulationState('STOPPED');
        this.loadSettings();
    }
    
    // WebSocket Communication
    requestUpdate() {
        if (this.isConnected) {
            this.socket.emit('request_update');
        }
    }
    
    handleSimulationUpdate(data) {
        this.simulationData = data;
        this.lastUpdateTime = Date.now();
        
        // Update UI elements
        this.updateSimulationState(data.state);
        this.updateStatistics(data.stats);
        this.updateVisualization(data);
        this.updateCharts(data);
    }
    
    // API Communication
    async apiCall(endpoint, method = 'GET', data = null) {
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(`/api/${endpoint}`, options);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || 'API call failed');
            }
            
            return result;
        } catch (error) {
            console.error(`API call failed (${endpoint}):`, error);
            this.showMessage(`Error: ${error.message}`, 'error');
            throw error;
        }
    }
    
    // Simulation Control Methods
    async startSimulation() {
        try {
            await this.apiCall('start', 'POST');
            this.showMessage('Simulation started', 'success');
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    async pauseSimulation() {
        try {
            await this.apiCall('pause', 'POST');
            this.showMessage('Simulation paused', 'info');
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    async resumeSimulation() {
        try {
            await this.apiCall('resume', 'POST');
            this.showMessage('Simulation resumed', 'success');
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    async stepSimulation() {
        try {
            await this.apiCall('step', 'POST');
            this.showMessage('Simulation stepped', 'info');
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    async stopSimulation() {
        try {
            await this.apiCall('stop', 'POST');
            this.showMessage('Simulation stopped', 'info');
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    async resetSimulation() {
        try {
            await this.apiCall('reset', 'POST');
            this.showMessage('Simulation reset', 'info');
            // Clear visualization
            if (window.visualizationController) {
                window.visualizationController.clearCanvas();
            }
            // Clear charts
            if (window.chartsController) {
                window.chartsController.clearCharts();
            }
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    async loadSimpleScenario() {
        try {
            await this.apiCall('scenarios/simple', 'POST');
            this.showMessage('Simple highway scenario loaded', 'success');
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    async clearVehicles() {
        try {
            // This would need to be implemented in the API
            // For now, just reset the simulation
            await this.resetSimulation();
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    async addVehicle() {
        try {
            const laneId = parseInt(document.getElementById('vehicle-lane').value);
            const position = parseFloat(document.getElementById('vehicle-position').value);
            const driverType = document.getElementById('vehicle-driver-type').value;
            
            const vehicleData = {
                lane_id: laneId,
                position: position,
                driver_type: driverType
            };
            
            const result = await this.apiCall('vehicles', 'POST', vehicleData);
            this.showMessage(`Vehicle added: ID ${result.vehicle.id}`, 'success');
            
            // Reset form
            document.getElementById('vehicle-position').value = '0';
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    async updateSettings() {
        try {
            const settings = {
                time_step: parseFloat(document.getElementById('time-step').value),
                real_time_factor: parseFloat(document.getElementById('real-time-factor').value),
                debug_mode: document.getElementById('debug-mode').checked
            };
            
            await this.apiCall('settings', 'POST', settings);
            this.showMessage('Settings updated', 'success');
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    async loadSettings() {
        try {
            const settings = await this.apiCall('settings');
            
            document.getElementById('time-step').value = settings.time_step || 0.1;
            document.getElementById('real-time-factor').value = settings.real_time_factor || 1.0;
            document.getElementById('debug-mode').checked = settings.debug_mode || false;
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }
    
    // UI Update Methods
    updateConnectionStatus(connected) {
        const statusDot = document.getElementById('connection-status');
        statusDot.className = `status-dot ${connected ? 'connected' : 'disconnected'}`;
    }
    
    updateSimulationState(state) {
        document.getElementById('simulation-state').textContent = state;
        
        // Update button states
        const startBtn = document.getElementById('start-btn');
        const pauseBtn = document.getElementById('pause-btn');
        const resumeBtn = document.getElementById('resume-btn');
        const stepBtn = document.getElementById('step-btn');
        const stopBtn = document.getElementById('stop-btn');
        
        // Reset all buttons
        [startBtn, pauseBtn, resumeBtn, stepBtn, stopBtn].forEach(btn => {
            btn.disabled = false;
        });
        
        switch (state) {
            case 'STOPPED':
                pauseBtn.disabled = true;
                resumeBtn.disabled = true;
                stopBtn.disabled = true;
                break;
            case 'RUNNING':
                startBtn.disabled = true;
                resumeBtn.disabled = true;
                break;
            case 'PAUSED':
                startBtn.disabled = true;
                pauseBtn.disabled = true;
                break;
        }
    }
    
    updateStatistics(stats) {
        document.getElementById('sim-time').textContent = `${stats.current_time.toFixed(1)}s`;
        document.getElementById('active-vehicles').textContent = stats.active_vehicles;
        document.getElementById('total-vehicles').textContent = stats.total_vehicles;
        document.getElementById('avg-speed').textContent = `${stats.average_speed.toFixed(1)} m/s`;
        document.getElementById('traffic-flow').textContent = `${stats.total_flow.toFixed(0)} veh/h`;
        document.getElementById('avg-density').textContent = `${stats.average_density.toFixed(1)} veh/km`;
    }
    
    updateVisualization(data) {
        if (window.visualizationController) {
            window.visualizationController.updateVisualization(data);
        }
    }
    
    updateCharts(data) {
        if (window.chartsController) {
            window.chartsController.updateCharts(data);
        }
    }
    
    showVehicleInfo(vehicle) {
        const modal = document.getElementById('vehicle-modal');
        const vehicleInfo = document.getElementById('vehicle-info');
        
        vehicleInfo.innerHTML = `
            <div class="info-grid">
                <span class="info-label">ID:</span>
                <span class="info-value">${vehicle.id}</span>
                
                <span class="info-label">Position:</span>
                <span class="info-value">${vehicle.x.toFixed(1)} m</span>
                
                <span class="info-label">Lane:</span>
                <span class="info-value">${vehicle.lane_id}</span>
                
                <span class="info-label">Speed:</span>
                <span class="info-value">${vehicle.velocity.toFixed(1)} m/s</span>
                
                <span class="info-label">Acceleration:</span>
                <span class="info-value">${vehicle.acceleration.toFixed(2)} m/s²</span>
                
                <span class="info-label">Length:</span>
                <span class="info-value">${vehicle.length} m</span>
                
                <span class="info-label">Lane Changing:</span>
                <span class="info-value">${vehicle.is_changing_lane ? 'Yes' : 'No'}</span>
                
                <span class="info-label">Crashed:</span>
                <span class="info-value">${vehicle.crashed ? 'Yes' : 'No'}</span>
            </div>
        `;
        
        modal.style.display = 'block';
    }
    
    closeModal() {
        document.getElementById('vehicle-modal').style.display = 'none';
    }
    
    showMessage(message, type = 'info') {
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        
        // Insert at top of control panel
        const controlPanel = document.querySelector('.control-panel');
        controlPanel.insertBefore(messageDiv, controlPanel.firstChild);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 5000);
    }
}

// Initialize the controller when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.simulationController = new TrafficSimulationController();
});