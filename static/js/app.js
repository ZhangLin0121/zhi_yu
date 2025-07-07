// 房间分配可视化系统 JavaScript

class RoomVisualization {
    constructor() {
        this.roomsData = null;
        // 移除房间详情缓存，直接从数据库获取
        this.currentFloor = null;
        this.searchTerm = '';
        this.filterFloor = '';
        this.filterStatus = '';
        this.filterTag = ''; // 新增：标签过滤
        this.currentView = 'overview'; // 'overview' 或 'floors'
        this.cacheLoaded = false; // 新增：标记缓存是否已加载
        this.tagsData = null; // 新增：标签数据
        this.tagStatistics = null; // 新增：标签统计
        this.currentEditingStudent = null; // 新增：当前编辑的学生

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

        document.getElementById('tagFilter').addEventListener('change', (e) => {
            this.filterTag = e.target.value;
            this.applyFilters();
        });

        // 刷新数据
        document.getElementById('refreshData').addEventListener('click', () => {
            this.loadRoomsData();
        });

        // 刷新认证信息
        document.getElementById('refreshAuth').addEventListener('click', () => {
            this.refreshAuth();
        });

        // 标签管理
        document.getElementById('tagManager').addEventListener('click', () => {
            this.openTagManager();
        });

        // 清除缓存
        document.getElementById('clearCache').addEventListener('click', () => {
            this.clearAllCache();
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

        // 标签管理模态框关闭
        document.getElementById('tagModal').addEventListener('click', (e) => {
            if (e.target.id === 'tagModal') {
                this.closeTagModal();
            }
        });

        // 学生标签编辑模态框关闭
        document.getElementById('studentTagModal').addEventListener('click', (e) => {
            if (e.target.id === 'studentTagModal') {
                this.closeStudentTagModal();
            }
        });

        // ESC键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
                this.closeTagModal();
                this.closeStudentTagModal();
            }
        });
    }

    async loadRoomsData(skipSync = false) {
        try {
            this.showLoading();

            // 自动检测API基础路径
            const basePath = window.location.pathname.includes('/rooms/') ? '/rooms' : '';

            // 如果是首次加载（skipSync=false），先同步数据
            if (!skipSync) {
                console.log('首次加载，开始同步外部API数据到数据库...');
                try {
                    const syncResponse = await fetch(`${basePath}/api/sync`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    const syncData = await syncResponse.json();
                    if (syncData.success) {
                        console.log('数据同步成功:', syncData.message);
                    } else {
                        console.warn('数据同步失败:', syncData.error);
                    }
                } catch (syncError) {
                    console.warn('数据同步发生错误，但继续从数据库加载:', syncError);
                }
            }

            console.log('开始从数据库加载房间数据...');

            const [basicResponse, tagsResponse] = await Promise.all([
                fetch(`${basePath}/api/rooms/with-tags`), // 从数据库读取
                fetch(`${basePath}/api/tags`)
            ]);

            const basicData = await basicResponse.json();
            const tagsData = await tagsResponse.json();

            // 检查基本数据是否成功获取
            if (basicData.error || !basicData.success) {
                throw new Error(basicData.error || '获取房间数据失败');
            }

            console.log('房间数据加载成功，包含标签统计:', basicData.tag_statistics);

            // 处理标签数据
            if (tagsData.success) {
                this.tagsData = tagsData.tags;
                this.tagStatistics = tagsData.statistics;
                console.log('标签数据加载成功:', this.tagsData);
            } else {
                console.warn('加载标签数据失败:', tagsData.error);
                this.tagsData = ['22级硕博士', '23级硕博士', '24级硕博士', '实习实践', '未分类'];
                this.tagStatistics = {};
            }

            // 优先使用带标签数据中的标签统计
            if (basicData.tag_statistics) {
                this.tagStatistics = basicData.tag_statistics;
                console.log('使用带标签数据中的标签统计:', this.tagStatistics);
            }

            this.roomsData = basicData;
            this.cacheLoaded = true;

            this.updateHeaderInfo();
            this.createFloorButtons();
            this.populateFloorFilter();
            this.populateTagFilter();
            this.updateTagLegend();
            this.renderCurrentView();
            this.hideLoading();

            // 显示缓存状态
            this.updateCacheStatus();

        } catch (error) {
            console.error('加载房间数据失败:', error);
            this.showError();
        }
    }

    updateHeaderInfo() {
        document.getElementById('totalRooms').textContent = `总房间数: ${this.roomsData.total_rooms}`;

        // 添加入住统计信息
        const occupiedCount = this.roomsData.occupied_count || 0;
        const vacantCount = this.roomsData.vacant_count || 0;
        const occupancyRate = this.roomsData.total_rooms > 0 ?
            ((occupiedCount / this.roomsData.total_rooms) * 100).toFixed(1) : 0;

        // 更新或创建入住统计显示
        let statsElement = document.getElementById('occupancyStats');
        if (!statsElement) {
            statsElement = document.createElement('div');
            statsElement.id = 'occupancyStats';
            statsElement.style.cssText = 'margin: 10px 0; color: #475569; font-size: 14px;';
            document.getElementById('totalRooms').parentNode.appendChild(statsElement);
        }

        statsElement.innerHTML = `
            <div>已入住: ${occupiedCount} 间 | 空置: ${vacantCount} 间 | 入住率: ${occupancyRate}%</div>
        `;

        if (this.roomsData.timestamp) {
            const date = new Date(this.roomsData.timestamp);
            document.getElementById('lastUpdate').textContent =
                `最后更新: ${date.toLocaleString('zh-CN')}`;
        }
    }

    updateCacheStatus() {
        // 在页面顶部显示缓存状态
        const existingStatus = document.getElementById('cacheStatus');
        if (existingStatus) {
            existingStatus.remove();
        }

        if (this.cacheLoaded) {
            const statusDiv = document.createElement('div');
            statusDiv.id = 'cacheStatus';
            statusDiv.className = 'cache-status-success';
            statusDiv.innerHTML = `
                <i class="fas fa-check-circle"></i>
                已缓存所有房间详细信息，点击房间可即时查看
            `;

            const header = document.querySelector('.header');
            header.appendChild(statusDiv);

            // 3秒后自动隐藏
            setTimeout(() => {
                if (statusDiv.parentNode) {
                    statusDiv.style.opacity = '0';
                    setTimeout(() => statusDiv.remove(), 300);
                }
            }, 3000);
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

        // 建筑信息头部 - 从floors对象中获取所有房间
        const allRooms = [];
        Object.values(this.roomsData.floors).forEach(floorRooms => {
            allRooms.push(...floorRooms);
        });

        const totalRooms = allRooms.length;
        const occupiedRooms = allRooms.filter(room => room.tenants.length > 0).length;
        const vacantRooms = totalRooms - occupiedRooms;
        const multiTenantRooms = allRooms.filter(room => room.tenants.length > 1).length;

        // 50平米房间统计
        const largeRooms = allRooms.filter(room => this.isLargeRoom(room.room_number)).length;
        const largeRoomsOccupied = allRooms.filter(room =>
            this.isLargeRoom(room.room_number) && room.tenants.length > 0
        ).length;
        const largeRoomsVacant = largeRooms - largeRoomsOccupied;

        // 35平米房间统计
        const smallRooms = allRooms.filter(room => !this.isLargeRoom(room.room_number)).length;
        const smallRoomsOccupied = allRooms.filter(room =>
            !this.isLargeRoom(room.room_number) && room.tenants.length > 0
        ).length;
        const smallRoomsVacant = smallRooms - smallRoomsOccupied;

        // 17-20层统计
        const highFloorRooms = allRooms.filter(room => {
            const floorNumber = Math.floor(parseInt(room.room_number) / 100);
            return floorNumber >= 17 && floorNumber <= 20;
        }).length;
        const highFloorRoomsOccupied = allRooms.filter(room => {
            const floorNumber = Math.floor(parseInt(room.room_number) / 100);
            return floorNumber >= 17 && floorNumber <= 20 && room.tenants.length > 0;
        }).length;
        const highFloorRoomsVacant = highFloorRooms - highFloorRoomsOccupied;

        // 计算入住率
        const occupancyRate = totalRooms > 0 ? ((occupiedRooms / totalRooms) * 100).toFixed(1) : 0;
        const largeRoomsRate = largeRooms > 0 ? ((largeRoomsOccupied / largeRooms) * 100).toFixed(1) : 0;
        const smallRoomsRate = smallRooms > 0 ? ((smallRoomsOccupied / smallRooms) * 100).toFixed(1) : 0;
        const highFloorRate = highFloorRooms > 0 ? ((highFloorRoomsOccupied / highFloorRooms) * 100).toFixed(1) : 0;

        // 生成全景视图HTML
        let html = '<div class="building-overview">';

        // 添加建筑信息头部
        html += `
            <div class="building-header">
                <div class="building-title">A4栋学生公寓</div>
                <div class="building-stats">
                    <div class="stats-row">
                        <strong>总计：</strong>共计 ${totalRooms} 套，入住 ${occupiedRooms} 套，入住率 ${occupancyRate}%
                    </div>
                    <div class="stats-row">
                        <strong>35平米：</strong>共计 ${smallRooms} 套，入住 ${smallRoomsOccupied} 套，入住率 ${smallRoomsRate}%
                    </div>
                    <div class="stats-row">
                        <strong>50平米：</strong>共计 ${largeRooms} 套，入住 ${largeRoomsOccupied} 套，入住率 ${largeRoomsRate}%
                    </div>
                    <div class="stats-row">
                        <strong>17-20层：</strong>共计 ${highFloorRooms} 套，入住 ${highFloorRoomsOccupied} 套，入住率 ${highFloorRate}%
                    </div>
                </div>
            </div>
        `;

        // 添加图例
        const legendHtml = `
            <div class="room-type-legend">
                <div class="legend-item-inline">
                    <div class="mini-room vacant">01</div>
                    <span>空闲房间</span>
                </div>
                <div class="legend-item-inline">
                    <div class="mini-room occupied">02</div>
                    <span>已入住</span>
                </div>
                <div class="legend-item-inline">
                    <div class="mini-room multi-tenant">03</div>
                    <span>多人合租</span>
                </div>
                <div class="legend-item-inline">
                    <span style="color: #64748b; font-size: 13px; font-weight: 500;">竖直虚线左侧为50㎡房间，右侧为35㎡房间</span>
                </div>
            </div>
        `;

        html += legendHtml;

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
                        <span class="stat-line">入住: <span class="occupied-count">${occupiedCount}</span></span>
                        <span class="stat-line">空闲: <span class="vacant-count">${vacantCount}</span></span>
                        <span class="stat-line">率: <span class="occupancy-rate">${rooms.length > 0 ? Math.round(occupiedCount/rooms.length*100) : 0}%</span></span>
                    </div>
                </div>
            `;
        }

        html += '</div>';
        overviewView.innerHTML = html;
    }

    // 判断是否为50平米房间 (1、2、3和11、12号房间)
    isLargeRoom(roomNumberOrInFloor) {
        let roomInFloor;
        if (typeof roomNumberOrInFloor === 'string') {
            // 从完整房间号提取房间内编号 (如 "1001" -> 1)
            roomInFloor = parseInt(roomNumberOrInFloor.slice(-2));
        } else {
            roomInFloor = roomNumberOrInFloor;
        }
        return [1, 2, 3, 11, 12].includes(roomInFloor);
    }

    createFloorRoomsOverview(rooms, floor) {
        // 确保房间按房间号排序，并添加room_in_floor字段
        const sortedRooms = [...rooms].map(room => ({
            ...room,
            room_in_floor: parseInt(room.room_number.slice(-2))
        })).sort((a, b) => a.room_in_floor - b.room_in_floor);
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

                        // 检查是否为50平米房间
                        if (this.isLargeRoom(room.room_in_floor)) {
                            roomClass += ' large-room';
                        }

                        // 添加房间分隔虚线（3号和10号房间后面）
                        if (room.room_in_floor === 3 || room.room_in_floor === 10) {
                            roomClass += ' room-divider-after';
                        }

                        if (tenantCount === 0) {
                            roomClass += ' vacant';
                        } else if (tenantCount === 1) {
                            roomClass += ' occupied';
                        } else {
                            roomClass += ' multi-tenant';
                        }

                        const roomTitle = `${room.house_name}${room.tenants.length > 0 ? ' - ' + room.tenants.map(t => t.tenant_name).join(', ') : ' - 空闲'}`;

                        roomsHtml.push(`
                            <div class="${roomClass}" onclick="app.showRoomDetail('${room.house_id}')" title="${roomTitle}">
                                ${room.room_number}
                            </div>
                        `);
                    } else {
                        // 空房间占位
                        const roomInFloor = parseInt(item.number);
                        const isLarge = this.isLargeRoom(roomInFloor);
                        let emptyRoomClass = `mini-room vacant${isLarge ? ' large-room' : ''}`;

                        // 添加房间分隔虚线（3号和10号房间后面）
                        if (roomInFloor === 3 || roomInFloor === 10) {
                            emptyRoomClass += ' room-divider-after';
                        }

                        roomsHtml.push(`
                            <div class="${emptyRoomClass}" title="房间${roomNumber} - 空闲">
                                ${roomNumber}
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
                    let roomText = room.room_number; // 显示完整房间号

                    // 检查是否为50平米房间
                    if (this.isLargeRoom(room.room_in_floor)) {
                        roomClass += ' large-room';
                    }

                    // 添加房间分隔虚线（3号和10号房间后面）
                    if (room.room_in_floor === 3 || room.room_in_floor === 10) {
                        roomClass += ' room-divider-after';
                    }

                    if (tenantCount === 0) {
                        roomClass += ' vacant';
                    } else if (tenantCount === 1) {
                        roomClass += ' occupied';
                    } else {
                        roomClass += ' multi-tenant';
                    }

                    const roomTitle = `${room.house_name}${room.tenants.length > 0 ? ' - ' + room.tenants.map(t => t.tenant_name).join(', ') : ' - 空闲'}`;

                    roomsHtml.push(`
                        <div class="${roomClass}" onclick="app.showRoomDetail('${room.house_id}')" title="${roomTitle}">
                            ${roomText}
                        </div>
                    `);
                } else {
                    // 空房间占位
                    const isLarge = this.isLargeRoom(i);
                    let emptyRoomClass = `mini-room vacant${isLarge ? ' large-room' : ''}`;

                    // 添加房间分隔虚线（3号和10号房间后面）
                    if (i === 3 || i === 10) {
                        emptyRoomClass += ' room-divider-after';
                    }

                    roomsHtml.push(`
                        <div class="${emptyRoomClass}" title="房间${floor}${i.toString().padStart(2, '0')} - 空闲">
                            ${floor}${i.toString().padStart(2, '0')}
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

        // 检查是否为50平米房间
        if (this.isLargeRoom(room.room_number)) {
            cardClass += ' large-room';
        }

        if (tenantCount === 0) {
            cardClass += ' vacant-room';
            tenantInfo = '<div class="tenant-info">空闲</div>';
        } else if (tenantCount === 1) {
            cardClass += ' occupied-room';
            const tenant = room.tenants.find(t => t.is_main === 1) || room.tenants[0];

            // 收集标签
            const tags = new Set();
            if (tenant.tag && tenant.tag !== '未分类') {
                tags.add(tenant.tag);
            }

            let tagsHtml = '';
            if (tags.size > 0) {
                tagsHtml = '<div class="room-tags">';
                tags.forEach(tag => {
                    tagsHtml += `<span class="student-tag tag-${tag}">${tag}</span>`;
                });
                tagsHtml += '</div>';
            }

            tenantInfo = `
                <div class="tenant-info">
                    <div class="tenant-name">${tenant.tenant_name}</div>
                    ${tagsHtml}
                </div>
            `;
        } else {
            cardClass += ' multi-tenant';
            const mainTenant = room.tenants.find(t => t.is_main === 1);

            // 收集所有租户的标签
            const tags = new Set();
            room.tenants.forEach(tenant => {
                if (tenant.tag && tenant.tag !== '未分类') {
                    tags.add(tenant.tag);
                }
            });

            let tagsHtml = '';
            if (tags.size > 0) {
                tagsHtml = '<div class="room-tags">';
                tags.forEach(tag => {
                    tagsHtml += `<span class="student-tag tag-${tag}">${tag}</span>`;
                });
                tagsHtml += '</div>';
            }

            tenantInfo = `
                <div class="tenant-info">
                    <div class="tenant-name">${mainTenant ? mainTenant.tenant_name : room.tenants[0].tenant_name}</div>
                    <div class="tenant-count">+${tenantCount - 1}人合租</div>
                    ${tagsHtml}
                </div>
            `;
        }

        const roomTitle = `${room.room_number}${this.isLargeRoom(room.room_number) ? ' (50㎡)' : ''}`;

        return `
            <div class="${cardClass}" onclick="app.showRoomDetail('${room.house_id || room.room_number}')">
                <div class="room-number">${roomTitle}</div>
                ${tenantInfo}
            </div>
        `;
    }

    async showRoomDetail(houseId) {
        try {
            // 确保houseId为字符串类型
            const houseIdStr = String(houseId);
            console.log(`获取房间详情: ${houseIdStr}`);

            // 检查houseId是否有效
            if (!houseIdStr || houseIdStr === 'null' || houseIdStr === 'undefined') {
                throw new Error(`无效的房间ID: ${houseIdStr}`);
            }

            // 直接从API（数据库）获取最新数据
            const basePath = window.location.pathname.includes('/rooms/') ? '/rooms' : '';
            const apiUrl = `${basePath}/api/room/${houseIdStr}`;
            console.log(`API请求地址: ${apiUrl}`);

            const response = await fetch(apiUrl);
            console.log(`API响应状态: ${response.status}`);

            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
            }

            const room = await response.json();
            console.log(`API返回数据:`, room);

            if (room.error) {
                throw new Error(room.error);
            }

            this.displayRoomModal(room);

        } catch (error) {
            console.error('获取房间详情失败详细信息:', error);
            console.error('错误堆栈:', error.stack);
            alert(`获取房间详情失败: ${error.message}\n请检查浏览器控制台查看详细错误信息`);
        }
    }

    async updateRoomInfo(houseId, roomData) {
        try {
            // 自动检测API基础路径
            const basePath = window.location.pathname.includes('/rooms/') ? '/rooms' : '';
            const response = await fetch(`${basePath}/api/room/${houseId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(roomData)
            });

            const result = await response.json();

            if (result.error) {
                throw new Error(result.error);
            }

            return result;

        } catch (error) {
            console.error('更新房间信息失败:', error);
            throw error;
        }
    }

    displayRoomModal(room) {
            const modal = document.getElementById('roomModal');
            const modalBody = modal.querySelector('.modal-body');
            const modalTitle = modal.querySelector('.modal-header h3');

            // 设置标题
            const isLarge = this.isLargeRoom(room.room_number);
            modalTitle.innerHTML = `
            <i class="fas fa-home"></i> 
            ${room.room_number} ${isLarge ? '(50㎡)' : '(35㎡)'}
        `;

            let roomInfo = `
            <div class="room-detail">
                <h4><i class="fas fa-info-circle"></i> 基本信息</h4>
                <div class="detail-grid">
                    <div><strong>房间号:</strong> ${room.room_number}</div>
                    <div><strong>楼层:</strong> ${room.floor}楼</div>
                    <div><strong>房间面积:</strong> ${isLarge ? '50㎡' : '35㎡'}</div>
                    <div><strong>入住状态:</strong> ${room.tenants.length > 0 ? `已入住 (${room.tenants.length}人)` : '空闲'}</div>
                </div>
            </div>
        `;

        if (room.tenants.length > 0) {
            roomInfo += `
                <div class="room-detail">
                    <h4><i class="fas fa-users"></i> 租户信息</h4>
                    <div class="detail-grid">
            `;

            room.tenants.forEach(tenant => {
                const isMainTenant = tenant.is_main === 1;
                const tenantTag = tenant.tag || '未分类';
                roomInfo += `
                    <div class="tenant-card ${isMainTenant ? 'main-tenant' : ''}">
                        <div class="tenant-header">
                            <div class="tenant-name-large">${tenant.tenant_name}</div>
                            ${isMainTenant ? '<span class="tenant-badge main">主租户</span>' : '<span class="tenant-badge">合租户</span>'}
                        </div>
                        <div style="margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <span class="student-tag tag-${tenantTag}">${tenantTag}</span>
                            <button class="edit-tag-btn" onclick="app.openStudentTagEditor({student_id: '${tenant.student_id}', name: '${tenant.tenant_name}', room_number: '${room.room_number}', tag: '${tenantTag}'})" style="padding: 4px 8px; font-size: 0.75rem;">编辑标签</button>
                        </div>
                    </div>
                `;
            });

            roomInfo += `
                    </div>
                </div>
            `;
        } else {
            roomInfo += `
                <div class="room-detail">
                    <h4><i class="fas fa-bed"></i> 房间状态</h4>
                    <div style="text-align: center; padding: 40px 20px; color: #64748b;">
                        <i class="fas fa-home" style="font-size: 3rem; margin-bottom: 16px; display: block; color: #94a3b8;"></i>
                        <p style="font-size: 1.1rem; margin: 0;">该房间目前空闲，暂无租户入住</p>
                    </div>
                </div>
            `;
        }

        modalBody.innerHTML = roomInfo;
        modal.style.display = 'block';
    }

    closeModal() {
        document.getElementById('roomModal').style.display = 'none';
    }

    // 标签相关方法
    populateTagFilter() {
        const tagFilter = document.getElementById('tagFilter');
        tagFilter.innerHTML = '<option value="">所有标签</option>';

        if (this.tagsData) {
            this.tagsData.forEach(tag => {
                const option = document.createElement('option');
                option.value = tag;
                option.textContent = tag;
                tagFilter.appendChild(option);
            });
        }
    }

    updateTagLegend() {
        const tagLegend = document.getElementById('tagLegend');
        if (!tagLegend || !this.tagsData) return;

        const tagColors = {
            '22级硕博士': '#fef2f2',
            '23级硕博士': '#f0fdfa',
            '24级硕博士': '#eff6ff',
            '实习实践': '#f0fdf4',
            '未分类': '#fffbeb'
        };

        tagLegend.innerHTML = '';
        this.tagsData.forEach(tag => {
            const item = document.createElement('div');
            item.className = 'tag-legend-item';
            
            const color = document.createElement('div');
            color.className = 'tag-legend-color';
            color.style.backgroundColor = tagColors[tag] || '#f1f5f9';
            
            const label = document.createElement('span');
            label.className = 'tag-legend-label';
            label.textContent = tag;
            
            item.appendChild(color);
            item.appendChild(label);
            tagLegend.appendChild(item);
        });
    }

    async openTagManager() {
        try {
            // 获取最新的标签统计
            const response = await fetch('/api/tags/statistics');
            const data = await response.json();
            
            if (data.success) {
                this.tagStatistics = data.statistics;
            }

            this.renderTagManager();
            document.getElementById('tagModal').style.display = 'block';
        } catch (error) {
            console.error('打开标签管理器失败:', error);
            this.showNotification('error', '打开标签管理器失败');
        }
    }

    renderTagManager() {
        // 渲染标签统计
        const tagStatsModal = document.getElementById('tagStatsModal');
        tagStatsModal.innerHTML = '';

        if (this.tagStatistics) {
            Object.entries(this.tagStatistics).forEach(([tag, count]) => {
                const item = document.createElement('div');
                item.className = 'tag-stat-item';
                
                const badge = document.createElement('div');
                badge.className = 'tag-stat-badge';
                badge.style.backgroundColor = this.getTagColor(tag);
                
                const label = document.createElement('span');
                label.className = 'tag-stat-label';
                label.textContent = tag;
                
                const countSpan = document.createElement('span');
                countSpan.className = 'tag-stat-count';
                countSpan.textContent = count;
                
                item.appendChild(badge);
                item.appendChild(label);
                item.appendChild(countSpan);
                tagStatsModal.appendChild(item);
            });
        }

        // 填充标签过滤器选择框
        const tagFilterModal = document.getElementById('tagFilterModal');
        tagFilterModal.innerHTML = '<option value="">选择标签</option>';
        
        if (this.tagsData) {
            this.tagsData.forEach(tag => {
                const option = document.createElement('option');
                option.value = tag;
                option.textContent = tag;
                tagFilterModal.appendChild(option);
            });
        }

        // 绑定标签过滤器事件
        tagFilterModal.addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadStudentsByTag(e.target.value);
            } else {
                document.getElementById('studentsByTag').innerHTML = '';
            }
        });
    }

    async loadStudentsByTag(tag) {
        try {
            const response = await fetch(`/api/students/tag/${encodeURIComponent(tag)}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderStudentsByTag(data.students, tag);
            } else {
                console.error('加载学生数据失败:', data.error);
            }
        } catch (error) {
            console.error('加载学生数据失败:', error);
        }
    }

    renderStudentsByTag(students, tag) {
        const container = document.getElementById('studentsByTag');
        container.innerHTML = '';

        if (students.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #64748b;">暂无该标签的学生</p>';
            return;
        }

        students.forEach(student => {
            const item = document.createElement('div');
            item.className = 'student-item';
            
            const info = document.createElement('div');
            info.className = 'student-info-item';
            
            const name = document.createElement('div');
            name.className = 'student-name';
            name.textContent = student.name || '未知姓名';
            
            const room = document.createElement('div');
            room.className = 'student-room';
            room.textContent = `房间: ${student.room_number || '未知'}`;
            
            info.appendChild(name);
            info.appendChild(room);
            
            const editBtn = document.createElement('button');
            editBtn.className = 'edit-tag-btn';
            editBtn.textContent = '编辑标签';
            editBtn.onclick = () => this.openStudentTagEditor(student);
            
            item.appendChild(info);
            item.appendChild(editBtn);
            container.appendChild(item);
        });
    }

    openStudentTagEditor(student) {
        this.currentEditingStudent = student;
        
        // 填充学生信息
        document.getElementById('editStudentName').textContent = student.name || '未知姓名';
        document.getElementById('editStudentRoom').textContent = `房间: ${student.room_number || '未知'}`;
        
        // 创建标签选择器
        const tagRadioGroup = document.getElementById('tagRadioGroup');
        tagRadioGroup.innerHTML = '';
        
        if (this.tagsData) {
            this.tagsData.forEach(tag => {
                const item = document.createElement('div');
                item.className = 'tag-radio-item';
                if (student.tag === tag) {
                    item.classList.add('selected');
                }
                
                const radio = document.createElement('input');
                radio.type = 'radio';
                radio.name = 'studentTag';
                radio.value = tag;
                radio.checked = student.tag === tag;
                
                const label = document.createElement('label');
                label.className = 'tag-radio-label';
                label.textContent = tag;
                label.onclick = () => {
                    // 更新选中状态
                    tagRadioGroup.querySelectorAll('.tag-radio-item').forEach(i => i.classList.remove('selected'));
                    item.classList.add('selected');
                    radio.checked = true;
                };
                
                item.appendChild(radio);
                item.appendChild(label);
                tagRadioGroup.appendChild(item);
            });
        }
        
        // 绑定保存按钮事件
        const saveBtn = document.getElementById('saveStudentTag');
        saveBtn.onclick = () => this.saveStudentTag();
        
        document.getElementById('studentTagModal').style.display = 'block';
    }

    async saveStudentTag() {
        if (!this.currentEditingStudent) return;
        
        const selectedTag = document.querySelector('input[name="studentTag"]:checked');
        if (!selectedTag) {
            this.showNotification('error', '请选择一个标签');
            return;
        }
        
        try {
            const response = await fetch(`/api/students/${this.currentEditingStudent.student_id}/tag`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tag: selectedTag.value
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('success', '标签更新成功');
                
                this.closeStudentTagModal();
                
                // 刷新数据，但跳过API同步，直接从数据库读取
                this.loadRoomsData(true);
                
                // 如果房间详情模态框是打开的，重新获取并显示最新数据
                const roomModal = document.getElementById('roomModal');
                if (roomModal.style.display === 'block' && this.currentEditingStudent) {
                    console.log(`重新加载房间 ${this.currentEditingStudent.room_number} 的详情`);
                    // 延迟一下确保数据已更新
                    setTimeout(() => {
                        this.showRoomDetail(this.currentEditingStudent.room_number);
                    }, 500);
                }
                
                // 如果标签管理器是打开的，刷新它
                if (document.getElementById('tagModal').style.display === 'block') {
                    this.openTagManager();
                }
            } else {
                this.showNotification('error', data.error || '标签更新失败');
            }
        } catch (error) {
            console.error('保存标签失败:', error);
            this.showNotification('error', '保存标签失败');
        }
    }

    getTagColor(tag) {
        const tagColors = {
            '22级硕博士': '#fecaca',
            '23级硕博士': '#a7f3d0',
            '24级硕博士': '#bfdbfe',
            '实习实践': '#bbf7d0',
            '未分类': '#fde68a'
        };
        return tagColors[tag] || '#f1f5f9';
    }

    closeTagModal() {
        document.getElementById('tagModal').style.display = 'none';
    }

    closeStudentTagModal() {
        document.getElementById('studentTagModal').style.display = 'none';
        this.currentEditingStudent = null;
    }

    maskIdCard(idCard) {
        if (!idCard || idCard.length < 8) return idCard;
        return idCard.substring(0, 4) + '****' + idCard.substring(idCard.length - 4);
    }

    async performSearch() {
        try {
            // 自动检测API基础路径
        const basePath = window.location.pathname.includes('/rooms/') ? '/rooms' : '';
        const response = await fetch(`${basePath}/api/search?q=${encodeURIComponent(this.searchTerm)}`);
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

        // 应用状态筛选和标签筛选
        if (this.filterStatus || this.filterTag) {
            this.applyStatusFilter();
        }

        // 更新标签过滤器样式
        const tagFilter = document.getElementById('tagFilter');
        if (this.filterTag) {
            tagFilter.classList.add('tag-filtered');
        } else {
            tagFilter.classList.remove('tag-filtered');
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

                // 状态筛选
                if (this.filterStatus === 'occupied' && !isOccupied) {
                    shouldShow = false;
                } else if (this.filterStatus === 'vacant' && !isVacant) {
                    shouldShow = false;
                }

                // 标签筛选
                if (shouldShow && this.filterTag) {
                    const houseId = card.dataset.houseId;
                    const room = this.findRoomByHouseId(houseId);
                    
                    if (!room || !room.tenants || room.tenants.length === 0) {
                        shouldShow = false;
                    } else {
                        const hasTag = room.tenants.some(tenant => tenant.tag === this.filterTag);
                        if (!hasTag) {
                            shouldShow = false;
                        }
                    }
                }

                card.style.display = shouldShow ? 'block' : 'none';
                if (shouldShow) visibleCount++;
            });

            // 如果该楼层没有符合条件的房间，隐藏整个楼层
            floorView.style.display = visibleCount > 0 ? 'block' : 'none';
        });
    }

    findRoomByHouseId(houseId) {
        if (!this.roomsData || !this.roomsData.floors) return null;
        
        for (const floorRooms of Object.values(this.roomsData.floors)) {
            const room = floorRooms.find(r => String(r.house_id) === String(houseId));
            if (room) return room;
        }
        return null;
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

    async refreshAuth() {
        try {
            // 显示刷新状态
            const refreshBtn = document.getElementById('refreshAuth');
            const originalText = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 更新中...';
            refreshBtn.disabled = true;

            // 自动检测API基础路径
            const basePath = window.location.pathname.includes('/rooms/') ? '/rooms' : '';
            
            // 调用认证刷新API
            const response = await fetch(`${basePath}/api/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                // 显示成功消息
                this.showNotification('success', `${result.message}`, 5000);
                
                // 刷新数据
                setTimeout(() => {
                    this.loadRoomsData();
                }, 1000);
            } else {
                this.showNotification('error', `认证更新失败: ${result.message}`, 8000);
            }

        } catch (error) {
            console.error('刷新认证失败:', error);
            this.showNotification('error', '认证更新失败，请稍后重试', 5000);
        } finally {
            // 恢复按钮状态
            const refreshBtn = document.getElementById('refreshAuth');
            refreshBtn.innerHTML = '<i class="fas fa-key"></i> 更新认证';
            refreshBtn.disabled = false;
        }
    }

    showNotification(type, message, duration = 3000) {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i>
                <span>${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // 添加到页面
        document.body.appendChild(notification);

        // 自动消失
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.opacity = '0';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
    }

    // 防抖函数
    debounce(func, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    clearAllCache() {
        if (confirm('确定要清除所有缓存并重新加载页面吗？这将刷新所有数据。')) {
            // 清除应用状态
            this.cacheLoaded = false;
            
            // 清除浏览器缓存
            if ('caches' in window) {
                caches.keys().then(names => {
                    names.forEach(name => {
                        caches.delete(name);
                    });
                });
            }
            
            // 强制刷新页面（绕过缓存）
            location.reload(true);
        }
    }
}

// 全局函数，供HTML调用
function closeModal() {
    app.closeModal();
}

function closeTagModal() {
    app.closeTagModal();
}

function closeStudentTagModal() {
    app.closeStudentTagModal();
}

// 初始化应用
const app = new RoomVisualization();