/**
 * Traffic Simulation Visualization Controller
 * Handles canvas-based rendering of the traffic simulation
 */

class VisualizationController {
    constructor() {
        this.canvas = document.getElementById('simulation-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.scale = 0.5; // pixels per meter
        this.offsetX = 0;
        this.offsetY = 0;
        
        // Colors and styling
        this.colors = {
            road: '#404040',
            roadMarkings: '#FFFF00',
            grass: '#90EE90',
            sky: '#87CEEB',
            vehicle: {
                normal: '#FF4444',
                aggressive: '#FF0000',
                cautious: '#4444FF',
                selected: '#FFFF00'
            },
            lane: {
                border: '#FFFFFF',
                divider: '#FFFF99'
            }
        };
        
        this.selectedVehicle = null;
        this.lanes = [];
        this.vehicles = [];
        
        this.init();
    }
    
    init() {
        this.setupCanvas();
        this.setupEventListeners();
        this.drawBackground();
    }
    
    setupCanvas() {
        // Set up canvas size
        const container = this.canvas.parentElement;
        this.canvas.width = Math.min(1000, container.clientWidth - 40);
        this.canvas.height = 300;
        
        // Set up coordinate system
        this.scale = this.canvas.width / 2000; // Show 2000m of road
        this.offsetY = this.canvas.height / 2;
    }
    
    setupEventListeners() {
        // Canvas click event for vehicle selection
        this.canvas.addEventListener('click', (event) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            this.handleCanvasClick(x, y);
        });
        
        // Window resize event
        window.addEventListener('resize', () => {
            this.setupCanvas();
            this.drawVisualization();
        });
    }
    
    handleCanvasClick(canvasX, canvasY) {
        // Convert canvas coordinates to simulation coordinates
        const simX = canvasX / this.scale;
        const simY = (canvasY - this.offsetY) / this.scale;
        
        // Find clicked vehicle
        let clickedVehicle = null;
        const clickTolerance = 10 / this.scale; // 10 pixels tolerance
        
        for (const vehicle of this.vehicles) {
            const vehicleX = vehicle.x * this.scale;
            const vehicleY = this.offsetY + vehicle.y * this.scale;
            
            // Check if click is within vehicle bounds
            if (Math.abs(canvasX - vehicleX) < clickTolerance &&
                Math.abs(canvasY - vehicleY) < clickTolerance) {
                clickedVehicle = vehicle;
                break;
            }
        }
        
        if (clickedVehicle) {
            this.selectedVehicle = clickedVehicle;
            if (window.simulationController) {
                window.simulationController.showVehicleInfo(clickedVehicle);
            }
        } else {
            this.selectedVehicle = null;
        }
        
        this.drawVisualization();
    }
    
    updateVisualization(simulationData) {
        this.lanes = simulationData.lanes || [];
        this.vehicles = simulationData.vehicles || [];
        this.drawVisualization();
    }
    
    drawVisualization() {
        this.clearCanvas();
        this.drawBackground();
        this.drawLanes();
        this.drawVehicles();
        this.drawLegend();
    }
    
    clearCanvas() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    drawBackground() {
        // Sky background
        const gradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
        gradient.addColorStop(0, this.colors.sky);
        gradient.addColorStop(0.7, this.colors.grass);
        
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    drawLanes() {
        if (this.lanes.length === 0) return;
        
        // Calculate road bounds
        const roadWidth = this.lanes.length * 4; // 4m per lane
        const roadTop = this.offsetY - (roadWidth / 2) * this.scale;
        const roadHeight = roadWidth * this.scale;
        
        // Draw road surface
        this.ctx.fillStyle = this.colors.road;
        this.ctx.fillRect(0, roadTop, this.canvas.width, roadHeight);
        
        // Draw lane markings
        this.ctx.strokeStyle = this.colors.lane.divider;
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([10, 10]);
        
        for (let i = 1; i < this.lanes.length; i++) {
            const y = roadTop + (i * 4 * this.scale);
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.canvas.width, y);
            this.ctx.stroke();
        }
        
        // Draw road borders
        this.ctx.strokeStyle = this.colors.lane.border;
        this.ctx.lineWidth = 3;
        this.ctx.setLineDash([]);
        
        this.ctx.beginPath();
        this.ctx.moveTo(0, roadTop);
        this.ctx.lineTo(this.canvas.width, roadTop);
        this.ctx.stroke();
        
        this.ctx.beginPath();
        this.ctx.moveTo(0, roadTop + roadHeight);
        this.ctx.lineTo(this.canvas.width, roadTop + roadHeight);
        this.ctx.stroke();
        
        // Draw lane numbers
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = '14px Arial';
        this.ctx.textAlign = 'left';
        
        for (let i = 0; i < this.lanes.length; i++) {
            const y = roadTop + (i * 4 * this.scale) + (2 * this.scale);
            this.ctx.fillText(`Lane ${i}`, 10, y);
        }
    }
    
    drawVehicles() {
        for (const vehicle of this.vehicles) {
            this.drawVehicle(vehicle);
        }
    }
    
