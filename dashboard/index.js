const express = require("express");
const { exec } = require("child_process");
const cors = require("cors");
const path = require("path");

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.static(path.join(__dirname, "public"))); // Serve frontend

// Fetch running Docker containers
app.get("/api/services", (req, res) => {
  exec("docker ps --format '{{json .}}'", (err, stdout) => {
    if (err) return res.status(500).json({ error: "Error fetching services" });
    const services = stdout.trim().split("\n").map(JSON.parse);
    res.json(services.map(s => ({ Name: s.Names, Status: s.State, Port: s.Ports })));
  });
});

// Fetch logs for a container
app.get("/api/logs/:container", (req, res) => {
  const { container } = req.params;
  exec(`docker logs --tail 10 ${container}`, (err, stdout) => {
    if (err) return res.status(500).json({ error: "Error fetching logs" });
    res.json({ logs: stdout.split("\n") });
  });
});

// Fetch system resource usage
app.get("/api/stats", (req, res) => {
  exec("docker stats --no-stream --format '{{json .}}'", (err, stdout) => {
    if (err) return res.status(500).json({ error: "Error fetching stats" });
    const stats = stdout.trim().split("\n").map(JSON.parse);
    res.json(stats.map(s => ({ Name: s.Name, CPU: s.CPUPerc, Memory: s.MemUsage })));
  });
});

// Serve the index.html file for the root route "/"
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

app.listen(PORT, () => console.log(`🚀 Backend running on http://localhost:${PORT}`));
