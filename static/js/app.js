// 房间分配可视化系统 JavaScript

class RoomVisualization {
    constructor() {
        this.roomsData = null;
        this.currentFloor = null;
        this.searchTerm = '';
        this.filterFloor = '';
        this.filterStatus = '';
        this.currentView = 'overview'; // 'overview' 或 'floors'

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadRoomsData();
    }

    bindEvents() {
        // 搜索功能
        const searchInput = document.getElementById('searchInput');
        const clearSearch = document.getElementById('clearSearch');

        searchInput.addEventListener('input', this.debounce(() => {
            this.searchTerm = searchInput.value.trim();
            if (this.searchTerm) {
                this.performSearch();
            } else {
                this.hideSearchResults();
                this.showAllFloors();
            }
        }, 300));

        clearSearch.addEventListener('click', () => {
            searchInput.value = '';
            this.searchTerm = '';
            this.hideSearchResults();
            this.showAllFloors();
        });

        // 筛选功能
        document.getElementById('floorFilter').addEventListener('change', (e) => {
            this.filterFloor = e.target.value;
            this.applyFilters();
        });

        document.getElementById('statusFilter').addEventListener('change', (e) => {
            this.filterStatus = e.target.value;
            this.applyFilters();
        });

        // 刷新数据
        document.getElementById('refreshData').addEventListener('click', () => {
            this.loadRoomsData();
        });

        // 视图切换
        document.getElementById('overviewBtn').addEventListener('click', () => {
            this.switchToOverview();
        });

        document.getElementById('floorBtn').addEventListener('click', () => {
            this.switchToFloors();
        });

        // 模态框关闭
        document.getElementById('roomModal').addEventListener('click', (e) => {
            if (e.target.id === 'roomModal') {
                this.closeModal();
            }
        });

        // ESC键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    async loadRoomsData() {
        try {
            this.showLoading();

            const response = await fetch('/api/rooms');
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.roomsData = data;
            this.updateHeaderInfo();
            this.createFloorButtons();
            this.populateFloorFilter();
            this.renderCurrentView();
            this.hideLoading();

        } catch (error) {
            console.error('加载房间数据失败:', error);
            this.showError();
        }
    }

    updateHeaderInfo() {
        document.getElementById('totalRooms').textContent = `总房间数: ${this.roomsData.total_rooms}`;

        if (this.roomsData.timestamp) {
            const date = new Date(this.roomsData.timestamp);
            document.getElementById('lastUpdate').textContent =
                `最后更新: ${date.toLocaleString('zh-CN')}`;
        }
    }

    createFloorButtons() {
        const floorButtons = document.getElementById('floorButtons');
        floorButtons.innerHTML = '';

        // 添加"全部楼层"按钮
        const allBtn = document.createElement('button');
        allBtn.className = 'floor-btn active';
        allBtn.textContent = '全部';
        allBtn.addEventListener('click', () => this.showAllFloors());
        floorButtons.appendChild(allBtn);

        // 添加各楼层按钮
        this.roomsData.floor_numbers.forEach(floor => {
            const btn = document.createElement('button');
            btn.className = 'floor-btn';
            btn.textContent = `${floor}楼`;
            btn.dataset.floor = floor;
            btn.addEventListener('click', () => this.showFloor(floor));
            floorButtons.appendChild(btn);
        });
    }

    populateFloorFilter() {
        const floorFilter = document.getElementById('floorFilter');
        floorFilter.innerHTML = '<option value="">所有楼层</option>';

        this.roomsData.floor_numbers.forEach(floor => {
            const option = document.createElement('option');
            option.value = floor;
            option.textContent = `${floor}楼`;
            floorFilter.appendChild(option);
        });
    }

    switchToOverview() {
        this.currentView = 'overview';
        this.updateViewButtons();
        this.renderCurrentView();
    }

    switchToFloors() {
        this.currentView = 'floors';
        this.updateViewButtons();
        this.renderCurrentView();
    }

    updateViewButtons() {
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        if (this.currentView === 'overview') {
            document.getElementById('overviewBtn').classList.add('active');
            document.getElementById('floorButtons').style.display = 'none';
        } else {
            document.getElementById('floorBtn').classList.add('active');
            document.getElementById('floorButtons').style.display = 'flex';
        }
    }

    renderCurrentView() {
        if (this.currentView === 'overview') {
            this.renderOverview();
        } else {
            this.renderFloors();
        }
    }

