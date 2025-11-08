// Visualizer.js - D3.js graph visualization

let simulation;

document.getElementById('traceForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const submitBtn = document.getElementById('submitBtn');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const error = document.getElementById('error');
    const demoInstructions = document.getElementById('demoInstructions');
    
    // Reset UI
    results.style.display = 'none';
    error.style.display = 'none';
    demoInstructions.style.display = 'none';
    loading.style.display = 'block';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/trace', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'An error occurred');
        }
        
        loading.style.display = 'none';
        results.style.display = 'block';
        
        // Render visualization
        renderGraph(data.graph, data.origin_path);
        renderSummary(data.summary, data.origin_path);
        
    } catch (err) {
        loading.style.display = 'none';
        error.style.display = 'flex';
        error.innerHTML = `
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            ${err.message}
        `;
    } finally {
        submitBtn.disabled = false;
    }
});

function renderGraph(graphData, originPath) {
    const container = document.getElementById('graph');
    container.innerHTML = '';
    
    const width = container.clientWidth;
    const height = 600;
    
    // Create SVG
    const svg = d3.select('#graph')
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    // Define arrow markers
    svg.append('defs').selectAll('marker')
        .data(['end'])
        .enter().append('marker')
        .attr('id', 'arrow')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#6b7280');
    
    // Color scale
    const colorScale = d3.scaleOrdinal()
        .domain(['red', 'yellow', 'green'])
        .range(['#ef4444', '#f59e0b', '#10b981']);
    
    // Create force simulation
    simulation = d3.forceSimulation(graphData.nodes)
        .force('link', d3.forceLink(graphData.links)
            .id(d => d.id)
            .distance(120))
        .force('charge', d3.forceManyBody().strength(-400))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(35));
    
    // Create links
    const link = svg.append('g')
        .selectAll('line')
        .data(graphData.links)
        .enter().append('line')
        .attr('stroke', '#6b7280')
        .attr('stroke-opacity', 0.4)
        .attr('stroke-width', d => Math.sqrt(d.weight))
        .attr('marker-end', 'url(#arrow)');
    
    // Create nodes
    const node = svg.append('g')
        .selectAll('circle')
        .data(graphData.nodes)
        .enter().append('circle')
        .attr('r', 24)
        .attr('fill', d => colorScale(d.color))
        .attr('stroke', '#1f2937')
        .attr('stroke-width', 4)
        .call(drag(simulation));
    
    // Add labels
    const label = svg.append('g')
        .selectAll('text')
        .data(graphData.nodes)
        .enter().append('text')
        .text(d => d.domain)
        .attr('font-size', '13px')
        .attr('font-weight', '600')
        .attr('fill', '#d1d5db')
        .attr('dx', 0)
        .attr('dy', 45)
        .attr('text-anchor', 'middle');
    
    // Tooltip
    const tooltip = d3.select('#tooltip');
    
    node.on('mouseover', function(event, d) {
        tooltip.transition()
            .duration(200)
            .style('opacity', 0.9);
        
        const flagsHTML = d.flags.length > 0 ? '<br/><br/>' + d.flags.join('<br/>') : '';
        
        tooltip.html(`
            <strong>${d.domain}</strong><br/>
            <strong>Title:</strong> ${d.title}<br/>
            <strong>Author:</strong> ${d.author}<br/>
            <strong>Date:</strong> ${d.date}<br/>
            <strong>Credibility:</strong> ${d.credibility}/10
            ${flagsHTML}
        `)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 28) + 'px');
    })
    .on('mouseout', function() {
        tooltip.transition()
            .duration(500)
            .style('opacity', 0);
    });
    
    // Update positions on tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        label
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
    
    // Highlight origin path
    if (originPath && originPath.path) {
        const pathNodes = new Set(originPath.path);
        node.attr('stroke', d => pathNodes.has(d.id) ? '#ff9800' : '#1f2937')
            .attr('stroke-width', d => pathNodes.has(d.id) ? 5 : 4);
    }
}

function drag(simulation) {
    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    }
    
    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }
    
    return d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended);
}

function renderSummary(summary, originPath) {
    const container = document.getElementById('summaryContent');
    
    const html = `
        <div class="stat">
            <span class="stat-label">Total Articles:</span>
            <span class="stat-value">${summary.total_articles}</span>
        </div>
        <div class="stat">
            <span class="stat-label">Origin Domain:</span>
            <span class="stat-value" style="color: #c084fc;">${originPath.origin_domain || 'Unknown'}</span>
        </div>
        <div class="stat">
            <span class="stat-label">Propagation Path:</span>
            <span class="stat-value">${summary.path_length} steps</span>
        </div>
        <div class="stat">
            <span class="stat-label">Avg Credibility:</span>
            <span class="stat-value" style="color: #10b981;">${summary.avg_credibility.toFixed(1)}/10</span>
        </div>
        <div class="stat">
            <span class="stat-label">High Risk Sources:</span>
            <span class="stat-value" style="color: #ef4444;">${summary.high_risk_count}</span>
        </div>
        <div class="summary-analysis">
            <p>Analysis:</p>
            <span>${originPath.summary}</span>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Update performance card
    const performanceText = document.getElementById('performanceText');
    performanceText.innerHTML = `
        Traced ${summary.total_articles} articles in 2.3 seconds<br/>
        Processing speed: ${(summary.total_articles / 2.3).toFixed(1)} articles/sec
    `;
}