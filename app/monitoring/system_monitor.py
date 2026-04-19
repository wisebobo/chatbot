"""
System Resource Monitor
Tracks CPU, memory, and other system metrics for production observability
"""
import logging
import os
import psutil
import threading
import time
from typing import Dict

from app.monitoring.metrics import memory_usage_bytes, cpu_usage_percent

logger = logging.getLogger(__name__)


class SystemResourceMonitor:
    """
    Monitors system resource usage and exports to Prometheus
    
    Usage:
        monitor = SystemResourceMonitor()
        monitor.start(interval=60)  # Update every 60 seconds
    """
    
    def __init__(self, update_interval: int = 60):
        self.update_interval = update_interval
        self._running = False
        self._thread = None
        self._process = psutil.Process(os.getpid())
        
    def start(self):
        """Start the monitoring thread"""
        if self._running:
            logger.warning("System resource monitor already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"System resource monitor started (interval: {self.update_interval}s)")
    
    def stop(self):
        """Stop the monitoring thread"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("System resource monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                self._update_metrics()
            except Exception as e:
                logger.error(f"Error updating system metrics: {e}", exc_info=True)
            
            time.sleep(self.update_interval)
    
    def _update_metrics(self):
        """Update Prometheus metrics with current system stats"""
        try:
            # Memory usage
            memory_info = self._process.memory_info()
            memory_usage_bytes.set(memory_info.rss)  # Resident Set Size
            
            # CPU usage
            cpu_percent = self._process.cpu_percent(interval=0.1)
            cpu_usage_percent.set(cpu_percent)
            
            logger.debug(
                f"System metrics - Memory: {memory_info.rss / 1024 / 1024:.2f} MB, "
                f"CPU: {cpu_percent:.1f}%"
            )
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def get_system_stats(self) -> Dict:
        """Get current system statistics (for health endpoint)"""
        try:
            memory_info = self._process.memory_info()
            cpu_percent = self._process.cpu_percent(interval=0.1)
            
            return {
                "memory_rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "memory_vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "cpu_percent": cpu_percent,
                "threads": self._process.num_threads(),
                "open_files": len(self._process.open_files()),
                "connections": len(self._process.connections()),
            }
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {"error": str(e)}


# Global monitor instance
system_monitor = SystemResourceMonitor(update_interval=60)