    renderOverview() {
        const overviewView = document.getElementById('overviewView');
        const floorViews = document.getElementById('floorViews');

        overviewView.style.display = 'block';
        floorViews.style.display = 'none';

        // 生成全景视图HTML
        let html = '<div class="building-overview">';

        // 从20楼到1楼显示（顶层到底层）
        for (let floor = 20; floor >= 1; floor--) {
            const rooms = this.roomsData.floors[floor] || [];
            const occupiedCount = rooms.filter(room => room.tenants.length > 0).length;
            const vacantCount = rooms.length - occupiedCount;

            html += `
                <div class="floor-row">
                    <div class="floor-label">${floor}楼</div>
                    <div class="floor-rooms">
                        ${this.createFloorRoomsOverview(rooms, floor)}
                    </div>
                    <div class="floor-stats">
                        ${occupiedCount}/${rooms.length} 入住<br>
                        <small>${rooms.length > 0 ? Math.round(occupiedCount/rooms.length*100) : 0}%</small>
                    </div>
                </div>
            `;
        }

        html += '</div>';
        overviewView.innerHTML = html;
    }

    createFloorRoomsOverview(rooms, floor) {
        // 确保房间按房间号排序
        const sortedRooms = [...rooms].sort((a, b) => a.room_in_floor - b.room_in_floor);
        const roomsHtml = [];

        if (floor === 1) {
            // 1楼特殊布局: 01-06, 通道, 通道, 07-10
            const floor1Layout = [
                { type: 'room', number: '01' }, { type: 'room', number: '02' }, { type: 'room', number: '03' },
                { type: 'room', number: '04' }, { type: 'room', number: '05' }, { type: 'room', number: '06' },
                { type: 'passage', label: '通道' }, { type: 'passage', label: '通道' },
                { type: 'room', number: '07' }, { type: 'room', number: '08' }, { type: 'room', number: '09' },
                { type: 'room', number: '10' }
            ];

            floor1Layout.forEach(item => {
                if (item.type === 'passage') {
                    roomsHtml.push(`
                        <div class="mini-room passage" title="${item.label}">
                            ${item.label}
                        </div>
                    `);
                } else {
                    const roomNumber = `1${item.number}`;
                    const room = sortedRooms.find(r => r.room_number === roomNumber);

                    if (room) {
                        const tenantCount = room.tenants.length;
                        let roomClass = 'mini-room';

                        if (tenantCount === 0) {
                            roomClass += ' vacant';
                        } else if (tenantCount === 1) {
                            roomClass += ' occupied';
                        } else {
                            roomClass += ' multi-tenant';
                        }

                        roomsHtml.push(`
                            <div class="${roomClass}" onclick="app.showRoomDetail(${room.house_id})" title="${room.house_name}${room.tenants.length > 0 ? ' - ' + room.tenants.map(t => t.tenant_name).join(', ') : ' - 空闲'}">
                                ${item.number}
                            </div>
                        `);
                    } else {
                        // 空房间占位
                        roomsHtml.push(`
                            <div class="mini-room vacant" title="房间${roomNumber} - 空闲">
                                ${item.number}
                            </div>
                        `);
                    }
                }
            });
        } else {
            // 2-20楼正常布局，每层12间房
            for (let i = 1; i <= 12; i++) {
                const room = sortedRooms.find(r => r.room_in_floor === i);

                if (room) {
                    const tenantCount = room.tenants.length;
                    let roomClass = 'mini-room';
                    let roomText = room.room_number.slice(-2); // 显示房间号后两位

                    if (tenantCount === 0) {
                        roomClass += ' vacant';
                    } else if (tenantCount === 1) {
                        roomClass += ' occupied';
                    } else {
                        roomClass += ' multi-tenant';
                    }

                    roomsHtml.push(`
                        <div class="${roomClass}" onclick="app.showRoomDetail(${room.house_id})" title="${room.house_name}${room.tenants.length > 0 ? ' - ' + room.tenants.map(t => t.tenant_name).join(', ') : ' - 空闲'}">
                            ${roomText}
                        </div>
                    `);
                } else {
                    // 空房间占位
                    roomsHtml.push(`
                        <div class="mini-room vacant" title="房间${floor}${i.toString().padStart(2, '0')} - 空闲">
                            ${i.toString().padStart(2, '0')}
                        </div>
                    `);
                }
            }
        }

        return roomsHtml.join('');
    }

    showAllFloors() {
        this.currentFloor = null;
        this.updateFloorButtons();
        this.renderFloors();
    }

    showFloor(floor) {
        this.currentFloor = floor;
        this.updateFloorButtons();
        this.renderFloors();
    }

    updateFloorButtons() {
        document.querySelectorAll('.floor-btn').forEach(btn => {
            btn.classList.remove('active');
            if (!this.currentFloor && btn.textContent === '全部') {
                btn.classList.add('active');
            } else if (btn.dataset.floor == this.currentFloor) {
                btn.classList.add('active');
            }
        });
    }