    drawVehicle(vehicle) {
        const x = vehicle.x * this.scale;
        const y = this.offsetY + (vehicle.lane_id * 4 - 2) * this.scale + vehicle.y * this.scale;
        
        const length = vehicle.length * this.scale;
        const width = vehicle.width * this.scale;
        
        // Determine vehicle color based on driver type or state
        let color = this.colors.vehicle.normal;
        
        if (vehicle.crashed) {
            color = '#800080'; // Purple for crashed
        } else if (vehicle === this.selectedVehicle) {
            color = this.colors.vehicle.selected;
        } else if (vehicle.driver_type) {
            switch (vehicle.driver_type) {
                case 'AGGRESSIVE':
                    color = this.colors.vehicle.aggressive;
                    break;
                case 'CAUTIOUS':
                    color = this.colors.vehicle.cautious;
                    break;
                default:
                    color = this.colors.vehicle.normal;
            }
        }
        
        // Draw vehicle body
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x - length/2, y - width/2, length, width);
        
        // Draw vehicle outline
        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(x - length/2, y - width/2, length, width);
        
        // Draw direction indicator (arrow)
        if (length > 10) {
            this.ctx.fillStyle = '#FFFFFF';
            this.ctx.beginPath();
            this.ctx.moveTo(x + length/2 - 2, y);
            this.ctx.lineTo(x + length/2 - 8, y - 3);
            this.ctx.lineTo(x + length/2 - 8, y + 3);
            this.ctx.closePath();
            this.ctx.fill();
        }
        
        // Draw vehicle ID if selected or in debug mode
        if (vehicle === this.selectedVehicle || (window.simulationController && 
            window.simulationController.simulationData && 
            window.simulationController.simulationData.settings.debug_mode)) {
            
            this.ctx.fillStyle = '#000000';
            this.ctx.font = '10px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(`${vehicle.id}`, x, y - width/2 - 5);
        }
        
        // Draw speed indicator
        if (vehicle.velocity > 0) {
            const speedBarLength = Math.min(vehicle.velocity * 2, 30);
            this.ctx.fillStyle = '#00FF00';
            this.ctx.fillRect(x - speedBarLength/2, y + width/2 + 2, speedBarLength, 2);
        }
        
        // Draw lane change indicator
        if (vehicle.is_changing_lane && vehicle.lane_change_direction) {
            this.ctx.strokeStyle = '#FFFF00';
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            
            const arrowY = y + (vehicle.lane_change_direction === 'LEFT' ? -width : width);
            this.ctx.moveTo(x - 5, y);
            this.ctx.lineTo(x, arrowY);
            this.ctx.lineTo(x + 5, y);
            this.ctx.stroke();
        }
    }
    
    drawLegend() {
        const legendX = this.canvas.width - 200;
        const legendY = 20;
        
        // Legend background
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        this.ctx.fillRect(legendX, legendY, 180, 120);
        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(legendX, legendY, 180, 120);
        
        // Legend title
        this.ctx.fillStyle = '#000000';
        this.ctx.font = 'bold 12px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText('Legend', legendX + 10, legendY + 20);
        
        // Vehicle types
        const vehicleTypes = [
            { label: 'Normal Driver', color: this.colors.vehicle.normal },
            { label: 'Aggressive Driver', color: this.colors.vehicle.aggressive },
            { label: 'Cautious Driver', color: this.colors.vehicle.cautious },
            { label: 'Selected Vehicle', color: this.colors.vehicle.selected },
            { label: 'Crashed Vehicle', color: '#800080' }
        ];
        
        this.ctx.font = '10px Arial';
        for (let i = 0; i < vehicleTypes.length; i++) {
            const y = legendY + 35 + i * 15;
            
            // Draw color box
            this.ctx.fillStyle = vehicleTypes[i].color;
            this.ctx.fillRect(legendX + 10, y - 8, 12, 8);
            this.ctx.strokeStyle = '#000000';
            this.ctx.strokeRect(legendX + 10, y - 8, 12, 8);
            
            // Draw label
            this.ctx.fillStyle = '#000000';
            this.ctx.fillText(vehicleTypes[i].label, legendX + 30, y);
        }
    }
    
    // Utility methods
    getVehicleAtPosition(x, y) {
        for (const vehicle of this.vehicles) {
            const vehicleX = vehicle.x * this.scale;
            const vehicleY = this.offsetY + (vehicle.lane_id * 4 - 2) * this.scale;
            
            const length = vehicle.length * this.scale;
            const width = vehicle.width * this.scale;
            
            if (x >= vehicleX - length/2 && x <= vehicleX + length/2 &&
                y >= vehicleY - width/2 && y <= vehicleY + width/2) {
                return vehicle;
            }
        }
        return null;
    }
    
    centerOnVehicle(vehicleId) {
        const vehicle = this.vehicles.find(v => v.id === vehicleId);
        if (vehicle) {
            this.offsetX = this.canvas.width / 2 - vehicle.x * this.scale;
            this.drawVisualization();
        }
    }
    
    zoomIn() {
        this.scale *= 1.2;
        this.drawVisualization();
    }
    
    zoomOut() {
        this.scale /= 1.2;
        this.drawVisualization();
    }
    
    resetView() {
        this.scale = this.canvas.width / 2000;
        this.offsetX = 0;
        this.drawVisualization();
    }
}

// Initialize the visualization controller when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.visualizationController = new VisualizationController();
});