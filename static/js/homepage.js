const graphContainer = document.querySelector('.graph-container'); // Select the container
const canvas = document.getElementById('graphCanvas');
const ctx = canvas.getContext('2d');

// Resize canvas to fit the container
canvas.width = canvas.offsetWidth;
canvas.height = canvas.offsetHeight;

// Graph settings
const lines = [
  { color: 'rgba(76, 175, 80, 0.4)', dataPoints: [], lastY: window.innerHeight / 3 }, // Very transparent Green
  { color: 'rgba(117, 245, 30, 0.4)', dataPoints: [], lastY: window.innerHeight * 2 / 3 }, // Very transparent Light Green
];

const maxPoints = 1000; // Maximum points visible
const speed = 3; // Speed of animation

let scrollProgress = 0; // Store scroll progress
let offsetY = 0;

// Draw the grid and labels
function drawGrid() {
  const stepX = 50; // Spacing between vertical grid lines
  const stepY = 50; // Spacing between horizontal grid lines
  
  ctx.beginPath();
  ctx.lineWidth = 1;
  ctx.strokeStyle = '#e0e0e0'; // Subtle grid color
  
  // Draw vertical lines
  for (let x = 0; x <= canvas.width; x += stepX) {
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
  }
  
  // Draw horizontal lines
  for (let y = 0; y <= canvas.height; y += stepY) {
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
  }
  ctx.stroke();
  
  // Draw labels
  ctx.font = '12px Arial';
  ctx.fillStyle = '#888'; // Label color
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  
  // Horizontal labels
  for (let x = 50; x <= canvas.width; x += stepX) {
    ctx.fillText(x, x + 15, canvas.height - 15);
  }
  
  // Vertical labels
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  for (let y = canvas.height; y >= 0; y -= stepY) {
    ctx.fillText(canvas.height - y, 30, y - 15); // Reverse Y-axis values
  }
}

// Generate upward trending data
function generateNextPoint(lastY) {
  const upwardBias = 19.5; // Scaled upward bias
  let nextX = 0;
  let nextY = window.innerHeight; // Use window height instead of canvas height
  
  if (lastY !== undefined) {
    nextY = Math.max(
      0,
      Math.min(
        window.innerHeight, // Use window height here for Y-range
        lastY - (Math.random() * 40 - upwardBias) // Upward bias
      )
    );
  }

  return { y: nextY };
}

// Update scroll progress based on container scroll position
function updateScrollProgress() {
  const container = document.querySelector('.graph-container'); // Get the container
  const maxScroll = container.scrollHeight - container.clientHeight; // Total scrollable area
  if (maxScroll > 0) {
    scrollProgress = container.scrollTop / maxScroll; // Scroll position relative to total scrollable area
    if (scrollProgress > 1) scrollProgress = 1; // Clamp between 0 and 1
    if (scrollProgress < 0) scrollProgress = 0; // Clamp between 0 and 1
  } else {
    scrollProgress = 0; // Reset to 0 if there's no scroll
  }
}

// Render graph based on scroll position
function renderGraph() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawGrid();

  lines.forEach((line) => {
    const dataPoints = line.dataPoints;

    // Add new points based on scroll progress
    if (scrollProgress > 0) {
      const numNewPoints = Math.floor(scrollProgress * maxPoints);
      while (dataPoints.length < numNewPoints) {
        const nextX = dataPoints.length > 0 ? dataPoints[dataPoints.length - 1].x + speed : 0;
        const nextPoint = generateNextPoint(line.lastY);
        nextPoint.x = nextX;
        line.lastY = nextPoint.y;
        dataPoints.push(nextPoint);
      }
    }

    // Shrink the line when scrolling up
    const numVisiblePoints = Math.floor(scrollProgress * dataPoints.length);

    // Calculate vertical offset based on scroll progress
    offsetY = scrollProgress * 0.695 * canvas.height; // Vertical shift based on scroll progress

    // Draw the line
    ctx.beginPath();
    ctx.lineWidth = 3;
    ctx.strokeStyle = line.color;

    // Draw only the visible portion based on scroll progress
    for (let i = 0; i < numVisiblePoints; i++) {
      const point = dataPoints[i];
      if (i === 0) {
        ctx.moveTo(point.x, point.y + offsetY); // Offset each point based on scroll
      } else {
        ctx.lineTo(point.x, point.y + offsetY); // Offset each point based on scroll
      }
    }

    ctx.stroke();
  });
}

// Attach scroll event listener to the container
graphContainer.addEventListener('scroll', () => {
  updateScrollProgress();
  renderGraph();
});

renderGraph();