    renderFloors() {
        const overviewView = document.getElementById('overviewView');
        const floorViews = document.getElementById('floorViews');

        overviewView.style.display = 'none';
        floorViews.style.display = 'block';

        floorViews.innerHTML = '';

        const floorsToShow = this.currentFloor ? [this.currentFloor] :
            this.roomsData.floor_numbers;

        floorsToShow.forEach(floor => {
            const rooms = this.roomsData.floors[floor];
            if (rooms && rooms.length > 0) {
                const floorView = this.createFloorView(floor, rooms);
                floorViews.appendChild(floorView);
            }
        });
    }

    createFloorView(floor, rooms) {
        const floorDiv = document.createElement('div');
        floorDiv.className = 'floor-view';
        floorDiv.dataset.floor = floor;

        // 统计房间状态
        const occupiedCount = rooms.filter(room => room.tenants.length > 0).length;
        const vacantCount = rooms.length - occupiedCount;

        floorDiv.innerHTML = `
            <div class="floor-header">
                <h2 class="floor-title"><i class="fas fa-layer-group"></i> ${floor}楼</h2>
                <div class="floor-info">
                    <span>总计 ${rooms.length} 间</span>
                    <span>已入住 ${occupiedCount} 间</span>
                    <span>空闲 ${vacantCount} 间</span>
                </div>
            </div>
            <div class="rooms-grid">
                ${rooms.map(room => this.createRoomCard(room)).join('')}
            </div>
        `;

        return floorDiv;
    }

    createRoomCard(room) {
        const tenantCount = room.tenants.length;
        let cardClass = 'room-card';
        let tenantInfo = '';

        if (tenantCount === 0) {
            cardClass += ' vacant-room';
            tenantInfo = '<div class="tenant-info">空闲</div>';
        } else if (tenantCount === 1) {
            cardClass += ' occupied-room';
            const tenant = room.main_tenant || room.tenants[0];
            tenantInfo = `
                <div class="tenant-info">
                    <div class="tenant-name">${tenant.tenant_name}</div>
                </div>
            `;
        } else {
            cardClass += ' multi-tenant';
            const mainTenant = room.main_tenant;
            tenantInfo = `
                <div class="tenant-info">
                    <div class="tenant-name">${mainTenant ? mainTenant.tenant_name : room.tenants[0].tenant_name}</div>
                    <div class="tenant-count">+${tenantCount - 1}人合租</div>
                </div>
            `;
        }

        return `
            <div class="${cardClass}" onclick="app.showRoomDetail(${room.house_id})">
                <div class="room-number">${room.room_number}</div>
                ${tenantInfo}
            </div>
        `;
    }

    async showRoomDetail(houseId) {
        try {
            const response = await fetch(`/api/room/${houseId}`);
            const room = await response.json();

            if (room.error) {
                throw new Error(room.error);
            }

            this.displayRoomModal(room);

        } catch (error) {
            console.error('获取房间详情失败:', error);
            alert('获取房间详情失败，请稍后重试');
        }
    }

    displayRoomModal(room) {
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');

        modalTitle.textContent = `${room.house_name} 详情`;

        // 房间基本信息
        let roomInfo = `
            <div class="room-detail">
                <h4><i class="fas fa-home"></i> 房间信息</h4>
                <div class="detail-grid">
                    <span class="detail-label">房间号:</span>
                    <span class="detail-value">${room.room_number}</span>
                    <span class="detail-label">楼层:</span>
                    <span class="detail-value">${room.floor}楼</span>
                    <span class="detail-label">栋号:</span>
                    <span class="detail-value">A${room.building}栋</span>
                    <span class="detail-label">单元:</span>
                    <span class="detail-value">${room.unit}单元</span>
                </div>
            </div>
        `;

        // 租户信息
        if (room.tenants.length > 0) {
            roomInfo += '<div class="room-detail"><h4><i class="fas fa-users"></i> 租户信息</h4>';

            room.tenants.forEach(tenant => {
                const isMain = tenant.is_main === 1;
                roomInfo += `
                    <div class="tenant-card ${isMain ? 'main-tenant' : ''}">
                        <div class="tenant-header">
                            <span class="tenant-name-large">${tenant.tenant_name}</span>
                            <span class="tenant-badge ${isMain ? 'main' : ''}">${isMain ? '主租户' : '合租户'}</span>
                        </div>
                        <div class="detail-grid">
                            <span class="detail-label">手机号:</span>
                            <span class="detail-value">${tenant.mobile}</span>
                            <span class="detail-label">身份证:</span>
                            <span class="detail-value">${this.maskIdCard(tenant.certificate_num)}</span>
                            <span class="detail-label">紧急联系人:</span>
                            <span class="detail-value">${tenant.emergency_contact}</span>
                            <span class="detail-label">紧急联系电话:</span>
                            <span class="detail-value">${tenant.emergency_mobile}</span>
                            <span class="detail-label">签约状态:</span>
                            <span class="detail-value">${tenant.sign_status === 1 ? '已签约' : '未签约'}</span>
                            <span class="detail-label">入住状态:</span>
                            <span class="detail-value">${tenant.occupancy_flag === 1 ? '已入住' : '未入住'}</span>
                        </div>
                    </div>
                `;
            });

            roomInfo += '</div>';
        } else {
            roomInfo += `
                <div class="room-detail">
                    <h4><i class="fas fa-bed"></i> 房间状态</h4>
                    <p style="color: #666; text-align: center; padding: 20px;">
                        <i class="fas fa-home" style="font-size: 2rem; margin-bottom: 10px; display: block;"></i>
                        该房间目前空闲，暂无租户入住
                    </p>
                </div>
            `;
        }

        modalBody.innerHTML = roomInfo;
        document.getElementById('roomModal').style.display = 'block';
    }

    closeModal() {
        document.getElementById('roomModal').style.display = 'none';
    }

    maskIdCard(idCard) {
        if (!idCard || idCard.length < 8) return idCard;
        return idCard.substring(0, 4) + '****' + idCard.substring(idCard.length - 4);
    }

    async performSearch() {
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(this.searchTerm)}`);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.displaySearchResults(data.rooms);

        } catch (error) {
            console.error('搜索失败:', error);
        }
    }

    displaySearchResults(rooms) {
        const searchResults = document.getElementById('searchResults');
        const searchResultsContent = document.getElementById('searchResultsContent');

        if (rooms.length === 0) {
            searchResultsContent.innerHTML = '<p style="text-align: center; color: #666;">未找到匹配的房间</p>';
        } else {
            // 按楼层分组显示搜索结果
            const floorGroups = {};
            rooms.forEach(room => {
                if (!floorGroups[room.floor]) {
                    floorGroups[room.floor] = [];
                }
                floorGroups[room.floor].push(room);
            });

            let html = '';
            Object.keys(floorGroups).sort((a, b) => parseInt(a) - parseInt(b)).forEach(floor => {
                html += `
                    <div class="floor-view">
                        <div class="floor-header">
                            <h3 class="floor-title">${floor}楼 - ${floorGroups[floor].length}间匹配</h3>
                        </div>
                        <div class="rooms-grid">
                            ${floorGroups[floor].map(room => this.createRoomCard(room)).join('')}
                        </div>
                    </div>
                `;
            });

            searchResultsContent.innerHTML = html;
        }

        searchResults.style.display = 'block';
        document.getElementById('overviewView').style.display = 'none';
        document.getElementById('floorViews').style.display = 'none';
    }

    hideSearchResults() {
        document.getElementById('searchResults').style.display = 'none';
        this.renderCurrentView();
    }

    applyFilters() {
        // 如果有搜索词，重新执行搜索
        if (this.searchTerm) {
            this.performSearch();
            return;
        }

        // 应用楼层筛选
        if (this.filterFloor) {
            this.showFloor(parseInt(this.filterFloor));
        } else {
            this.showAllFloors();
        }

        // 应用状态筛选
        if (this.filterStatus) {
            this.applyStatusFilter();
        }
    }

    applyStatusFilter() {
        const floorViews = document.querySelectorAll('.floor-view');

        floorViews.forEach(floorView => {
            const roomCards = floorView.querySelectorAll('.room-card');
            let visibleCount = 0;

            roomCards.forEach(card => {
                const isOccupied = card.classList.contains('occupied-room') || card.classList.contains('multi-tenant');
                const isVacant = card.classList.contains('vacant-room');

                let shouldShow = true;

                if (this.filterStatus === 'occupied' && !isOccupied) {
                    shouldShow = false;
                } else if (this.filterStatus === 'vacant' && !isVacant) {
                    shouldShow = false;
                }

                card.style.display = shouldShow ? 'block' : 'none';
                if (shouldShow) visibleCount++;
            });

            // 如果该楼层没有符合条件的房间，隐藏整个楼层
            floorView.style.display = visibleCount > 0 ? 'block' : 'none';
        });
    }

    showLoading() {
        document.getElementById('loading').style.display = 'block';
        document.getElementById('error').style.display = 'none';
        document.getElementById('overviewView').style.display = 'none';
        document.getElementById('floorViews').style.display = 'none';
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    showError() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'block';
        document.getElementById('overviewView').style.display = 'none';
        document.getElementById('floorViews').style.display = 'none';
    }

    // 防抖函数
    debounce(func, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }
}

// 全局函数，供HTML调用
function closeModal() {
    app.closeModal();
}

// 初始化应用
const app = new RoomVisualization();